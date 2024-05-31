import logging
import speech_recognition as sr

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class AudioRecorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.recognizer = sr.Recognizer()
        self.source = sr.Microphone(sample_rate=self.sample_rate)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.debug("Setting up AudioRecorder")

    def record(self):
        with self.source as source:
            self.recognizer.adjust_for_ambient_noise(source)
            self.logger.info("Recording audio... Press Ctrl+C to stop.")
            try:
                while True:
                    audio_data = self.recognizer.listen(source)
                    yield audio_data
            except KeyboardInterrupt:
                self.logger.info("Recording stopped by user.")
