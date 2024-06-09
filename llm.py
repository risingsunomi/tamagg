import os
import openai

import logging

class LLM:
    """
    LLM interface with images
    Focused on using gpt4 omni, working on other llms
    """
    def __init__(
            self,
            gpt_model="gpt-4o",
            console_display=None
        ):
        
        self.gpt_model = gpt_model
        self.open_ai_client = openai.OpenAI()
        self.console_display = console_display
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.chat_history = []

    def run(
            self,
            sbframes,
            transcription_text
        ) -> str:
        """
        Send image frames and transcription text to LLM
        """
        
        response_text = ""

        try:
            # Read video frames and convert to base64
            # send to LLM
            if self.console_display:
                self.console_display.add_text(
                    f"[System] Processing {len(sbframes)} frames with transcription\n {transcription_text}")
                    
            user_msg = {
                "role": "user",
                "content": [
                    transcription_text,
                    *map(lambda x: {
                        "image": x,
                        "resize": 768
                    }, sbframes[0::60]),
                ],
            }

            self.chat_history.append(user_msg)
        
            params = {
                "model": self.gpt_model,
                "messages": self.chat_history,
                "temperature": 0.7
            }

            self.logger.info("Calling OpenAI API")
            if self.console_display:
                self.console_display.add_text(
                    f"[System] Calling OpenAI GPT-4o API with image and transcription")
                
            response = self.open_ai_client.chat.completions.create(**params)
            response_text = response.choices[0].message.content
            self.logger.info(f"ai response: {response_text}")

            self.chat_history.append({
                "role": "assistant",
                "content": response_text
            })

            # Log the response to the console
            if self.console_display:
                self.console_display.add_text(f"[AI] {response_text}")

        except Exception as e:
            print(f"Error in transcribing and responding: {e}")
            raise
        
        return response_text
