import unittest
from llm_tts import LLMTTS
from console_display import ConsoleDisplay
from dotenv import load_dotenv
import os

class TestLLMTTS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load environment variables from .env file
        load_dotenv()
        # Ensure the OpenAI API key is set
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise EnvironmentError("OPENAI_API_KEY not found in environment variables")

    def setUp(self):
        # Initialize a mock console display
        self.console_display = ConsoleDisplay(None)
        
        # Initialize the LLMTTS class
        self.llmtts = LLMTTS(console_display=self.console_display)

    def test_transcribe_and_respond(self):
        # Path to the example video of the Three Stooges
        video_path = "data/tsbank.mp4"
        
        # Example transcription text/question
        transcription_text = "Does this explain the modern banking system?"

        # Run the transcribe and respond method
        response_text = self.llmtts.transcribe_and_respond(video_path, transcription_text)

        # Check if the response text is not empty
        self.assertIsNotNone(response_text)
        self.assertTrue(len(response_text) > 0)

        # Print the response text for manual verification
        print(f"AI Response: {response_text}")

if __name__ == "__main__":
    unittest.main()
