import logging
import threading
import speech_recognition as sr

class AudioRecorder:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.source = None
        self.logger = logging.getLogger(__name__)
        self.stop_event = threading.Event()

    def record(self):
        self.logger.debug("Starting recording...")
        self.source = sr.Microphone()
        self.stop_event.clear()
        try:
            with self.source as source:
                self.recognizer.adjust_for_ambient_noise(source)
                while not self.stop_event.is_set():
                    self.logger.info("recording...")
                    audio = self.recognizer.listen(source)
                    yield audio
        except Exception as e:
            self.logger.error(f"Error during recording: {e}")

    def stop(self):
        self.logger.info("Stopping recording")
        self.stop_event.set()
        
