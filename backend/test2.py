import pyaudio
import speech_recognition as sr

# r = sr.Recognizer()
# r.energy_threshold = 4000

# # for index, name in enumerate(sr.Microphone.list_microphone_names()):
# #     print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))

# # returns a list of 15 devices (microphone, system speakers, headphones...)
# print(sr.Microphone.list_working_microphones())

# with sr.Microphone(21) as source:
#     audio = r.listen(source)

# try:
#     print("Speech was:" + r.recognize_google(audio))
# except LookupError:
#     print('Speech not understood')


def main():
    r = sr.Recognizer()

    with sr.Microphone(device_index=49) as source:

        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)

    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-us')
        print("User said: {query}\n")

    except Exception as e:
        print(e)
        # print("I can't hear you sir.")
        # return "None"


if __name__ == '__main__':
    main()
