import os
import openai
import logging
import json

from llm_functions import LLMFunctions

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

        # functions
        self.llmfunc = LLMFunctions(console_display=self.console_display)


    def run(
            self,
            frames_wh,
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
            if sbframes:
                self.logger.info(f"[System] Processing {len(sbframes)} frames with transcription, \"{transcription_text}\"")
                if self.console_display:
                    self.console_display.add_text(
                        f"[System] Processing {len(sbframes)} frames with transcription, \"{transcription_text}\"")
                
                user_msg = {
                    "role": "user",
                    "content": [
                        transcription_text,
                        *map(lambda x: {
                            "image": x,
                            "resize": 768
                        }, sbframes[0::60]),
                    ]
                }
            else:
                if self.console_display:
                    self.console_display.add_text(
                        f"[System] Processing transcription, \"{transcription_text}\"")
                self.logger.info(f"[System] Processing only transcription, \"{transcription_text}\"")
                user_msg = {
                    "role": "user",
                    "content": transcription_text
                }

            self.chat_history.append(user_msg)
        
            params = {
                "model": self.gpt_model,
                "messages": self.chat_history,
                "temperature": 0.7,
                "functions": self.llmfunc.functions,
                "function_call": self.llmfunc.function_call
            }

            self.logger.info("Calling OpenAI API")
            if self.console_display:
                self.console_display.add_text(
                    f"[System] Calling OpenAI GPT-4o API with image and transcription")
                
            response = self.open_ai_client.chat.completions.create(**params)

            self.logger.info(f"===choices===\n{response.choices}\n{response.choices[0]}")

            # handle functions
            response_choice = response.choices[0]
            if response_choice.message.function_call:
                fcall = response_choice.message.function_call
                fname = fcall.name
                fargs = json.loads(fcall.arguments)
                self.logger.info(f"LLM called function '{fcall.name}'")
                if frames_wh:
                    self.llmfunc.image_width = frames_wh[0]
                    self.llmfunc.image_height = frames_wh[1]

                self.llmfunc.handle_call(fname, fargs)
            else:
                response_text = response_choice.message.content
                self.logger.info(f"ai response: {response_text}")

                self.chat_history.append({
                    "role": "assistant",
                    "content": response_text
                })

                # Log the response to the console
                if self.console_display:
                    self.console_display.add_text(f"[Assistant] {response_text}", ftype="ai")

        except Exception as e:
            print(f"Error in transcribing and responding: {e}")
            raise
        
        return response_text
