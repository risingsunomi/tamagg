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
        
        self.transcriber = Transcriber()
        self.console_display = ConsoleDisplay(self.root)
        self.screen_recorder = None
        self.allow_screen_recording = True
        self.llm = LLM(console_display=self.console_display)
        self.tts = TTS(console_display=self.console_display)
        self.tts_thread = None
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

        self.style.configure(
            'TButton', 
            background='green', 
            foreground='white', 
            font=("Consolas", 10)
        )
        self.style.map(
            'TButton', 
            background=[('active', 'green')], 
            foreground=[('active', 'white')])
        
        self.style.configure(
            'Green.TButton', 
            background='green', 
            foreground='white',
            font=("Consolas", 10)
        )
        self.style.map(
            'Green.TButton', 
            background=[('active', 'darkgreen')], 
            foreground=[('active', 'white')]
        )
        
        self.style.configure(
            'Red.TButton', 
            background='red', 
            foreground='white',
            font=("Consolas", 10)
        )
        self.style.map(
            'Red.TButton', 
            background=[('active', 'red')], 
            foreground=[('active', 'white')]
        )
        
        self.style.configure(
            'Gray.TButton', 
            background='gray', 
            foreground='white',
            font=("Consolas", 10)
        )
        self.style.map(
            'Gray.TButton', 
            background=[('active', 'gray')], 
            foreground=[('active', 'white')]
        )
        
        
        self.start_stop_button = ttk.Button(
            self.root, 
            text="Start Recording", 
            command=self.toggle_recording, 
            style='Green.TButton'
        )
        self.start_stop_button.grid(row=1, column=0, padx=10, pady=10, sticky="se")
        self.root.bind('<Control-r>', self.toggle_recording)

        # Monitor select dropdown with dark theme
        self.monitor_var = tk.StringVar(value="All Monitors -1")
        self.monitor_list = [f"Monitor {i}" for i in range(1, len(mss.mss().monitors))]
        self.monitor_list = ["All Monitors -1"] + self.monitor_list
        self.monitor_dropdown = ttk.Combobox(
            self.root, 
            textvariable=self.monitor_var, 
            values=self.monitor_list
        )
        self.monitor_dropdown.grid(row=2, column=2, padx=10, pady=10, sticky="e")
        self.monitor_dropdown.configure(
            font=("Consolas", 10)
        )

        # Status label
        self.status_label = tk.Label(
            self.root, 
            text="", 
            bg="black", 
            fg="lime"
        )
        self.status_label.grid(
            row=2, column=0, columnspan=2, sticky="sw", padx=10, pady=10)

        # Make the console display resizable
        self.console_display.text_widget.grid(
            row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)
        self.root.grid_columnconfigure(2, weight=0)

        # Microphone select dropdown
        self.microphone_var = tk.StringVar()
        self.microphone_list = self.get_microphone_list()
        self.microphone_var.set(self.microphone_list[0])
        self.microphone_dropdown = ttk.Combobox(
            self.root, 
            textvariable=self.microphone_var, 
            values=self.microphone_list
        )
        self.microphone_dropdown.grid(
            row=1, column=2, padx=10, pady=10, sticky="e")
        self.microphone_dropdown.bind(
            "<<ComboboxSelected>>", self.select_microphone)

        # enable/disable screen recording
        self.screen_record_var = tk.IntVar(value=True)
        self.screen_record_checkbox = tk.Checkbutton(
            self.root, 
            text='Allow Screen Recording', 
            variable=self.screen_record_var,
            command=self.toggle_screen_recording)
        self.screen_record_checkbox.grid(
            row=1, column=1, columnspan=1, padx=10, pady=10, sticky="sw")

        # File menu
        menubar = tk.Menu(self.root)
        menubar.configure(bg="black", fg="lime")
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Quit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=file_menu)

        # Configure the root window to display the menubar
        self.root.config(menu=menubar)

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

    def handle_menu_selection(self, event):
        selected_option = self.menu_var.get()
        if selected_option == "Quit":    
            self.logger.info("Quitting application")
            self.on_closing()

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def toggle_screen_recording(self):
        self.allow_screen_recording = bool(self.screen_record_var.get())
    
    def start_recording(self):
        self.update_status("Recording & Transcribing...")
        self.logger.info("Recording & Transcribing...")
        self.is_recording = True

        # stop any audio
        self.logger.info("Stopping TTS if any")
        if self.tts.is_playing:
            self.tts.stop_audio()

        # record monitor
        if self.allow_screen_recording:
            # get monitor selection and start
            monitor_number = int(self.monitor_var.get().split()[-1])
            
            if monitor_number > 0:
                self.console_display.add_text(
                    f"[System] Screen Recording Started on Monitor {monitor_number}",
                    "system"
                )
            else:
                self.console_display.add_text(
                    f"[System] Screen Recording Started on all monitors",
                    "system"
                )

            self.logger.info("Starting screen recording thread")

            self.screen_recorder = ScreenRecorder(monitor_number)
            self.video_rec_thread = threading.Thread(
                target=self.screen_recorder.start_recording)
            self.video_rec_thread.start()
        
        # start mic and record for transcribe
        self.console_display.add_text(
            "[System] Audio and Transcribing Started",
            "system"
        )
        self.logger.info("Starting record_transcribe thread")

        self.audio_rec_thread = threading.Thread(
            target=self.transcriber.record_transcribe)
        self.audio_rec_thread.start()

        self.start_stop_button.config(text="Stop Recording", style='Red.TButton')
        
    def stop_recording(self):
        self.update_status("Stopping Recording & Transcribing...")
        self.logger.info("Stopping Recording & Transcribing...")
        self.console_display.add_text("[System] Stopping recordings...")

        self.logger.info("Changing to Processing button...")        
        self.start_stop_button.config(text="Processing...", style='Gray.TButton')
        self.start_stop_button.config(state='disabled')

        processing_thread = threading.Thread(target=self._process_stop_recording)
        processing_thread.start()

    def _process_stop_recording(self):
        if self.tts.is_playing:
            self.tts.stop_audio()

        self.is_recording = False

        if self.allow_screen_recording:
            
            self.logger.info("self.screen_recorder.stop_recording()")
            self.screen_recorder.stop_recording()
            self.logger.info("self.video_rec_thread.join()")
            self.video_rec_thread.join(timeout=10)

            self.console_display.add_text(
                f"[System] Screen Recording Stopped\n{len(self.screen_recorder.frames)} frames captured",
                "system"
            )

        self.logger.info("self.audio_rec_thread.join()")
        self.transcriber.audio_recorder.stop()
        self.audio_rec_thread.join()

        self.console_display.add_text(
            "[System] Audio and Transcribing Stopped",
            "system"
        )
        self.update_status("Recording stopped")
        self.logger.info("Recording stopped")

        self.console_display.add_text(f"[User] {self.transcriber.transcribed_text}")
        self.ai_thread = threading.Thread(target=self.process_ai_assistant)
        self.ai_thread.start()

        # Update the UI in the main thread
        self.start_stop_button.after(0, self._update_button_to_start)

    def _update_button_to_start(self):
        self.logger.info("Changing to Start button...")
        self.start_stop_button.config(text="Start Recording", style='Green.TButton')
        self.start_stop_button.config(state='normal')

    def process_ai_assistant(self):
        self.console_display.add_text("[System] Interfacing with AI...", "system")
        self.logger.info("processing ai assistant")
        self.logger.info(f"transcription_text: {self.transcriber.transcribed_text}")
        try:
            if not self.allow_screen_recording:
                resp = self.llm.run(
                    sbframes=None,
                    transcription_text=self.transcriber.transcribed_text
                )
            else:
                # resp = self.llm.run(
                #     sbframes=self.screen_recorder.get_frames(),
                #     transcription_text=self.transcriber.transcribed_text
                # )

                resp = self.llm.run(
                    sbframes=self.screen_recorder.frames,
                    transcription_text=self.transcriber.transcribed_text
                )
            
            # clear frames and text
            self.transcriber.transcribed_text = ""
            self.screen_recorder.frames = []

            if resp:
                self.tts_thread = threading.Thread(
                    target=self.tts.run_speech, args=(resp,)
                )
                self.tts_thread.start()
                self.tts_thread.join()

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
            self.tts.stop_audio()

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
