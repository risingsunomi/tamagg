import os
import openai
import logging
import json

from llm_functions import LLMFunctions
# from oai_ict import OpenAIImageCoordinateTranslator

class LLM:
    """
    LLM interface with images
    Focused on using gpt4 omni, working on other llms
    """
    def __init__(
            self,
            gpt_model="gpt-4o",
            llm_provider="openai",
            console_display=None
        ):
        
        self.gpt_model = gpt_model
        self.llm_provider = llm_provider
        self.open_ai_client = openai.OpenAI()
        self.console_display = console_display
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.chat_history = []
        self.llm_temp = 1.0

        # functions
        self.llmfunc = LLMFunctions(console_display=self.console_display)

        self.initial_prompt = """
        You are Layla a professional, talented, assistant for User. Your work is mostly assistance and task management. If asked to do a task, lets think through the task step by step with short form thoughts. For tasks, remeber to use the functions provided to do actions as needed.

        User: 
        """


    def run(
            self,
            frames_hw,
            sbframes,
            transcription_text
        ) -> str:
        """
        Send image frames and transcription text to LLM
        """
        
        func_resp = ""
        response_text = ""

        try:
            # Read video frames and convert to base64
            # send to LLM
            if sbframes:
                self.logger.info(f"Processing {len(sbframes)} frames with transcription, \"{transcription_text}\"")
                self.logger.info(f"{frames_hw}")
                if self.console_display:
                    self.console_display.add_text(
                        f"Processing {len(sbframes)} frames with transcription, \"{transcription_text}\"")
                
                # get scaled dimensions
                # oai_ict = OpenAIImageCoordinateTranslator(
                #     original_width=frames_wh[0],
                #     original_height=frames_wh[1]
                # )
                # scaled_width, scaled_height = oai_ict.calculate_resized_dimensions()
                # # add info about original frame width and height
                # transcription_text += f"""
                #     \n The frames were originally recorded with dimensions {frames_wh} but are scaled down to ({scaled_width},{scaled_height}). Make sure to scale up for x, y coordinates when using the mouse action. For example the scaling factor in original is (1080,3840) and scaled down to (768, 2730), scaling up the x factor is approx 1.4066 and the y is approx 1.40625
                # """
                user_msg = {
                    "role": "user",
                    "content": [
                        self.initial_prompt + transcription_text,
                        *map(lambda x: {
                            "image": x,
                            "resize": frames_hw[1]
                        }, sbframes[0::60]),
                    ]
                }

                # del oai_ict
            else:
                if self.console_display:
                    self.console_display.add_text(
                        f"Processing transcription, \"{transcription_text}\"")
                self.logger.info(f"Processing only transcription, \"{transcription_text}\"")
                user_msg = {
                    "role": "user",
                    "content": self.initial_prompt + transcription_text,
                }

            self.chat_history.append(user_msg)
        
            params = {
                "model": self.gpt_model,
                "messages": self.chat_history,
                "temperature": self.llm_temp,
                "functions": self.llmfunc.functions,
                "function_call": self.llmfunc.function_call
            }

            self.logger.info("Calling OpenAI API")
            if self.console_display:
                self.console_display.add_text(
                    f"Calling OpenAI GPT-4o API with image and transcription")
                
            response = self.open_ai_client.chat.completions.create(**params)
            response_choice = response.choices[0]

            self.logger.info(f"choices: {response.choices}\n")
            self.logger.info(f"response_choice: {response_choice}\n")

            if response_choice.message.content:
                response_text = response_choice.message.content
                self.logger.info(f"ai response: {response_text}")

                self.chat_history.append({
                    "role": "assistant",
                    "content": response_text 
                })

                # Log the response to the console
                if self.console_display:
                    self.console_display.add_text(f"{response_text}", ftype="ai")

            # handle functions
            
            if response_choice.message.function_call:
                fcall = response_choice.message.function_call
                fname = fcall.name
                fargs = json.loads(fcall.arguments)
                self.logger.info(f"LLM called function '{fcall.name}'")
                if frames_hw:
                    self.llmfunc.image_width = frames_hw[0]
                    self.llmfunc.image_height = frames_hw[1]

                func_resp = self.llmfunc.handle_call(fname, fargs)

                self.chat_history.append({
                    "role": "assistant",
                    "content": '; '.join(func_resp)
                })

            

        except Exception as e:
            print(f"Error in transcribing and responding: {e}")
            raise
        
        return response_text
