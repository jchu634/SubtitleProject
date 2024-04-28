import argparse
import os
import numpy as np
import speech_recognition as sr
import pyaudiowpatch
import audioop
import torch

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform

import whisper


class AudioBridge(sr.AudioSource):
    """
    Capture audio from speakers(via loopback, on Windows)
    """
    format = pyaudiowpatch.paInt16  # 16-bit int sampling

    def __init__(self, device_index=None, sample_rate=None, chunk_size=1024):
        assert device_index is None or isinstance(
            device_index, int), "Device index must be None or an integer"
        assert sample_rate is None or (isinstance(
            sample_rate, int) and sample_rate > 0), "Sample rate must be None or a positive integer"
        assert isinstance(
            chunk_size, int) and chunk_size > 0, "Chunk size must be a positive integer"

        # set up PyAudio
        self.pyaudio_module = self.get_pyaudio()
        audio = self.pyaudio_module.PyAudio()
        try:
            count = audio.get_device_count()  # obtain device count
            if device_index is not None:  # ensure device index is in range
                assert 0 <= device_index < count, "Device index out of range ({} devices available; device index should be between 0 and {} inclusive)".format(
                    count, count - 1)

            device_info = None
            if device_index is not None:
                device_info = audio.get_device_info_by_index(device_index)
                assert device_info.get(
                    "isLoopbackDevice", False), f"Device with index {device_index} is not a loopback"
            else:
                default_speaker = audio.get_default_output_device_info()
                for loopback in audio.get_loopback_device_info_generator():
                    if loopback["name"].startswith(default_speaker["name"]):
                        device_info = loopback
                        break

                assert device_info is not None, "Unable to find loopback for default speakers"
                device_index = device_info["index"]

            if sample_rate is None:  # automatically set the sample rate to the hardware's default sample rate if not specified
                assert isinstance(device_info.get("defaultSampleRate"), (float, int)
                                  ) and device_info["defaultSampleRate"] > 0, "Invalid device info returned from PyAudio: {}".format(device_info)
                sample_rate = int(device_info["defaultSampleRate"])

            channels = device_info["maxInputChannels"]
        finally:
            audio.terminate()

        self.device_index = device_index
        self.channels = channels
        self.SAMPLE_WIDTH = self.pyaudio_module.get_sample_size(
            self.format)  # size of each sample
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="medium", help="Model to use",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--non_english", action='store_true',
                        help="Don't use the english model.")
    parser.add_argument("--energy_threshold", default=40,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=2,
                        help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=3,
                        help="How much empty space between recordings before we "
                             "consider it a new line in the transcription.", type=float)
    if 'linux' in platform:
        parser.add_argument("--default_microphone", default='pulse',
                            help="Default microphone name for SpeechRecognition. "
                                 "Run this with 'list' to view available Microphones.", type=str)
    args = parser.parse_args()

    # The last time a recording was retrieved from the queue.
    phrase_time = None
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()
    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
    recorder.dynamic_energy_threshold = False

    # Important for linux users.
    # Prevents permanent application hang and crash by using the wrong Microphone
    # if 'linux' in platform:
    #     mic_name = args.default_microphone
    #     if not mic_name or mic_name == 'list':
    #         print("Available microphone devices are: ")
    #         for index, name in enumerate(sr.Microphone.list_microphone_names()):
    #             print(f"Microphone with name \"{name}\" found")
    #         return
    #     else:
    #         for index, name in enumerate(sr.Microphone.list_microphone_names()):
    #             if mic_name in name:
    #                 source = sr.Microphone(
    #                     sample_rate=16000, device_index=index)
    #                 break
    # else:
    #     source = sr.Microphone(sample_rate=16000)
    audio = pyaudiowpatch.PyAudio()

    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        print("Device index: ", i)
        print("Name: ", device_info["name"])
        print("Channels: ", device_info["maxInputChannels"])
        print("Sample rate: ", device_info["defaultSampleRate"])
        print("-----------------------------")

    mic = int(input("Select Mic: "))
    # Note: Setting the sample_rate seems to cause errors
    if "Loopback" in audio.get_device_info_by_index(mic)["name"]:
        source = AudioBridge(device_index=mic)
    else:
        source = sr.Microphone(sample_rate=16000)

    # Load / Download model
    model = args.model
    if args.model != "large" and not args.non_english:
        model = model + ".en"
    # audio_model = whisper.load_model(model)

    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout

    transcription = ['']

    if "Loopback" not in audio.get_device_info_by_index(mic)["name"]:
        with source:
            recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio: sr.AudioData) -> None:
        """
        Threaded callback function to receive audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        data_queue.put(data)

    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    recorder.listen_in_background(
        source, record_callback, phrase_time_limit=record_timeout)

    # Cue the user that we're ready to go.
    print("Model loaded.\n")

    import wave

    # ...

    # Add these lines before the while loop
    import os

    def get_unique_filename(filename):
        base_name, ext = os.path.splitext(filename)
        counter = 1

        while os.path.exists(filename):
            filename = f"{base_name}_{counter}{ext}"
            counter += 1

        return filename

    output_filename = "outputTest.wav"
    output_filename = get_unique_filename(output_filename)

    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(audio.get_sample_size(pyaudiowpatch.paInt16))
    wf.setframerate(16000)  # Assuming the audio is at 16000Hz

    while True:
        try:
            now = datetime.utcnow()
            # Pull raw recorded audio from the queue.
            if not data_queue.empty():
                phrase_complete = False
                # If enough time has passed between recordings, consider the phrase complete.
                # Clear the current working audio buffer to start over with the new data.
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    phrase_complete = True
                # This is the last time we received new audio data from the queue.
                phrase_time = now

                # Combine audio data from queue
                audio_data = b''.join(data_queue.queue)
                data_queue.queue.clear()

                wf.writeframes(audio_data)

                # Convert in-ram buffer to something the model can use directly without needing a temp file.
                # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
                # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
                audio_np = np.frombuffer(
                    audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                # audio_bytes = (audio_np * 32768.0).astype(np.int16).tobytes()
                # wf.writeframes(audio_bytes)

            # Read the transcription.
            # result = audio_model.transcribe(
            #     audio_np, fp16=torch.cuda.is_available())
            # text = result['text'].strip()

            # # If we detected a pause between recordings, add a new item to our transcription.
            # # Otherwise edit the existing one.
            # if phrase_complete:
            #     transcription.append(text)
            # else:
            #     transcription[-1] = text

            # # Clear the console to reprint the updated transcription.
            # os.system('cls' if os.name == 'nt' else 'clear')
            # for line in transcription:
            #     print(line)
            # # Flush stdout.
            # print('', end='', flush=True)
            else:
                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            break

    wf.close()

    print("\n\nTranscription:")
    for line in transcription:
        print(line)


if __name__ == "__main__":
    main()
