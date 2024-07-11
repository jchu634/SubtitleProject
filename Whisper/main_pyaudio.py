#! python3.7

import argparse
import os
import numpy as np
import speech_recognition as sr
from whisper.transcribe import transcribe
from whisper.model import load_model
import pyaudiowpatch as pyaudio

from AudioBridge import AudioBridge

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform

import uuid
import wave

def save_debug_audio(audio_np, sample_rate, folder="default"):
    debug_dir = os.path.join("debug", folder)
    os.makedirs(debug_dir, exist_ok=True)
    
    # Find the next available filename
    file_index = 0
    while os.path.exists(os.path.join(debug_dir, f"audio_{file_index}.wav")):
        file_index += 1
    
    debug_filename = os.path.join(debug_dir, f"audio_{file_index}.wav")
    
    # Save the audio_np array to a .wav file
    with wave.open(debug_filename, 'w') as wf:
        wf.setnchannels(1)  # Mono audio
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(sample_rate)
        wf.writeframes((audio_np * 32768).astype(np.int16).tobytes())
    
    return debug_filename


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--non_english", action='store_true',
                        help="Don't use the english model.")
    parser.add_argument("--energy_threshold", default=1000,
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
    recorder.dynamic_energy_threshold = True

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
    #                 source = sr.Microphone(sample_rate=16000, device_index=index)
    #                 break
    # else:
    #     source = sr.Microphone(sample_rate=16000)

    audio = pyaudio.PyAudio()

    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        print("Device index: ", i)
        print("Name: ", device_info["name"])
        print("Channels: ", device_info["maxInputChannels"])
        print("Sample rate: ", device_info["defaultSampleRate"])
        print("-----------------------------")

    mic = int(input("Select Mic: "))
    if "Loopback" in audio.get_device_info_by_index(mic)["name"]:
        # Note: Loopback interfaces do not support sample_rates
        # https://github.com/s0d3s/PyAudioWPatch/issues/15#issuecomment-2025114713
        source = AudioBridge(device_index=mic)
    else:
        source = sr.Microphone(sample_rate=16000)

    onnx_encoder_path: str = "models\\float-encoder.onnx"
    onnx_decoder_path: str = "models\\quant-decoder.onnx"

    encoder_target: str = 'cpu'
    decoder_target: str = 'aie'

    model = load_model('tiny', onnx_encoder_path, onnx_decoder_path, encoder_target, decoder_target)

    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout

    transcription = ['']

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio:sr.AudioData) -> None:
        """
        Threaded callback function to receive audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        data_queue.put(data)

    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

    # Cue the user that we're ready to go.
    print("Model loaded.\n")


    debug_folder = uuid.uuid4().hex

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
                
                # Convert in-ram buffer to something the model can use directly without needing a temp file.
                # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
                # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                # Save the audio_np array to a .wav file for debugging
                save_debug_audio(audio_np, source.SAMPLE_RATE, debug_folder)

                # Read the transcription.
                # Arguments are hard-coded as the model does not fully support alternative options.
                result = transcribe(model=model, 
                                    audio=audio_np, 
                                    temperature=[0],
                                    task = "transcribe",
                                    language = 'en',
                                    verbose=False,
                                    best_of = 5,
                                    beam_size = 5,
                                    patience = None,
                                    length_penalty = 0.08,
                                    suppress_tokens = "-1",
                                    initial_prompt = None,
                                    condition_on_previous_text = None,
                                    compression_ratio_threshold = 2.4,
                                    logprob_threshold = -1,
                                    no_speech_threshold = 0.6
                                    )
                text = result['text'].strip()

                # If we detected a pause between recordings, add a new item to our transcription.
                # Otherwise edit the existing one.
                if phrase_complete:
                    transcription.append(text)
                else:
                    transcription[-1] = text

                # Clear the console to reprint the updated transcription.
                os.system('cls' if os.name=='nt' else 'clear')
                for line in transcription:
                    print(line)
                # Flush stdout.
                print('', end='', flush=True)
            else:
                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            break

    print("\n\nTranscription:")
    for line in transcription:
        print(line)


if __name__ == "__main__":
    main()