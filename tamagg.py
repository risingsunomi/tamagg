import tkinter as tk
import tkinter.ttk as ttk
import threading
import mss
import logging
import time
from datetime import datetime

from audio_recorder import AudioRecorder
from transcriber import Transcriber
from console_display import ConsoleDisplay
from screen_recorder import ScreenRecorder
from llm_tts import LLMTTS

# Configure logging
logging.basicConfig(level=logging.DEBUG,
format='[%(name)s] %(asctime)s - %(levelname)s - %(message)s',
handlers=[logging.StreamHandler()])

class Tamagg:
    def __init__(self, root):
        self.root = root
        self.root.title("TAMAGG [ALPHA]")
        self.root.configure(bg='black')
        self.is_recording = False
        self.audio_recorder = AudioRecorder()
        self.transcriber = Transcriber()
        self.transcribed_text = ""
        self.console_display = ConsoleDisplay(root)
        self.screen_recorder = None
        self.llm_tts = LLMTTS()


        # Thread management
        self.audio_rec_thread = None
        self.video_rec_thread = None

        # logging
        self.logger = logging.getLogger(__name__)

        # Start/Stop recording buttons with dark theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', background='green', foreground='white')
        self.style.map('TButton', background=[('active', 'green')], foreground=[('active', 'white')])
        self.style.configure('Green.TButton', background='green', foreground='white')
        self.style.map('Green.TButton', background=[('active', 'darkgreen')], foreground=[('active', 'white')])
        self.style.configure('Red.TButton', background='red', foreground='white')
        self.style.map('Red.TButton', background=[('active', 'red')], foreground=[('active', 'white')])
        self.start_stop_button = ttk.Button(root, text="Start Recording", command=self.toggle_recording, style='Green.TButton')
        self.start_stop_button.grid(row=1, column=0, padx=10, pady=10, sticky="se")
        self.root.bind('<Control-r>', self.toggle_recording)

        # Monitor select dropdown with dark theme
        self.monitor_var = tk.StringVar(value="Monitor 1")
        self.monitor_list = [f"Monitor {i}" for i in range(1, len(mss.mss().monitors))]
        self.monitor_dropdown = ttk.Combobox(root, textvariable=self.monitor_var, values=self.monitor_list)
        self.monitor_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="e")

        # Status label
        self.status_label = tk.Label(root, text="", bg="black", fg="lime")
        self.status_label.grid(row=2, column=0, columnspan=2, sticky="sw", padx=10, pady=10)

        # Make the console display resizable
        self.console_display.text_widget.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)

    def toggle_recording(self, event=None):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        self.is_recording = True
        self.update_status("Recording & Transcribing...")
        self.logger.info("Recording & Transcribing...")

        self.start_stop_button.config(text="Stop Recording", style='Red.TButton')
        
        monitor_number = self.monitor_var.get().split()[-1]
        self.screen_recorder = ScreenRecorder(int(monitor_number))
        self.video_rec_thread = threading.Thread(target=self.screen_recorder.start_recording)
        self.video_rec_thread.start()

        self.audio_rec_thread = threading.Thread(target=self.record_transcribe)
        self.audio_rec_thread.start()

    def stop_recording(self):
        self.is_recording = False
        self.update_status("Stopping Transcribing...")
        self.start_stop_button.config(text="Start Recording", style='Green.TButton')

        if self.audio_rec_thread:
            self.logger.debug("Joining audio_rec_thread")
            self.audio_rec_thread.join()
            self.audio_recorder.stop()
        if self.video_rec_thread:
            self.logger.debug("Joining video_rec_thread")
            self.screen_recorder.stop_recording()
            self.video_rec_thread.join()

        self.update_status("Recording stopped")
        self.logger.info("Recording stopped")

        self.update_status("Interfacing with AI...")
        self.llm_tts.transcribe_and_respond(self.screen_recorder.output_file, self.transcribed_text)
    
    def record_transcribe(self):
        try:
            self.audio_recorder.is_recording = True
            for audio_data in self.audio_recorder.record():
                try:
                    self.transcribed_text = self.transcriber.transcribe(audio_data)
                    if self.transcribed_text.strip():
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        formatted_result = f"[{timestamp}] {self.transcribed_text}"
                        self.logger.debug(f"Transcription: {formatted_result}")
                        self.console_display.add_text(formatted_result)
                        self.update_status("Transcription complete")
                        self.logger.info("Transcription complete. Sending to AI with screen recording.")
                except Exception as e:
                    self.update_status("ERROR during transcription", error=True)
                    self.logger.error(f"Error during transcription: {e}")
        except Exception as e:
            self.logger.error(f"Error during audio recording: {e}")

    def update_status(self, message, error=False):
        if error:
            self.status_label.config(fg="red", text=message)
        else:
            self.status_label.config(fg="lime", text=message)

if __name__ == "__main__":
    root = tk.Tk()
    app = Tamagg(root)
    root.mainloop()
