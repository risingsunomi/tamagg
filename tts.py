import logging
import os
from datetime import datetime
import threading
import openai
from pydub import AudioSegment
from pydub.playback import play

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
        self.playback_thread = None
        self.is_playing = False
        self.audio = None
        self.audio_path = None

    def run_speech(self, response_text):
        if self.tts_provider == "openai":
            try:
                self.run_openai(response_text)
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
        # self.playback_thread = threading.Thread(target=self.play_audio, args=(audio_path,))
        # self.playback_thread.start()

    def run_openai(self, response_text):
        client = openai.OpenAI()
        nn = datetime.now().strftime('%Y%M%d_%H%M%S')
        audio_fname = f"airesp{nn}.mp3"
        self.audio_path = f"{self.root_dir}/data/{audio_fname}"

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

    def play_audio(self):
        """
        Play audio from TTS interface
        """
        audio = AudioSegment.from_mp3(self.audio_path)
        # play(audio)
        
        self.playback_thread = threading.Thread(
            target=play,
            args=(audio,)
        )
        
        self.playback_thread.start()

    def stop_audio(self):
        self.logger.info("Stopping audio...")
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join()
            self.logger.info(f"removing {self.audio_path}")
            # os.remove(self.audio_path)

    # def play_audio(self, audio_path):
    #     # Load the mp3 file
    #     self.audio = AudioSegment.from_mp3(audio_path)
    #     self.audio.play()
    #     chunk_size = 1024
    #     chunks = make_chunks(audio, chunk_size)

    #     p = pyaudio.PyAudio()
    #     chunk_iter = iter(chunks)

    #     def callback(in_data, frame_count, time_info, status):
    #         if self.stop_event.is_set():
    #             return (None, pyaudio.paComplete)
    #         try:
    #             chunk = next(chunk_iter)
    #         except StopIteration:
    #             return (None, pyaudio.paComplete)
    #         return (chunk._data, pyaudio.paContinue)

    #     stream = p.open(format=p.get_format_from_width(audio.sample_width),
    #                     channels=audio.channels,
    #                     rate=audio.frame_rate,
    #                     output=True,
    #                     stream_callback=callback)

    #     stream.start_stream()
    #     self.is_playing = True

    #     while stream.is_active():
    #         if self.stop_event.is_set():
    #             break
    #         time.sleep(0.1)

    #     stream.stop_stream()
    #     stream.close()
    #     p.terminate()

    #     # os.remove(audio_path)
    #     self.is_playing = False

    # def stop_speech(self):
    #     if self.playback_thread and self.playback_thread.is_alive():
    #         self.is_playing = False
    #         
    #         self.playback_thread.join()
    #         