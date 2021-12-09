import pyaudio

from rich import print


def print_devices():

    def _get_dev_info(idx, key):
        return paudio.get_device_info_by_host_api_device_index(0, idx).get(key)

    paudio = pyaudio.PyAudio()
    info = paudio.get_host_api_info_by_index(0)
    numdevices = info.get("deviceCount")
    # for each audio device, determine if is an input or an output and
    # add it to the appropriate list and dictionary
    for i in range(0, numdevices):
        if _get_dev_info(i, "maxInputChannels") > 0:
            print(f"Input Device id {i} - {_get_dev_info(i, 'name')}")

        if _get_dev_info(i, "maxOutputChannels") > 0:
            print(f"Output Device id {i} - {_get_dev_info(i, 'name')}")

