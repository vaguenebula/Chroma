import importlib
import threading
import time
import keyboard
from vosk import Model, KaldiRecognizer, SetLogLevel
from pyaudio import PyAudio, paInt16
from playsound import playsound
from sys import getsizeof

# When set to true, program loop will enter a dictate mode where the keyboard types what the user is saying
import gui

dictate: bool = False

# A dictionary with commonly misspelled names / programs / words
listOfMisspells: dict = {"spot a thigh": "Spotify", "spot of i": "Spotify", "spot if i": "Spotify",
                         "spot a fire": "Spotify", "bonafide": "Spotify", "spot of fi": "Spotify",
                         "to escort": "discord", "a bolton": "Ableton", "able to": "Ableton", "calculate": "Calculator",
                         "spot i": "Spotify", "hoping": "open", "mark a player": "Markiplier",
                         "market blair": "Markiplier", "spot a fight": "Spotify", "spot a hi": "Spotify",
                         "you too": "Youtube", "you tube": "Youtube", "birch": "search", "you to": "Youtube",
                         "explore": "Explorer"}
print(f"Allocated bytes for dictionary: {getsizeof(listOfMisspells)}")

# Able to access what the current word stream up until the final result
currentWordStream: str = ""


class ChromaApplication:
    enabledMic = False
    SetLogLevel(-1)
    model = Model("./models/vosk-model-small-en-us-0.15")
    recognizer = KaldiRecognizer(model, 16000)
    mic = PyAudio()
    stream = mic.open(format=paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
    possibleKeywords = {}

    # constructor for application which takes a list of plugins
    def __init__(self, plugins: list = []):

        if plugins:
            # create a list of plugins
            self._plugins = [
                importlib.import_module(plugin, "./plugins/" + plugin).Plugin() for plugin in plugins
            ]

            # Generate a dictionary of keywords containing the keyword and boolean
            # If the boolean is True, then the keyword MUST be in the beginning of the text
            # in order for the plugin to start
            for eachPlugin in self._plugins:
                for eachKeyword in eachPlugin.keywords:
                    if eachKeyword not in self.possibleKeywords:
                        self.possibleKeywords[eachKeyword] = eachPlugin.keywords.get(eachKeyword)

    def run(self, stream=stream, recognizer=recognizer):


        print("Starting my application")
        print("-" * 10)
        print("Running with the following plugins:")

        for plugin in self._plugins:
            print(f"{plugin.name.upper()} by {plugin.author}")

        print("-" * 10)
        # print("Ending my application")
        print()

        while True:
            global dictate
            global currentWordStream

            if dictate is True:
                if stream.is_stopped():
                    stream.start_stream()
                data = stream.read(4096, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    text = recognizer.Result()[14:-3]
                    if text == "dictate":
                        dictate = False
                        stream.stop_stream()
                        playsound("./assets/sfx/voiceoff.mp3", False)
                    else:
                        keyboard.write(text + " ")

            else:
                if self.enabledMic:
                    data = stream.read(4096, exception_on_overflow=False)

                    if recognizer.AcceptWaveform(data):

                        text: str = recognizer.Result()[14:-3]
                        self.enabledMic = False
                        gui.activate_mic_indicator()

                        print(f"\nPreliminary Result: {text}")

                        # Replacing each misspelled word with the correct word
                        start: int = time.perf_counter_ns()
                        for eachWord in (x for x in listOfMisspells if f" {x} " in f" {text} "):
                            text = text.replace(eachWord, listOfMisspells.get(eachWord))

                        print(f"Time taken to replace words: {time.perf_counter_ns() - start} nanoseconds")
                        print(f"Final Result: {text}")

                        # If the first word is a keyword, then it will start a new thread which
                        # runs the associated plugin
                        # However, if not first word, check if the boolean is false
                        for eachKeyword in self.possibleKeywords:
                            if eachKeyword in text:
                                if text.index(eachKeyword) == 0:
                                    threading.Thread(
                                        target=next(x for x in self._plugins if eachKeyword in x.keywords).process,
                                        args=(text,),
                                        daemon=True).start()
                                    break
                                elif not self.possibleKeywords.get(eachKeyword):
                                    threading.Thread(
                                        target=next(x for x in self._plugins if eachKeyword in x.keywords).process,
                                        args=(text,),
                                        daemon=True).start()
                                    break

                        currentWordStream = ""
                        playsound("./assets/sfx/voiceoff.mp3", False)

                    else:
                        if (recognizer.PartialResult()[17:-3]).split(" ")[-1] not in currentWordStream:
                            currentWordStream = currentWordStream + (recognizer.PartialResult()[17:-3]).split(" ")[
                                -1] + " "
                            print(currentWordStream)

    def enable_mic(self):
        if not dictate:
            if self.enabledMic is False:
                print("STARTING MIC")
                self.enabledMic = True
                playsound("./assets/sfx/voiceon.mp3", False)
                gui.activate_mic_indicator()




