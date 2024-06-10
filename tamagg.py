import tkinter as tk
import tkinter.ttk as ttk
import threading
import mss
import logging
import time
import pyaudio
import os
from dotenv import load_dotenv
from playsound import _playsoundWin

from audio_recorder import AudioRecorder
from transcriber import Transcriber
from console_display import ConsoleDisplay
from screen_recorder import ScreenRecorder
from llm import LLM
from tts import TTS

# Configure logging
logging.basicConfig(level=logging.INFO,
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
        self.llm = LLM(console_display=self.console_display)
        self.tts = TTS(console_display=self.console_display)
        self.microphone_index = None


        # Thread management
        self.audio_rec_thread = None
        self.video_rec_thread = None
        self.ai_thread = None

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
        
        self.style.configure('Gray.TButton', background='gray', foreground='white')
        self.style.map('Gray.TButton', background=[('active', 'gray')], foreground=[('active', 'white')])
        
        
        self.start_stop_button = ttk.Button(root, text="Start Recording", command=self.toggle_recording, style='Green.TButton')
        self.start_stop_button.grid(row=1, column=0, padx=10, pady=10, sticky="se")
        self.root.bind('<Control-r>', self.toggle_recording)

        # Monitor select dropdown with dark theme
        self.monitor_var = tk.StringVar(value="Monitor 1")
        self.monitor_list = [f"Monitor {i}" for i in range(1, len(mss.mss().monitors))]
        self.monitor_dropdown = ttk.Combobox(root, textvariable=self.monitor_var, values=self.monitor_list)
        self.monitor_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="e")

        # Status label
        self.status_label = tk.Label(root, text="", bg="black", fg="lime")
        self.status_label.grid(row=2, column=0, columnspan=2, sticky="sw", padx=10, pady=10)

        # Make the console display resizable
        self.console_display.text_widget.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)
        self.root.grid_columnconfigure(2, weight=0)

        # Microphone select dropdown
        self.microphone_var = tk.StringVar()
        self.microphone_list = self.get_microphone_list()
        self.microphone_var.set(self.microphone_list[0])
        self.microphone_dropdown = ttk.Combobox(root, textvariable=self.microphone_var, values=self.microphone_list)
        self.microphone_dropdown.grid(row=1, column=2, padx=10, pady=10, sticky="e")
        self.microphone_dropdown.bind("<<ComboboxSelected>>", self.select_microphone)
    
    def get_microphone_list(self):
        p = pyaudio.PyAudio()
        mic_list = []
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                mic_list.append(f"{i}: {device_info['name']}")
        return mic_list

    def select_microphone(self, event):
        selected_mic = self.microphone_var.get()
        self.microphone_index = int(selected_mic.split(":")[0])
        print(f"Selected microphone index: {self.microphone_index}")

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        self.update_status("Recording & Transcribing...")
        self.logger.info("Recording & Transcribing...")
        self.is_recording = True

        # stop any audio
        self.tts.stop_speech()

        monitor_number = self.monitor_var.get().split()[-1]
        self.screen_recorder = ScreenRecorder(int(monitor_number))
        self.video_rec_thread = threading.Thread(target=self.screen_recorder.start_recording)
        self.video_rec_thread.start()

        self.audio_rec_thread = threading.Thread(target=self.record_transcribe)
        self.audio_rec_thread.start()

        time.sleep(1)
        
        self.start_stop_button.config(text="Stop Recording", style='Red.TButton')
        

    def stop_recording(self):
        self.update_status("Stopping Recording & Transcribing...")
        self.logger.info("Stopping Recording & Transcribing...")
        
        self.is_recording = False

        self.logger.info("Changing to Start button...")
        self.start_stop_button.config(text="Processing...", style='Gray.TButton')
        self.start_stop_button.config(state='disabled')

        self.logger.info("self.audio_recorder.stop()")
        self.audio_recorder.stop()
        self.logger.info("self.screen_recorder.stop_recording()")
        self.screen_recorder.stop_recording()
        
        self.logger.info("self.audio_rec_thread.join()")
        self.audio_rec_thread.join(timeout=5)
        self.logger.info("self.video_rec_thread.join()")
        self.video_rec_thread.join()

        self.update_status("Recording stopped")
        self.logger.info("Recording stopped")

        self.start_stop_button.config(text="Start Recording", style='Green.TButton')
        self.start_stop_button.config(state='normal')

        self.console_display.add_text(f"[User] {self.transcribed_text}")
        self.ai_thread = threading.Thread(target=self.process_ai_assistant)
        self.ai_thread.start()
        self.ai_thread.join(timeout=0.1)
        
        self.transcribed_text = ""

    def record_transcribe(self):
        try:
            for audio_data in self.audio_recorder.record():
                if self.is_recording:
                    try:
                        tresp = self.transcriber.transcribe(audio_data)
                        if tresp.strip():
                            self.transcribed_text += tresp
                            self.logger.info(f"{self.transcribed_text}")
                    except Exception as e:
                        self.update_status("ERROR during transcription", error=True)
                        self.logger.error(f"Error during transcription: {e}")
                        break
                else:
                    break
        except Exception as e:
            self.logger.error(f"Error during audio recording: {e}")
        finally:
            self.audio_recorder.stop()

    def process_ai_assistant(self):
        self.console_display.add_text("[System] Interfacing with AI...")
        self.logger.info("processing ai assistant")
        try:
            resp = self.llm.run(
                self.screen_recorder.get_frames(),
                self.transcribed_text
            )

            if resp:
                self.tts.run_speech(resp)

            self.logger.info("done processing")
        except Exception as err:
            self.update_status("Error with LLM! Please retry...", error=True)
            self.console_display.add_text("[System] Error with LLM! Please try again...")
            self.logger.error(err)

    def update_status(self, message, error=False):
        if error:
            self.status_label.config(fg="red", text=message)
        else:
            self.status_label.config(fg="lime", text=message)

    def on_closing(self):
        if self.tts.is_playing:
            self.tts.stop_speech()

        if self.screen_recorder:
            self.screen_recorder.nvjpeg.cleanup_nvjpeg()
            os.remove(self.screen_recorder.sqldb)
        
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    load_dotenv()
    root = tk.Tk()
    app = Tamagg(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
