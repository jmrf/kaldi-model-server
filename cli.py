import argparse

def get_args():
    parser = argparse.ArgumentParser(
        description="Starts a Kaldi nnet3 decoder")
    parser.add_argument(
        "-i",
        "--input",
        dest="input",
        help="Input scp, simulate online decoding from wav files",
        type=str,
        default="scp:conf/wav.scp",
    )
    parser.add_argument(
        "-l",
        "--list-audio-interfaces",
        dest="list_audio_interfaces",
        help="List all available audio interfaces on this system",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-m",
        "--mic-id",
        dest="micid",
        help="Microphone ID, if not set to -1, do online decoding directly from the microphone.",
        type=int,
        default="-1",
    )

    parser.add_argument(
        "-e",
        "--enable-server-mic",
        dest="enable_server_mic",
        help="If -e is set, use redis audio data channel instead of a local microphone",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-c",
        "--channels",
        dest="channels",
        help="Number of channels to record from the microphone, ",
        type=int,
        default=1,
    )

    parser.add_argument(
        "-wait",
        "--wait-for-start-command",
        dest="wait_for_start_command",
        help="Do not start decoding directly, wait for a start command from the redis control channel.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-hist",
        "--record-message-history",
        dest="record_message_history",
        help="Record message history as a new Python program, useful for debugging and message replay.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-s",
        "--speaker-name",
        dest="speaker_name",
        help="Name of the speaker, use #c# for channel",
        type=str,
        default="speaker#c#",
    )
    parser.add_argument(
        "-cs",
        "--chunk_size",
        dest="chunk_size",
        help="Default buffer size for the microphone buffer.",
        type=int,
        default=1024,
    )

    parser.add_argument(
        "-bs",
        "--beam_size",
        dest="beam_size",
        help="Beam size of the decoding beam. Defaults to 10.",
        type=int,
        default=10,
    )

    parser.add_argument(
        "-fpc",
        "--frames_per_chunk",
        dest="frames_per_chunk",
        help="Frames per (decoding) chunk. This will also have an effect on latency.",
        type=int,
        default=30,
    )

    parser.add_argument(
        "-rs",
        "--redis-server",
        dest="redis_server",
        help="Hostname or IP of the server (for redis-server)",
        type=str,
        default="localhost",
    )

    parser.add_argument(
        "-red",
        "--redis-channel",
        dest="redis_channel",
        help="Name of the channel (for redis-server)",
        type=str,
        default="asr",
    )

    parser.add_argument(
        "--redis-audio",
        dest="redis_audio_channel",
        help="Name of the channel (for redis-server)",
        type=str,
        default="asr_audio",
    )
    parser.add_argument(
        "--redis-control",
        dest="redis_control_channel",
        help="Name of the channel (for redis-server)",
        type=str,
        default="asr_control",
    )

    parser.add_argument(
        "-y",
        "--yaml-config",
        dest="yaml_config",
        help="Path to the yaml model config",
        type=str,
        default="conf/en_160k_nnet3chain_tdnn1f_2048_sp_bi.yaml",
    )
    parser.add_argument(
        "-o",
        "--online-config",
        dest="online_config",
        help=(
            "Path to the Kaldi online config. If not available, will try to read the " ,
            "parameters from the yaml file and convert it to the Kaldi online config ",
            "format (See online_config_options.info.txt for details)",
        ),
        type=str,
        default="models/kaldi_tuda_de_nnet3_chain2.online.conf",
    )
    parser.add_argument(
        "-r",
        "--record-samplerate",
        dest="record_samplerate",
        help="The recording samplingrate if a microphone is used",
        type=int,
        default=16000,
    )
    parser.add_argument(
        "-d",
        "--decode-samplerate",
        dest="decode_samplerate",
        help="Decode samplerate, if not the same as the microphone samplerate "
        "then the signal is automatically resampled",
        type=int,
        default=16000,
    )

    parser.add_argument(
        "-a",
        "--resample_algorithm",
        dest="resample_algorithm",
        help="One of the following: linear, sinc_best, sinc_fastest,"
        " sinc_medium, zero_order_hold (default: sinc_best)",
        type=str,
        default="sinc_fastest",
    )

    parser.add_argument(
        "-t",
        "--use-threads",
        dest="use_threads",
        help="Use a thread worker for realtime decoding",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-mf",
        "--minimum-num-frames-decoded-per-speaker",
        dest="minimum_num_frames_decoded_per_speaker",
        help="Minimum number of frames that need to be decoded per speaker until a speaker change can happen",
        type=int,
        default=5,
    )

    parser.add_argument(
        "-w",
        "--save_debug_wav",
        dest="save_debug_wav",
        help="This will write out a debug.wav (resampled)"
        " and debugraw.wav (original) after decoding,"
        " so that the recording quality can be analysed",
        action="store_true",
        default=False,
    )

    return parser.parse_args()
