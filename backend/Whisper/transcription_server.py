# Webserver imports
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from config import Settings

# Transription Imports
import os
import numpy as np
import speech_recognition as sr
from whisper.transcribe import transcribe
from whisper.model import load_model
import pyaudiowpatch as pyaudio

import audioop

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
        return pyaudio

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

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
import asyncio

# Debug Imports
import uuid
import wave


transcribe_api = APIRouter(tags=["Transcription"])

active_connections_set = set()


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


onnx_encoder_path: str = "Whisper\\models\\float-encoder.onnx"
onnx_decoder_path: str = "Whisper\\models\\quant-decoder.onnx"

encoder_target: str = 'cpu'
decoder_target: str = 'aie'

debug_enabled = Settings.ENV == "development"

@transcribe_api.websocket("/transcription_feed")
async def transcription_ws_endpoint(websocket: WebSocket):
    # await manager.connect(websocket)
    await websocket.accept()
    active_connections_set.add(websocket)
    
    phrase_time = None      # The last time a recording was retrieved from the queue.
    data_queue = Queue()    # Thread safe Queue for passing data from the threaded recording callback.
    recorder = sr.Recognizer()      # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder.energy_threshold = Settings.energy_threshold
    record_timeout = Settings.record_timeout
    phrase_timeout = Settings.phrase_timeout   
    recorder.dynamic_energy_threshold = True    # Set to True to always record, (Dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.)
    
    audio = pyaudio.PyAudio()  
    mic = Settings.SOUND_DEVICE
    
    if "Loopback" in audio.get_device_info_by_index(mic)["name"]:
        # Note: Loopback interfaces do not support sample_rates (https://github.com/s0d3s/PyAudioWPatch/issues/15#issuecomment-2025114713)
        source = AudioBridge(device_index=mic)
    else:
        source = sr.Microphone(sample_rate=16000)

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

    model = load_model('tiny', onnx_encoder_path, onnx_decoder_path, encoder_target, decoder_target)
    
    try:
        # Cue the user that we're ready to go.
        await websocket.send_text(f"Model loaded.") 
        
        if debug_enabled:
            debug_folder = uuid.uuid4().hex     # UUID Folder name for storing debug audio files

        while Settings._enable_transcription:
            now = datetime.utcnow()
            
            # Pull raw recorded audio from the queue.
            if not data_queue.empty():
                phrase_complete = False

                # Initialize phrase_start_time if not already set
                if 'phrase_start_time' not in locals() or phrase_start_time is None:
                    phrase_start_time = now


                # If enough time has passed between recordings, consider the phrase complete.
                # Additionally, due to model limitations, kill the phrase after 10 seconds as the model becomes less accurate.
                # Clear the current working audio buffer to start over with the new data.
                if phrase_time and (now - phrase_time > timedelta(seconds=phrase_timeout) or now - phrase_start_time > timedelta(seconds=10)):
                    phrase_complete = True
                    phrase_start_time = None
                    print("PHRASE COMPLETE")
                    await websocket.send_text("[PHRASE_COMPLETE]")


                phrase_time = now   # Last time new audio data was received from the queue.
                
                audio_data = b''.join(data_queue.queue)     # Combine audio data from queue
                data_queue.queue.clear()
                
                # Convert in-ram buffer to something the model can use directly without needing a temp file.
                # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
                # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                if debug_enabled:
                    save_debug_audio(audio_np, source.SAMPLE_RATE, debug_folder)    # Save the audio_np array to a .wav file for debugging

                # Note: Arguments are hard-coded as the model does not fully support alternative options.
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

                # Send only the latest line of transcription to the client.
                await websocket.send_text(transcription[-1])

                # # Clear the console to reprint the updated transcription.
                # await websocket.send_text("[TERMINATE_TRANSCRIPTION]")
                # for line in transcription:
                #     await websocket.send_text(line)
                
                # This call is neccessary, as the server never realises the client has disconnected otherwise.
                ack = await websocket.receive_text() # Wait for the client to acknowledge the transcription.
            else:
                asyncio.sleep(600)  # Infinite loops are bad for processors, must sleep.
    except WebSocketDisconnect:
        websocket.close()
        print("Client disconnected Normally")
        print("\n\nTranscription:")
        for line in transcription:
            print(line)
        return
    except RuntimeError:
        print("Client disconnected via RuntimeError")
        print("\n\nTranscription:")
        for line in transcription:
            print(line)
        return
    except IOError:
        print("Client disconnected via IOError")
        print("\n\nTranscription:")
        for line in transcription:
            print(line)


# # TODO: Fix to not use deprecated FastAPI event handler
# # Uses deprecated FastAPI event handler 
# @transcribe_api.on_event("shutdown")
# async def shutdown():
#     for websocket in active_connections_set:
#         await websocket.close()

# @transcribe_api.get("/api/disable_transcription")
# def disable_transcription():
#     print("disabled transcription")
#     Settings._enable_transcription = False
#     return {"message": "Transcription Disabled"}

# @transcribe_api.get("/api/enable_transcription")
# def enable_transcription():
#     print("enabled transcription")
#     Settings._enable_transcription = True
#     return {"message": "Transcription Enabled"}
    