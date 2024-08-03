import logging
import speech_recognition as sr
from audio_recorder import AudioRecorder

class Transcriber:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Initializing Transcriber")
        self.recognizer = sr.Recognizer()
        self.logger.debug("Recognizer initialized successfully")
        self.audio_recorder = AudioRecorder()
        self.transcribed_text = ""

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
        
    def record_transcribe(self):
        self.logger.info("record_transcribe started")
        try:
            for audio_data in self.audio_recorder.record():
                try:
                    resp = self.transcribe(audio_data)
                    if resp.strip():
                        self.transcribed_text += resp
                except Exception as e:
                    self.logger.error(f"Error during transcription: {e}")
                    break
        except Exception as e:
            self.logger.error(f"Error during audio recording: {e}")
        
        self.logger.info(f"record_transcribe -> \"{self.transcribed_text}\"")
