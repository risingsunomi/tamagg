import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import threading
import speech_recognition as sr
from audio_recorder import AudioRecorder
from transcriber import Transcriber
from console_display import ConsoleDisplay

class AudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Recorder and Transcriber")
        self.is_recording = False
        self.audio_recorder = AudioRecorder()
        self.transcriber = Transcriber()
        self.console_display = ConsoleDisplay(root)

        self.style = ttk.Style()
        self.style.configure('TButton', background='green', foreground='white')
        self.style.map('TButton', background=[('active', 'green')], foreground=[('active', 'white')])

        self.start_stop_button = ttk.Button(root, text="Start Recording", command=self.toggle_recording, style='TButton')
        self.start_stop_button.pack(pady=20)

        self.root.bind('<Control-r>', self.toggle_recording)

    def toggle_recording(self, event=None):
        if self.is_recording:
            self.is_recording = False
            self.start_stop_button.config(text="Start Recording")
            self.style.configure('TButton', background='green', foreground='white')
        else:
            self.is_recording = True
            self.start_stop_button.config(text="Stop Recording")
            self.style.configure('TButton', background='red', foreground='white')
            threading.Thread(target=self.record_audio).start()

    def record_audio(self):
        audio_data_list = []
        for audio_data in self.audio_recorder.record():
            audio_data_list.append(audio_data)
            if not self.is_recording:
                break

        self.transcribe_audio(audio_data_list)

    def transcribe_audio(self, audio_data_list):
        for audio_data in audio_data_list:
            try:
                result = self.transcriber.transcribe(audio_data)
                if result.strip():
                    print(f"Transcription: {result}")
                    self.console_display.add_text(result)
            except Exception as e:
                print(f"Error during transcription: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()
