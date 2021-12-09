import yaml
import os
import pyaudio
import time
import logging

import numpy as np
import samplerate
import scipy.io.wavfile as wavefile

from concurrent.futures import ThreadPoolExecutor
from rich import print

from kaldi.asr import NnetLatticeFasterOnlineRecognizer
from kaldi.decoder import LatticeFasterDecoderOptions
from kaldi.nnet3 import NnetSimpleLoopedComputationOptions
from kaldi.online2 import (
    OnlineEndpointConfig,
    OnlineIvectorExtractorAdaptationState,
    OnlineNnetFeaturePipelineConfig,
    OnlineNnetFeaturePipelineInfo,
    OnlineNnetFeaturePipeline,
    OnlineSilenceWeighting,
)
from kaldi.util.options import ParseOptions
from kaldi.util.table import SequentialWaveReader
from kaldi.lat.sausages import MinimumBayesRisk
from kaldi.matrix import Vector


logger = logging.getLogger(__name__)


def load_model(
    config_file, online_config, models_path="models/", beam_size=10, frames_per_chunk=50
):
    # Read YAML file
    with open(config_file, "r") as stream:
        model_yaml = yaml.safe_load(stream)

    decoder_yaml_opts = model_yaml["decoder"]

    print(f"Decoder yml options:\n{decoder_yaml_opts}")

    feat_opts = OnlineNnetFeaturePipelineConfig()
    endpoint_opts = OnlineEndpointConfig()

    if not os.path.isfile(online_config):
        print(
            online_config
            + " does not exists. Trying to create it from yaml file settings."
        )
        print("See also online_config_options.info.txt for what possible settings are.")
        with open(online_config, "w") as online_config_file:
            online_config_file.write("--add_pitch=False\n")
            online_config_file.write(
                "--mfcc_config=" + models_path + decoder_yaml_opts["mfcc-config"] + "\n"
            )
            online_config_file.write("--feature_type=mfcc\n")
            online_config_file.write(
                "--ivector_extraction_config="
                + models_path
                + decoder_yaml_opts["ivector-extraction-config"]
                + "\n"
            )
            online_config_file.write(
                "--endpoint.silence-phones="
                + decoder_yaml_opts["endpoint-silence-phones"]
                + "\n"
            )
    else:
        print("Loading online conf from:", online_config)

    po = ParseOptions("")
    feat_opts.register(po)
    endpoint_opts.register(po)
    po.read_config_file(online_config)
    feat_info = OnlineNnetFeaturePipelineInfo.from_config(feat_opts)

    # Construct recognizer
    decoder_opts = LatticeFasterDecoderOptions()
    decoder_opts.beam = beam_size
    decoder_opts.max_active = 7000
    decodable_opts = NnetSimpleLoopedComputationOptions()
    decodable_opts.acoustic_scale = 1.0
    decodable_opts.frame_subsampling_factor = 3
    decodable_opts.frames_per_chunk = frames_per_chunk
    asr = NnetLatticeFasterOnlineRecognizer.from_files(
        models_path + decoder_yaml_opts["model"],
        models_path + decoder_yaml_opts["fst"],
        models_path + decoder_yaml_opts["word-syms"],
        decoder_opts=decoder_opts,
        decodable_opts=decodable_opts,
        endpoint_opts=endpoint_opts,
    )

    return asr, feat_info, decodable_opts


def decode_chunked_partial(scp:str = "scp:wav.scp"):
    """ Decode whole utterance """
    for key, wav in SequentialWaveReader(scp):
        feat_pipeline = OnlineNnetFeaturePipeline(feat_info)
        asr.set_input_pipeline(feat_pipeline)
        asr.init_decoding()
        data = wav.data()[0]
        last_chunk = False
        part = 1
        prev_num_frames_decoded = 0
        for i in range(0, len(data), chunk_size):
            if i + chunk_size >= len(data):
                last_chunk = True
            feat_pipeline.accept_waveform(wav.samp_freq, data[i : i + chunk_size])
            if last_chunk:
                feat_pipeline.input_finished()
            asr.advance_decoding()
            num_frames_decoded = asr.decoder.num_frames_decoded()
            if not last_chunk:
                if num_frames_decoded > prev_num_frames_decoded:
                    prev_num_frames_decoded = num_frames_decoded
                    out = asr.get_partial_output()
                    print(key + "-part%d" % part, out["text"], flush=True)
                    part += 1
        asr.finalize_decoding()
        out = asr.get_output()
        print(key + "-final", out["text"], flush=True)


def decode_chunked_partial_endpointing(
    asr,
    feat_info,
    decodable_opts,
    scp,
    chunk_size=1024,
    asr_client=None,
    pad_confidences=True,
):
    # Decode (chunked + partial output + endpointing
    #         + ivector adaptation + silence weighting)
    adaptation_state = OnlineIvectorExtractorAdaptationState.from_info(
        feat_info.ivector_extractor_info
    )
    for key, wav in SequentialWaveReader(scp):
        feat_pipeline = OnlineNnetFeaturePipeline(feat_info)
        feat_pipeline.set_adaptation_state(adaptation_state)
        asr.set_input_pipeline(feat_pipeline)
        asr.init_decoding()
        sil_weighting = OnlineSilenceWeighting(
            asr.transition_model,
            feat_info.silence_weighting_config,
            decodable_opts.frame_subsampling_factor,
        )
        data = wav.data()[0]
        print("type(data):", type(data))
        last_chunk = False
        utt, part = 1, 1
        prev_num_frames_decoded, offset = 0, 0
        for i in range(0, len(data), chunk_size):
            if i + chunk_size >= len(data):
                last_chunk = True
            feat_pipeline.accept_waveform(wav.samp_freq, data[i : i + chunk_size])
            if last_chunk:
                feat_pipeline.input_finished()
            if sil_weighting.active():
                sil_weighting.compute_current_traceback(asr.decoder)
                feat_pipeline.ivector_feature().update_frame_weights(
                    sil_weighting.get_delta_weights(feat_pipeline.num_frames_ready())
                )
            asr.advance_decoding()
            num_frames_decoded = asr.decoder.num_frames_decoded()
            if not last_chunk:
                if asr.endpoint_detected():
                    asr.finalize_decoding()
                    out = asr.get_output()
                    mbr = MinimumBayesRisk(out["lattice"])
                    confd = mbr.get_one_best_confidences()
                    if pad_confidences:
                        token_length = len(out["text"].split())

                        # computed confidences array is smaller than the
                        # actual token length,
                        if len(confd) < token_length:
                            print(
                                "WARNING: less computed confidences than token length! "
                                "Fixing this with padding!"
                            )
                            confd = np.pad(
                                confd,
                                [0, token_length - len(confd)],
                                mode="constant",
                                constant_values=1.0,
                            )
                        elif len(confd) > token_length:
                            print(
                                "WARNING: more computed confidences than token length! "
                                "Fixing this with slicing!"
                            )
                            confd = confd[:token_length]

                    print(confd)
                    print(key + "-utt%d-final" % utt, out["text"], flush=True)
                    if asr_client is not None:
                        asr_client.completeUtterance(
                            utterance=out["text"],
                            key=key + "-utt%d-part%d" % (utt, part),
                            confidences=confd,
                        )
                    offset += int(
                        num_frames_decoded
                        * decodable_opts.frame_subsampling_factor
                        * feat_pipeline.frame_shift_in_seconds()
                        * wav.samp_freq
                    )
                    feat_pipeline.get_adaptation_state(adaptation_state)
                    feat_pipeline = OnlineNnetFeaturePipeline(feat_info)
                    feat_pipeline.set_adaptation_state(adaptation_state)
                    asr.set_input_pipeline(feat_pipeline)
                    asr.init_decoding()
                    sil_weighting = OnlineSilenceWeighting(
                        asr.transition_model,
                        feat_info.silence_weighting_config,
                        decodable_opts.frame_subsampling_factor,
                    )
                    remainder = data[offset : i + chunk_size]
                    feat_pipeline.accept_waveform(wav.samp_freq, remainder)
                    utt += 1
                    part = 1
                    prev_num_frames_decoded = 0
                elif num_frames_decoded > prev_num_frames_decoded:
                    prev_num_frames_decoded = num_frames_decoded
                    out = asr.get_partial_output()
                    print(key + "-utt%d-part%d" % (utt, part), out["text"], flush=True)
                    if asr_client is not None:
                        asr_client.partialUtterance(
                            utterance=out["text"],
                            key=key + "-utt%d-part%d" % (utt, part),
                        )
                    part += 1
        asr.finalize_decoding()
        out = asr.get_output()
        mbr = MinimumBayesRisk(out["lattice"])
        confd = mbr.get_one_best_confidences()
        print(out)
        print(key + "-utt%d-final" % utt, out["text"], flush=True)
        if asr_client is not None:
            asr_client.completeUtterance(
                utterance=out["text"],
                key=key + "-utt%d-part%d" % (utt, part),
                confidences=confd,
            )

        feat_pipeline.get_adaptation_state(adaptation_state)


def decode_chunked_partial_endpointing_mic(
    asr,
    feat_info,
    decodable_opts,
    paudio,
    input_microphone_id,
    channels=1,
    samp_freq=16000,
    record_samplerate=16000,
    chunk_size=1024,
    wait_for_start_command=False,
    record_message_history=False,
    asr_client=None,
    speaker_str="Speaker",
    resample_algorithm="sinc_best",
    save_debug_wav=False,
    use_threads=False,
    minimum_num_frames_decoded_per_speaker=5,
    mic_vol_cutoff=0.5,
    use_local_mic=True,
    decode_control_channel="asr_control",
    audio_data_channel="asr_audio",
):
    """Realtime decoding loop, uses blocking calls and interfaces a microphone
    directly (with pyaudio)
    """
    # Subscribe to command and control redis channel
    import redis
    red = redis.StrictRedis(host="localhost")
    p = red.pubsub()
    p.subscribe(decode_control_channel)

    if not use_local_mic:
        pa = red.pubsub()
        pa.subscribe(audio_data_channel)

    # Figure out if we need to resample (Todo: channles does not seem to work)
    need_resample = False
    if record_samplerate != samp_freq:
        logger.warning(
            "Activating resampler since record and decode samplerate are different: "
            f"{record_samplerate} -> {samp_freq}",
        )
        resampler = samplerate.Resampler(resample_algorithm, channels=channels)
        need_resample = True
        ratio = samp_freq / record_samplerate
        logger.debug("Resample ratio:", ratio)

    # Initialize Python/Kaldi bridge
    logger.info("Constructing decoding pipeline")
    adaptation_state = OnlineIvectorExtractorAdaptationState.from_info(
        feat_info.ivector_extractor_info
    )
    key = "mic" + str(input_microphone_id)
    feat_pipeline, sil_weighting = initNnetFeatPipeline(
        adaptation_state, asr, decodable_opts, feat_info
    )
    logger.info("Done")

    speaker = speaker_str.replace("#c#", "0")
    last_chunk = False
    utt, part = 1, 1
    prev_num_frames_decoded, offset_complete = 0, 0
    chunks_decoded = 0
    num_chunks = 0
    blocks = []
    rawblocks = []

    if use_local_mic:
        # Open microphone channel
        logger.info(f"Open microphone stream with id: {input_microphone_id}...")
        stream = paudio.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=record_samplerate,
            input=True,
            frames_per_buffer=chunk_size,
            input_device_index=input_microphone_id,
        )
        logger.info("Done!")

    do_decode = not wait_for_start_command
    need_finalize = False
    block, previous_block = None, None
    decode_future = None

    # Send event (with redis) to the front that ASR session is ready
    asr_client.asr_ready(speaker=speaker)

    # Initialize a ThreadPoolExecutor.
    # Note that we initialize the thread executer independently of whether we
    # actually use it later (the -t option).
    # At the end of this loop we have two code paths, one that uses a computation
    # future (with -t) and one without it.
    with ThreadPoolExecutor(max_workers=1) as executor:
        while not last_chunk:
            # Check if there is a message from the redis server first (non-blocking!),
            # if there is no new message msh is simply None.
            msg = p.get_message()

            # We check if there are externally send control commands
            if msg is not None:
                print("msg:", msg)
                if msg["data"] == b"start":
                    print("Start command received!")
                    do_decode = True
                    asr_client.sendstatus(isDecoding=do_decode)

                elif msg["data"] == b"stop":
                    print("Stop command received!")
                    if do_decode and prev_num_frames_decoded > 0:
                        need_finalize = True
                    do_decode = False
                    asr_client.sendstatus(isDecoding=do_decode)

                elif msg["data"] == b"shutdown":
                    print("Shutdown command received!")
                    last_chunk = True

                elif msg["data"] == b"status":
                    print("Status command received!")
                    asr_client.sendstatus(isDecoding=do_decode)

                elif msg["data"] == b"reset_timer":
                    print("Reset time command received!")
                    asr_client.resetTimer()

            if use_local_mic:
                # We always consume from the microphone stream, even if we do not decode
                block_raw = stream.read(chunk_size, exception_on_overflow=False)
                npblock = np.frombuffer(block_raw, dtype=np.int16)
            else:
                block_audio_redis_msg = next(pa.listen())
                if (
                    block_audio_redis_msg["type"] == "subscribe"
                    and block_audio_redis_msg["data"] == 1
                ):
                    print("audio msg:", block_audio_redis_msg)
                    print("Successfully connected to redis audio stream!")
                    continue
                else:
                    npblock = np.frombuffer(
                        block_audio_redis_msg["data"], dtype=np.int16
                    )
                    print("audio data: ", npblock)

            # Resample the block if necessary, e.g. 48kHz -> 16kHz
            if need_resample:
                block = resampler.process(np.array(npblock, copy=True), ratio)
                block = np.array(block, dtype=np.int16)
            else:
                block = npblock

            # Only save the wav, if the save_debug flag is enabled
            # (TODO: investigate: does not seem to work with multiple channels)
            if save_debug_wav:
                blocks.append(block)
                rawblocks.append(npblock)

            # Block on the result of the decode if one is pending
            if (
                use_threads
                and do_decode
                and block is not None
                and decode_future is not None
            ):
                # This call blocks until the result is ready
                (
                    need_endpoint_finalize,
                    prev_num_frames_decoded,
                    part,
                    utt,
                ) = decode_future.result()

                # Check if we need to finalize, disallow endpoint without a single decoded frame
                if need_endpoint_finalize and prev_num_frames_decoded > 0:
                    need_finalize = True
                    resend_previous_waveform = True
                    print("prev_num_frames_decoded:", prev_num_frames_decoded)

                if need_endpoint_finalize and prev_num_frames_decoded == 0:
                    print(
                        "WARN need_endpoint_finalize and prev_num_frames_decoded == 0"
                    )

            # Finalize the decoding here, if endpointing signalized that we should
            # start a new utterance.
            # We might also need to finalize if we switch from do_decode=True to
            # do_decode=False (user starts/stops decoding from frontend).
            if need_finalize and block is not None and prev_num_frames_decoded > 0:
                print("prev_num_frames_decoded:", prev_num_frames_decoded)
                out, confd = finalize_decode(asr, asr_client, key, part, speaker, utt)
                feat_pipeline, sil_weighting = reinitialize_asr(
                    adaptation_state, asr, decodable_opts, feat_info, feat_pipeline
                )
                utt += 1
                part = 1

                if resend_previous_waveform and previous_block is not None:
                    # We always resend the last block for the new utterance
                    # (we only know that the endpoint is inside of a chunk, but not where exactly)
                    feat_pipeline.accept_waveform(samp_freq, Vector(previous_block))
                    resend_previous_waveform = False

                need_finalize = False

                prev_num_frames_decoded = 0

            # If we operate on multichannel data, select the channel here that has the
            # highest volume.
            # (with some added heuristic, only change the speaker if the previous
            # speaker was active for minimum_num_frames_decoded_per_speaker many frames)
            if channels > 1:
                block = np.reshape(block, (-1, channels))

                # Select loudest channel
                volume_norms = []
                for i in range(channels):
                    # We have a simplyfied concept of loudness, it is simply the L2
                    # of the chunk interpreted as a vector (sqrt of the sum of squares):
                    # This has nothing to do with the physical loudness.
                    volume_norms.append(np.linalg.norm(block[:, i] / 65536.0) * 10.0)

                volume_norms = [
                    0.0 if elem < mic_vol_cutoff else elem for elem in volume_norms
                ]

                volume_norm = max(volume_norms)
                max_channel = volume_norms.index(volume_norm)
                block = block[:, max_channel]

                new_speaker = speaker_str.replace("#c#", str(max_channel))

                # print('vols:',volume_norms, 'max:',max_channel, 'value:',volume_norm)

                if (
                    sum(volume_norms) > 1e-10
                    and new_speaker != speaker
                    and prev_num_frames_decoded
                    >= minimum_num_frames_decoded_per_speaker
                ):
                    print(
                        "Speaker change! Number of frames decoded "
                        f"for previous speaker: {str(prev_num_frames_decoded)}",
                    )

                    speaker = new_speaker

                    need_finalize = True
                    resend_previous_waveform = True
            else:
                volume_norm = np.linalg.norm(block / 65536.0) * 10.0

            num_chunks += 1

            # Send status beacon periodically (to frontend, so its knows we are alive)
            if num_chunks % 50 == 0:
                asr_client.sendstatus(isDecoding=do_decode)

            if do_decode:
                # If we use the unthreaded mode, we block until the computation here in this loop
                if not use_threads:
                    (
                        need_endpoint_finalize,
                        prev_num_frames_decoded,
                        part,
                        utt,
                    ) = advance_mic_decoding(
                        adaptation_state,
                        asr,
                        asr_client,
                        block,
                        chunks_decoded,
                        feat_info,
                        feat_pipeline,
                        key,
                        last_chunk,
                        part,
                        prev_num_frames_decoded,
                        samp_freq,
                        sil_weighting,
                        speaker,
                        utt,
                    )
                    # Check if we need to finalize, disallow endpoint without a single
                    # decoded frame
                    if need_endpoint_finalize and prev_num_frames_decoded > 0:
                        need_finalize = True
                        resend_previous_waveform = True
                        print("prev_num_frames_decoded:", prev_num_frames_decoded)

                else:
                    # In threaded mode, we submit a non blocking computation request
                    # to the thread executor
                    decode_future = executor.submit(
                        advance_mic_decoding,
                        adaptation_state,
                        asr,
                        asr_client,
                        block,
                        chunks_decoded,
                        feat_info,
                        feat_pipeline,
                        key,
                        last_chunk,
                        part,
                        prev_num_frames_decoded,
                        samp_freq,
                        sil_weighting,
                        speaker,
                        utt,
                    )
            else:
                time.sleep(0.001)

            previous_block = block

    # Record message history as an integrated Python file, that can be used as a
    # standalone replay
    if record_message_history:
        with open("message_history_replay.py", "w") as message_history_out:
            message_history_out.write(asr_client.message_trace)
    else:
        print(
            "Not writing record message history since "
            "--record_message_history is not set."
        )

    # Write debug wav as output file (will only be executed after shutdown)
    if save_debug_wav:
        print("Saving debug output...")
        wavefile.write("debug.wav", samp_freq, np.concatenate(blocks, axis=None))
        wavefile.write(
            "debugraw.wav", record_samplerate, np.concatenate(rawblocks, axis=None)
        )
    else:
        print("Not writing debug wav output since --save_debug_wav is not set.")

    # Now shuting down pipeline, compute MBR for the final utterance and complete it.
    print("Shutdown: finalizing ASR output...")
    asr.finalize_decoding()
    out = asr.get_output()
    mbr = MinimumBayesRisk(out["lattice"])
    confd = mbr.get_one_best_confidences()
    print(out)
    print(key + "-utt%d-final" % utt, out["text"], flush=True)
    if asr_client is not None:
        asr_client.completeUtterance(
            utterance=out["text"],
            key=key + "-utt%d-part%d" % (utt, part),
            confidences=confd,
            speaker=speaker,
        )
        asr_client.sendstatus(isDecoding=False, shutdown=True)
    print("Done, will exit now.")


# Advance decoding with one chunk of data
def advance_mic_decoding(
    adaptation_state,
    asr,
    asr_client,
    block,
    chunks_decoded,
    feat_info,
    feat_pipeline,
    key,
    last_chunk,
    part,
    prev_num_frames_decoded,
    samp_freq,
    sil_weighting,
    speaker,
    utt,
):
    need_endpoint_finalize = False
    chunks_decoded += 1

    # Let the feature pipeline accept the wavform, take block (numpy array) and convert
    # into Kaldi Vector.
    # This is blocking and Kaldi computes all features updates necessary
    # for the input chunk.
    feat_pipeline.accept_waveform(samp_freq, Vector(block))

    # If this is the last chunk of an utterance, inform feature the pipeline to flush
    # all buffers and finialize all features
    if last_chunk:
        feat_pipeline.input_finished()
    if sil_weighting.active():
        sil_weighting.compute_current_traceback(asr.decoder)

        # inform ivector feature computation about current silence weighting
        feat_pipeline.ivector_feature().update_frame_weights(
            sil_weighting.get_delta_weights(feat_pipeline.num_frames_ready())
        )

    # This is where we inform Kaldi to advance the decoding pipeline by one step until
    # the input chunk is completely processed.
    asr.advance_decoding()
    num_frames_decoded = asr.decoder.num_frames_decoded()

    # If the endpointing did not indicate that we are in the last chunk:
    if not last_chunk:
        # Check if we should set an endpoint for the next chunk
        if asr.endpoint_detected():
            if num_frames_decoded > 0:
                need_endpoint_finalize = True
            #    prev_num_frames_decoded = 0
        # If we do not have decteted an endpoint, check if a new full frame
        # (actually a block of frames) has been decoded and something changed:
        elif num_frames_decoded > prev_num_frames_decoded:
            # Get the partial output from the decoder (best path)
            out = asr.get_partial_output()

            # Debug output (partial utterance)
            print(key + "-utt%d-part%d" % (utt, part), out["text"], flush=True)
            # Now send the partial Utterance to the frontend (that then displays it to the user)
            if asr_client is not None:
                asr_client.partialUtterance(
                    utterance=out["text"],
                    key=key + "-utt%d-part%d" % (utt, part),
                    speaker=speaker,
                )
            part += 1

    return need_endpoint_finalize, num_frames_decoded, part, utt


def initNnetFeatPipeline(adaptation_state, asr, decodable_opts, feat_info):
    """Initialize all needed Kaldi object for online feature computation (feat_pipeline)
    and online decoding (asr object)
    """
    feat_pipeline = OnlineNnetFeaturePipeline(feat_info)
    feat_pipeline.set_adaptation_state(adaptation_state)
    asr.set_input_pipeline(feat_pipeline)
    asr.init_decoding()
    sil_weighting = OnlineSilenceWeighting(
        asr.transition_model,
        feat_info.silence_weighting_config,
        decodable_opts.frame_subsampling_factor,
    )
    return feat_pipeline, sil_weighting


def finalize_decode(asr, asr_client, key, part, speaker, utt):
    """This finalizes an utterance and computes confidences.
    We only compute the confidences (with MBR) on the finalized utterance,
    not on the partial ones.
    """
    # Tell Kaldi to finalize decoding
    asr.finalize_decoding()
    # Get final best path and lattice (out is a dict object with
    # out["text"] = best path and out["lattice"] = Kaldi lattice object)
    out = asr.get_output()
    # Use the lattice to compute MBR confidences
    mbr = MinimumBayesRisk(out["lattice"])
    # confd is a vector with a confidence for each word of the best path
    confd = mbr.get_one_best_confidences()
    print(confd)
    print(key + "-utt%d-final" % utt, out["text"], flush=True)

    # Now send the final utterance to the frontend
    # (this will also indicate that this is a final utterance and the front displays it differently)
    if asr_client is not None:
        asr_client.completeUtterance(
            utterance=out["text"],
            key=key + "-utt%d-part%d" % (utt, part),
            confidences=confd,
            speaker=speaker,
        )

    return out, confd


def reinitialize_asr(adaptation_state, asr, decodable_opts, feat_info, feat_pipeline):
    """Reinitialize an already initialized Kaldi pipeline, reset the adaptation state"""
    feat_pipeline.get_adaptation_state(adaptation_state)
    feat_pipeline = OnlineNnetFeaturePipeline(feat_info)
    feat_pipeline.set_adaptation_state(adaptation_state)
    asr.set_input_pipeline(feat_pipeline)
    asr.init_decoding()
    sil_weighting = OnlineSilenceWeighting(
        asr.transition_model,
        feat_info.silence_weighting_config,
        decodable_opts.frame_subsampling_factor,
    )
    return feat_pipeline, sil_weighting

