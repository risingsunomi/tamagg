import logging
import os
from datetime import datetime
import openai
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
from pathlib import Path
from elevenlabs.client import ElevenLabs

class TTS:
    """
    Text to speech interface
    Current using Openai, will expand
    """
    def __init__(
            self,
            tts_model="tts-1-1106",
            tts_provider="openai",
            console_display=None
        ):
        
        self.tts_model = tts_model
        self.tts_provider = tts_provider
        self.console_display = console_display
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.playback_process = None
        self.is_playing = False
        self.audio = None
        self.audio_path = None
        self.playback = None

        # check for data dir and if none, create
        folder = Path(f"{self.root_dir}/data/")
        if not folder.exists():
            try:
                folder.mkdir(parents=True, exist_ok=True)  # Create parent directories if needed
                print(f"Folder created: {folder}")
            except OSError as e:
                print(f"Error creating folder: {e}")

    def run_speech(self, response_text):
        if self.is_playing:
            self.stop_audio()
            
        if self.tts_provider == "openai":
            try:
                self.run_openai(response_text)
            except Exception as err:
                self.logger.error(f"run_speech failed: {err}")
                raise
        elif self.tts_provider == "elevenlab":
            try:
                self.run_elevenlabs(response_text)
            except Exception as err:
                self.logger.error(f"run_speech failed: {err}")
                raise

        # # Use TTS to get the audio response
        # tts_response = requests.post(
        #     "https://api.openai.com/v1/audio/speech",
        #     headers={
        #         "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        #     },
        #     json={
        #         "model": self.tts_model,
        #         "input": response_text,
        #         "voice": "nova",
        #     },
        # )

        # # Collect the audio response
        # audio = b""
        # for chunk in tts_response.iter_content(chunk_size=1024 * 1024):
        #     audio += chunk

        # # Save the audio response
        # nn = datetime.now().strftime('%Y%M%d_%H%M%S')
        # audio_fname = f"airesp{nn}.wav"
        # audio_path = f"{self.root_dir}/data/{audio_fname}"
        # with open(audio_path, "wb") as audio_file:
        #     audio_file.write(audio)
        
        # # Play the audio response
        # self.playback_process = threading.Thread(target=self.play_audio, args=(audio_path,))
        # self.playback_process.start()

    def run_openai(self, response_text):
        client = openai.OpenAI()
        nn = datetime.now().strftime('%Y%M%d_%H%M%S')
        audio_fname = f"oai_airesp{nn}.mp3"
        self.audio_path = Path(f"{self.root_dir}/data/{audio_fname}")

        try:
            with client.audio.speech.with_streaming_response.create(
                model=self.tts_model,
                voice="nova",
                input=response_text
            ) as tts_oai:
                tts_oai.stream_to_file(self.audio_path)
        except Exception as err:
            self.logger.error(f"run_openai tts failed: {err}")
            raise
        finally:
            # Play the audio response
            self.play_audio()

    def run_elevenlabs(self, response_text):
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        nn = datetime.now().strftime('%Y%M%d_%H%M%S')
        audio_fname = f"11_airesp{nn}.mp3"
        self.audio_path = Path(f"{self.root_dir}/data/{audio_fname}")

        try:
            audio = client.generate(
                text=response_text,
                voice="Rachel",
                model="eleven_multilingual_v2",
                stream=True
            )

            with open(self.audio_path, "wb") as out_file:
                for bchunk in audio:
                    if bchunk is not None:
                        out_file.write(bchunk)

        except Exception as err:
            self.logger.error(f"elevenlabs failed: {err}")
            raise
        finally:
            # Play the audio response
            self.play_audio()

    def play_audio(self):
        """
        Play audio from TTS interface
        """
        self.is_playing = True
        try:
            self.audio = AudioSegment.from_mp3(self.audio_path)
            self.playback = _play_with_simpleaudio(self.audio)
        except Exception as err:
            self.logger.error(f"play_audio failed: {err}")
            self.is_playing = False

    def stop_audio(self):
        self.logger.info(f"Stopping audio... {self.is_playing} {self.playback}")
        if self.is_playing:
            self.is_playing = False
            self.playback.stop()
            self.logger.info(f"removing {self.audio_path}")
            
            try:
                os.remove(self.audio_path)
            except Exception as err:
                self.logger.error(f"Removing {self.audio_path} failed: {err}")
            