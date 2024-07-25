import argparse
import os
import numpy as np
import speech_recognition as sr
import pyaudiowpatch
from AudioBridge import AudioBridge

import torch

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform

import whisper


def main():
    # The last time a recording was retrieved from the queue.
    phrase_time = None
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()
    recorder = sr.Recognizer()
    recorder.energy_threshold = 40
    # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
    recorder.dynamic_energy_threshold = False

    audio = pyaudiowpatch.PyAudio()

    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        print("Device index: ", i)
        print("Name: ", device_info["name"])
        print("Channels: ", device_info["maxInputChannels"])
        print("Sample rate: ", device_info["defaultSampleRate"])
        print("-----------------------------")

    mic = int(input("Select Mic: "))
    if "Loopback" in audio.get_device_info_by_index(mic)["name"]:
        source = AudioBridge(device_index=mic)
        # Note: Loopback interfaces do not support sample_rates (https://github.com/s0d3s/PyAudioWPatch/issues/15#issuecomment-2025114713)
    else:
        source = sr.Microphone(sample_rate=16000)

    record_timeout = 2
    phrase_timeout = 3

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
    print("Ready and Recording.\n")

    # ...
    import wave

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
    wf.setframerate(source.SAMPLE_RATE)  # Assuming the audio is at 16000Hz

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
                # audio_np = np.frombuffer(
                #     audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                # audio_bytes = (audio_np * 32768.0).astype(np.int16).tobytes()
                # wf.writeframes(audio_bytes)

            else:
                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            break

    wf.close()


if __name__ == "__main__":
    main()
