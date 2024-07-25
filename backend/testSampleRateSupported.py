import pyaudiowpatch


def check_sample_rate_supported(sample_rate=16000):
    p = pyaudiowpatch.PyAudio()
    devinfo = p.get_device_info_by_index(40)

    print(p.is_format_supported(float(sample_rate),
                                input_device=devinfo['index'],
                                input_channels=devinfo['maxInputChannels'],
                                input_format=pyaudiowpatch.paInt16
                                ))


if __name__ == "__main__":
    # sample_rate = int(input("Sample rate: "))
    sample_rate = 44100.0
    print(f"SampleRate: {sample_rate}")
    check_sample_rate_supported(sample_rate)
