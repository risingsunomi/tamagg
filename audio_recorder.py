import logging
import speech_recognition as sr

class AudioRecorder:
    def __init__(self, rate=16000, chunk_size=1024):
        self.recognizer = sr.Recognizer()
        self.source = sr.Microphone(sample_rate=rate, chunk_size=chunk_size)
        self.is_recording = False
        self.logger = logging.getLogger(__name__)

    def record(self):
        self.logger.debug("Starting recording...")
        if self.is_recording:
            self.logger.error("Recording is already in progress.")
            return
        try:
            with self.source as source:
                self.recognizer.adjust_for_ambient_noise(source)
                self.is_recording = True
                while self.is_recording:
                    self.logger.info("recording...")
                    audio = self.recognizer.listen_in_background(source)
                    yield audio
        except Exception as e:
            self.logger.error(f"Error during recording: {e}")
        finally:
            self.is_recording = False
            self.logger.info("Recording stopped")

    def stop(self):
        self.logger.info("Stopping recording")
        self.is_recording = False
        
