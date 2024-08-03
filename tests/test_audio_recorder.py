import unittest
import logging
import io
import wave
from audio_recorder import AudioRecorder

class TestAudioRecorder(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.audio_recorder = AudioRecorder()

    def test_record_audio(self):
        print("Start speaking... (Press Ctrl+C to stop)")
        audio_data_list = []
        try:
            for audio_data in self.audio_recorder.record():
                audio_data_list.append(audio_data)
                print("Audio captured successfully.")
                break  # Capture one segment for test
        except KeyboardInterrupt:
            print("Stopped recording.")

        self.assertTrue(len(audio_data_list) > 0, "No audio data captured.")
        audio_data = audio_data_list[0]
        audio_bytes = audio_data.get_wav_data()

        # Write the captured audio to a BytesIO stream and read it
        audio_stream = io.BytesIO(audio_bytes)
        wf = wave.open(audio_stream, 'rb')
        self.assertEqual(wf.getframerate(), self.audio_recorder.sample_rate, "Sample rate does not match.")
        self.assertEqual(wf.getnchannels(), 1, "Number of channels does not match.")
        frames = wf.readframes(wf.getnframes())
        self.assertTrue(len(frames) > 0, "No audio frames captured.")

    def tearDown(self):
        # Clean up resources if needed
        pass

if __name__ == "__main__":
    unittest.main()
