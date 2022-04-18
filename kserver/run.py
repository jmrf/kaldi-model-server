import logging
import json

from kserver.asr import ASR
from kserver.cli import get_args
from kserver.utils import print_devices

# from kserver.redis_channel import ASRRedisClient
from kserver.rabbit import BlockingQueueConsumer


logger = logging.getLogger(__name__)


if __name__ == "__main__":

    args = get_args()

    if args.list_audio_interfaces:
        logger.info("Listing audio interfaces...")
        print_devices()
    else:
        # # Init Redis client
        # asr_client = ASRRedisClient(
        #     host=args.redis_server,
        #     channel=args.redis_channel,
        #     record_message_history=args.record_message_history,
        # )
        # # Send message via Reddis
        # asr_client.asr_loading(speaker=args.speaker_name)

        # Load ASR model
        asr = ASR(
            args.yaml_config,
            args.online_config,
            models_path="models/",
            beam_size=args.beam_size,
            frames_per_chunk=args.frames_per_chunk,
        )

        # Decode
        # if args.micid == -1:
        #     print("Reading from wav scp:", args.input)
        #     asr_client.asr_ready(speaker=args.speaker_name)
        #     decode_chunked_partial_endpointing(
        #         asr,
        #         feat_info,
        #         decodable_opts,
        #         args.input,
        #         asr_client=asr_client,
        #         speaker=args.speaker_name,
        #         chunk_size=args.chunk_size,
        #     )
        # else:

        def open_mic(event):
            logger.debug(f"Rx event: {event}")
            asr.mic_asr(
                input_microphone_id=args.micid,
                samp_freq=args.decode_samplerate,
                record_samplerate=args.record_samplerate,
                chunk_size=args.chunk_size,
                channels=args.channels,
                resample_algorithm=args.resample_algorithm,
                save_debug_wav=args.save_debug_wav,
                use_threads=args.use_threads,
                continuous=False
                # minimum_num_frames_decoded_per_speaker=args.minimum_num_frames_decoded_per_speaker,
            )

        consumer = BlockingQueueConsumer(
            "localhost",
            on_event=open_mic,
            on_done=lambda: logger.info("Done!"),
            load_func=json.loads,
            queue_name="asr-q",
            exchange_name="fiona",
            exchange_type="topic",
            routing_keys=["hotword-detected"],
        )

        consumer.consume()


