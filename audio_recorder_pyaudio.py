import pyaudio
import speech_recognition as sr
import logging

class AudioRecorderPyAudio:
    def __init__(self, rate=16000, chunk_size=2048):
        self.rate = rate
        self.chunk_size = chunk_size
        self.is_recording = False
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.logger = logging.getLogger(__name__)

        info = self.audio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')

        for i in range(0, numdevices):
            if (self.audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                print("Input Device id ", i, " - ", self.audio.get_device_info_by_host_api_device_index(0, i).get('name'))

    def start_recording(self):
        self.stream = self.audio.open(format=pyaudio.paInt16, channels=1,
                                      rate=self.rate, input=True,
                                      frames_per_buffer=self.chunk_size, input_device_index=4)
        self.is_recording = True
        self.logger.debug("Starting recording...")

    def record(self):
        self.start_recording()
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = sr.AudioData(data, self.rate, 2)
                yield audio_data
            except IOError as e:
                if e.errno == pyaudio.paInputOverflowed:
                    self.logger.warning("Input overflowed, skipping chunk")
                    continue
                else:
                    self.logger.error(f"Error during recording: {e}")
                    break
        self.stop()

    def stop(self):
        self.logger.info("Stopping recording")
        self.is_recording = False
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        self.audio.terminate()