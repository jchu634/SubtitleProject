# Written by https://github.com/s0d3s (https://github.com/s0d3s/PyAudioWPatch/issues/9)
import speech_recognition as sr
import audioop

try:
    import pyaudiowpatch
except ImportError:
    raise AttributeError("Could not find PyAudioWPatch; check installation")

pyaudio = pyaudiowpatch

class AudioBridge(sr.AudioSource):
    """
    Capture audio from speakers(via loopback, on Windows)
    """
    format = pyaudio.paInt16  # 16-bit int sampling

    def __init__(self, device_index=None, sample_rate=None, chunk_size=1024):
        assert device_index is None or isinstance(device_index, int), "Device index must be None or an integer"
        assert sample_rate is None or (isinstance(sample_rate, int) and sample_rate > 0), "Sample rate must be None or a positive integer"
        assert isinstance(chunk_size, int) and chunk_size > 0, "Chunk size must be a positive integer"

        # set up PyAudio
        self.pyaudio_module = self.get_pyaudio()
        audio = self.pyaudio_module.PyAudio()
        try:
            count = audio.get_device_count()  # obtain device count
            if device_index is not None:  # ensure device index is in range
                assert 0 <= device_index < count, "Device index out of range ({} devices available; device index should be between 0 and {} inclusive)".format(count, count - 1)

            device_info = None
            if device_index is not None:
                device_info = audio.get_device_info_by_index(device_index)
                assert device_info.get("isLoopbackDevice", False), f"Device with index {device_index} is not a loopback"
            else:
                default_speaker = audio.get_default_output_device_info()
                for loopback in audio.get_loopback_device_info_generator():
                    if loopback["name"].startswith(default_speaker["name"]):
                        device_info = loopback
                        break

                assert device_info is not None, "Unable to find loopback for default speakers"
                device_index = device_info["index"]

            if sample_rate is None:  # automatically set the sample rate to the hardware's default sample rate if not specified
                assert isinstance(device_info.get("defaultSampleRate"), (float, int)) and device_info["defaultSampleRate"] > 0, "Invalid device info returned from PyAudio: {}".format(device_info)
                sample_rate = int(device_info["defaultSampleRate"])

            channels = device_info["maxInputChannels"]
        finally:
            audio.terminate()

        self.device_index = device_index
        self.channels = channels
        self.SAMPLE_WIDTH = self.pyaudio_module.get_sample_size(self.format)  # size of each sample
        self.SAMPLE_RATE = sample_rate  # sampling rate in Hertz
        self.CHUNK = chunk_size  # number of frames stored in each buffer

        self.audio = None
        self.stream = None

    def __enter__(self):
        assert self.stream is None, "This audio source is already inside a context manager"
        self.audio = self.pyaudio_module.PyAudio()
        try:
            self.stream = self.LoopbackStream(
                self.audio.open(
                    input_device_index=self.device_index, channels=self.channels, format=self.format,
                    rate=self.SAMPLE_RATE, frames_per_buffer=self.CHUNK, input=True,
                )
            )
        except Exception:
            self.audio.terminate()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.stream.close()
        finally:
            self.stream = None
            self.audio.terminate()

    @staticmethod
    def get_pyaudio():
        return pyaudiowpatch

    class LoopbackStream(object):
        def __init__(self, pyaudio_stream):
            self.pyaudio_stream = pyaudio_stream

        def read(self, size):
            return audioop.tomono(
                self.pyaudio_stream.read(size, exception_on_overflow=False),
                AudioBridge.get_pyaudio().get_sample_size(AudioBridge.format),
                1, 1
            )

        def close(self):
            try:
                # sometimes, if the stream isn't stopped, closing the stream throws an exception
                if not self.pyaudio_stream.is_stopped():
                    self.pyaudio_stream.stop_stream()
            finally:
                self.pyaudio_stream.close()