import unittest
import threading
import time
from audio_recorder import AudioRecorder
from transcriber import Transcriber
from screen_recorder import ScreenRecorder
from dotenv import load_dotenv
import os

class TestIntegratedClasses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load environment variables from .env file
        load_dotenv()
        # Ensure the OpenAI API key is set
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise EnvironmentError("OPENAI_API_KEY not found in environment variables")

    def setUp(self):
        self.audio_recorder = AudioRecorder()
        self.transcriber = Transcriber()
        self.screen_recorder = ScreenRecorder(1)  # Assuming monitor 1 for the test
        self.stop_event = threading.Event()

    def test_record_transcribe_screen(self):
        # Start screen recording in a separate thread
        screen_rec_thread = threading.Thread(target=self.screen_recorder.start_recording)
        screen_rec_thread.start()

        # Start audio recording and transcribing in a separate thread
        audio_rec_thread = threading.Thread(target=self.record_and_transcribe)
        audio_rec_thread.start()

        # Allow some time for recording
        time.sleep(10)

        # Stop recording
        self.stop_event.set()
        self.audio_recorder.stop()
        self.screen_recorder.stop_recording()

        # Join threads
        audio_rec_thread.join()
        screen_rec_thread.join()

        # Check if screen recording file exists
        self.assertTrue(os.path.exists(self.screen_recorder.output_file))

    def record_and_transcribe(self):
        audio_data_list = []
        try:
            for audio_data in self.audio_recorder.record(self.stop_event):
                audio_data_list.append(audio_data)
                if self.stop_event.is_set():
                    break
        except Exception as e:
            print(f"Error during audio recording: {e}")

        # Transcribe audio data
        for audio_data in audio_data_list:
            try:
                result = self.transcriber.transcribe(audio_data)
                print(f"Transcription: {result}")
            except Exception as e:
                print(f"Error during transcription: {e}")

if __name__ == "__main__":
    unittest.main()
