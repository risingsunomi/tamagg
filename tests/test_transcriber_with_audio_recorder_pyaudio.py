import unittest
import logging
from audio_recorder_pyaudio import AudioRecorderPyAudio
from transcriber import Transcriber

class TestTranscriberWithAudioRecorder(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.transcriber = Transcriber()
        self.audio_recorder = AudioRecorderPyAudio()

    def test_transcribe_from_microphone(self):
        print("Start speaking... (Press Ctrl+C to stop)")
        try:
            for audio_data in self.audio_recorder.record():
                try:
                    result = self.transcriber.transcribe(audio_data)
                    self.assertIsNotNone(result)
                    if result.strip():  # Only print non-empty transcriptions
                        print(f"Transcription from microphone: {result}")
                except Exception as e:
                    print(f"Error during transcription: {e}")
        except KeyboardInterrupt:
            print("Stopped recording.")

if __name__ == "__main__":
    unittest.main()
