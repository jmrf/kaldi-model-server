from kserver.asr import decode_chunked_partial_endpointing
from kserver.asr import load_model
from kserver.asr import mic_asr
from kserver.cli import get_args
from kserver.redis_channel import ASRRedisClient
from kserver.utils import print_devices


if __name__ == "__main__":

    args = get_args()

    if args.list_audio_interfaces:
        print("Listing audio interfaces...")
        print_devices()
    else:
        # Init Redis client
        asr_client = ASRRedisClient(
            host=args.redis_server,
            channel=args.redis_channel,
            record_message_history=args.record_message_history,
        )
        # Send message via Reddis
        asr_client.asr_loading(speaker=args.speaker_name)

        # Load ASR model
        asr, feat_info, decodable_opts = load_model(
            args.yaml_config,
            args.online_config,
            beam_size=args.beam_size,
            frames_per_chunk=args.frames_per_chunk,
        )

        # Decode
        if args.micid == -1:
            print("Reading from wav scp:", args.input)
            asr_client.asr_ready(speaker=args.speaker_name)
            decode_chunked_partial_endpointing(
                asr,
                feat_info,
                decodable_opts,
                args.input,
                asr_client=asr_client,
                speaker=args.speaker_name,
                chunk_size=args.chunk_size,
            )
        else:
            import pyaudio

            paudio = pyaudio.PyAudio()
            mic_asr(
                asr,
                feat_info,
                decodable_opts,
                input_microphone_id=args.micid,
                samp_freq=args.decode_samplerate,
                record_samplerate=args.record_samplerate,
                chunk_size=args.chunk_size,
                channels=args.channels,
                resample_algorithm=args.resample_algorithm,
                save_debug_wav=args.save_debug_wav,
                use_threads=args.use_threads,
                minimum_num_frames_decoded_per_speaker=args.minimum_num_frames_decoded_per_speaker,
            )
