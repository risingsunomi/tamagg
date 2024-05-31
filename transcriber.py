import logging
import speech_recognition as sr

class Transcriber:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Initializing Transcriber")
        self.recognizer = sr.Recognizer()
        self.logger.debug("Recognizer initialized successfully")

    def transcribe(self, audio_data):
        try:
            text = self.recognizer.recognize_whisper(audio_data)
            self.logger.debug("Transcription successful")
            self.logger.debug(f"Transcription result: {text}")
            return text
        except sr.UnknownValueError:
            self.logger.error("Whisper could not understand audio")
            return ""
        except sr.RequestError as e:
            self.logger.error(f"Could not request results from Whisper; {e}")
            raise e
