import cv2  # OpenCV for reading video
import base64
import os
import requests
import openai
import playsound
import logging
from datetime import datetime

class LLMTTS:
    def __init__(
            self,
            gpt_model="gpt-4o",
            tts_model="tts-1-1106",
            console_display=None
        ):
        
        self.gpt_model = gpt_model
        self.tts_model = tts_model
        self.open_ai_client = openai.OpenAI()
        self.console_display = console_display
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.chat_history = []

    def transcribe_and_respond(
            self,
            sbframes,
            transcription_text
        ) -> str:
        
        response_text = ""

        try:
            # Read video frames and convert to base64
            if len(sbframes) > 0 and transcription_text:
                if self.console_display:
                    self.console_display.add_text(
                        f"[System] Processing {len(sbframes)} frames with transcription\n {transcription_text}")
                    
                self.logger.info(f"Grabbed {len(sbframes)} frames")

                # prompt
                system_msg = {
                    "role": "system",
                    "content": f"Transcription with {len(sbframes)} base64 images"
                }

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
            elif transcription_text:
                self.logger.info("No frames found")

                # prompt
                system_msg = {
                    "role": "system",
                    "content": "Transcription only"
                }

                user_msg = {
                    "role": "user",
                    "content": transcription_text,
                }

            self.chat_history.append(system_msg)
            self.chat_history.append(user_msg)
        
            params = {
                "model": self.gpt_model,
                "messages": self.chat_history,
                "temperature": 0.7
            }

            self.logger.info("Calling OpenAI API")
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

            # Use TTS to get the audio response
            tts_response = requests.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                },
                json={
                    "model": self.tts_model,
                    "input": response_text,
                    "voice": "nova",
                },
            )

            # Collect the audio response
            audio = b""
            for chunk in tts_response.iter_content(chunk_size=1024 * 1024):
                audio += chunk

            # Play the audio response
            nn = datetime.now().strftime('%Y%M%d_%h%m%s')
            audio_fname = f"airesp{nn}.mp3"
            audio_path = f"{self.root_dir}/data/{audio_fname}"
            with open(audio_path, "wb") as audio_file:
                audio_file.write(audio)
            
            playsound.playsound(audio_path)

            # Remove the audio file after playing
            os.remove(audio_path)
        except Exception as e:
            print(f"Error in transcribing and responding: {e}")
            raise
        
        return response_text
