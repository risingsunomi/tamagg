import requests
import logging
import os
from datetime import datetime
import wave
import pyaudio
import threading
import time

class TTS:
    """
    Text to speech interface
    Current using Openai, will expand
    """
    def __init__(
            self,
            tts_model="tts-1-1106",
            console_display=None
        ):
        
        self.tts_model = tts_model
        self.console_display = console_display
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.playback_thread = None
        self.stop_event = threading.Event()

    def run_speech(self, response_text):
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

        # Save the audio response
        nn = datetime.now().strftime('%Y%M%d_%H%M%S')
        audio_fname = f"airesp{nn}.wav"
        audio_path = f"{self.root_dir}/data/{audio_fname}"
        with open(audio_path, "wb") as audio_file:
            audio_file.write(audio)
        
        # Play the audio response
        self.playback_thread = threading.Thread(target=self.play_audio, args=(audio_path,))
        self.playback_thread.start()

    def play_audio(self, audio_path):
        wf = wave.open(audio_path, 'rb')
        p = pyaudio.PyAudio()

        def callback(in_data, frame_count, time_info, status):
            if self.stop_event.is_set():
                return (None, pyaudio.paComplete)
            data = wf.readframes(frame_count)
            return (data, pyaudio.paContinue)

        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        stream_callback=callback)

        stream.start_stream()

        while stream.is_active():
            if self.stop_event.is_set():
                break
            time.sleep(0.1)

        stream.stop_stream()
        stream.close()
        wf.close()
        p.terminate()

        os.remove(audio_path)

    def stop_speech(self):
        if self.playback_thread and self.playback_thread.is_alive():
            self.stop_event.set()
            self.playback_thread.join()
            self.stop_event.clear()
