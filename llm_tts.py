import cv2  # OpenCV for reading video
import base64
import os
import requests
import openai
import playsound

class LLMTTS:
    def __init__(self, gpt_model="gpt-4", tts_model="tts-1-1106", console_display=None):
        self.gpt_model = gpt_model
        self.tts_model = tts_model
        self.console_display = console_display

    def transcribe_and_respond(self, video_path, transcription_text):
        try:
            # Read video frames and convert to base64
            video = cv2.VideoCapture(video_path)
            base64_frames = []
            while video.isOpened():
                success, frame = video.read()
                if not success:
                    break
                _, buffer = cv2.imencode(".jpg", frame)
                base64_frames.append(base64.b64encode(buffer).decode("utf-8"))
            video.release()

            # Prepare the GPT-4 prompt
            prompt_messages = [
                {
                    "role": "user",
                    "content": [
                        "These are frames from a video. Generate a compelling response based on the transcription text provided.",
                        {"transcription_text": transcription_text},
                        *map(lambda x: {"image": x, "resize": 768}, base64_frames[0::60]),
                    ],
                },
            ]
            params = {
                "model": self.gpt_model,
                "messages": prompt_messages,
                "max_tokens": 200,
            }

            # Call OpenAI API
            response = openai.ChatCompletion.create(**params)
            response_text = response.choices[0].message.content

            # Log the response to the console
            if self.console_display:
                self.console_display.add_text(f"AI Response: {response_text}")

            # Use TTS to get the audio response
            tts_response = requests.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                },
                json={
                    "model": self.tts_model,
                    "input": response_text,
                    "voice": "onyx",
                },
            )

            # Collect the audio response
            audio = b""
            for chunk in tts_response.iter_content(chunk_size=1024 * 1024):
                audio += chunk

            # Play the audio response
            audio_path = "response_audio.mp3"
            with open(audio_path, "wb") as audio_file:
                audio_file.write(audio)
            
            playsound.playsound(audio_path)

            # Remove the audio file after playing
            os.remove(audio_path)

            return response_text
        except Exception as e:
            print(f"Error in transcribing and responding: {e}")
            return None
