#! python3.7

import argparse
import os
import shutil
import numpy as np
import speech_recognition as sr
from whisper.transcribe import transcribe
from whisper.model import load_model
import pyaudiowpatch as pyaudio


from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform


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
    recorder.dynamic_energy_threshold = False

    # Important for linux users.
    # Prevents permanent application hang and crash by using the wrong Microphone
    # if 'linux' in p
                
                

                    # Read the transcription.
                    # result = transcribe(temp_audio.name, fp16=True)
    print("Does this ever run")
    result = transcribe(model=model, task="transcribe", 
                        audio=audio_np, temperature=0, compression_ratio_threshold=2.4, 
                        condition_on_previous_text=None, logprob_threshold=-1, language='en', 
                        best_of=5, beam_size=5, patience=None, length_penalty=0.08,
                        suppress_tokens="-1", initial_prompt=None, no_speech_threshold=0.6
                        )
                        
    print("RESULT")
    print(result)
    text = result['text'].strip()

if __name__ == "__main__":
    main()