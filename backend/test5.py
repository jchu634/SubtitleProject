import pyaudiowpatch as pyaudio
import wave

audio = pyaudio.PyAudio()

# List all devices
for i in range(audio.get_device_count()):
    device_info = audio.get_device_info_by_index(i)
    print("Device index: ", i)
    print("Name: ", device_info["name"])
    print("Channels: ", device_info["maxInputChannels"])
    print("Sample rate: ", device_info["defaultSampleRate"])
    print("-----------------------------")

# Prompt for device index
# device_index = int(input("Enter the device index: "))

# # Set your recording parameters
# FORMAT = pyaudio.paInt16  # sample format
# CHANNELS = 1  # mono
# RATE = 48000  # sample rate
# CHUNK = 1024  # frames per buffer
# RECORD_SECONDS = 10  # length of recording in seconds
# WAVE_OUTPUT_FILENAME = "output.wav"  # output file name

# # Open the stream with the chosen device
# stream = audio.open(format=FORMAT, channels=CHANNELS,
#                     rate=RATE, input=True,
#                     frames_per_buffer=CHUNK,
#                     input_device_index=device_index)

# print("Recording...")

# frames = []

# # Record for the desired number of seconds
# for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
#     data = stream.read(CHUNK)
#     frames.append(data)

# print("Finished recording")

# # Stop and close the stream
# stream.stop_stream()
# stream.close()

# Terminate the PortAudio interface
audio.terminate()

# Save the recorded data as a WAV file
# wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
# wf.setnchannels(CHANNELS)
# wf.setsampwidth(audio.get_sample_size(FORMAT))
# wf.setframerate(RATE)
# wf.writeframes(b''.join(frames))
# wf.close()

# print("Output saved to", WAVE_OUTPUT_FILENAME)
