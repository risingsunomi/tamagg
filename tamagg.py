import tkinter as tk
import tkinter.ttk as ttk
import threading
import mss
import logging
import time
import pyaudio

from dotenv import load_dotenv
import cv2
import platform

from transcriber import Transcriber
from console_display import ConsoleDisplay
from screen_recorder import ScreenRecorder
from cam_recorder import CamRecorder
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
        self.root.configure(bg='#2b2b2b')
        self.transcriber = Transcriber()
        self.console_display = ConsoleDisplay(self.root)
        self.llm = LLM(console_display=self.console_display)
        self.tts = None

        self.screen_recorder = None
        self.cam_recorder = None
        self.tts_thread = None
        self.microphone_index = None
        self.monitor_number = 0
        self.webcam_index = 0
        self.screen_record_allow = 0
        self.voice_assistant_allow = 0
        self.tts_provider = "openai"
        self.convo_mode_allow = False

        self.is_recording = False
        self.allow_screen_recording = True
        self.enable_assistant_voice = True
        self.use_webcam = False

        # Agent management
        self.is_agent = False
        self.agent_loop = 1

        # Thread management
        self.audio_rec_thread = None
        self.video_rec_thread = None
        self.ai_thread = None

        # Logging
        self.logger = logging.getLogger(__name__)

        # Start/Stop recording buttons with dark theme
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # --------------------------
        # Styling
        # --------------------------
        self.style.configure(
            'TButton', 
            background='#3a6ea5',  # Slate Blue
            foreground='white', 
            font=("Helvetica", 10)
        )
        self.style.map(
            'TButton', 
            background=[('active', '#2a5d84')],  # Darker Slate Blue on Active
            foreground=[('active', 'white')]
        )

        self.style.configure(
            'Primary.TButton', 
            background='#3a6ea5',  # Slate Blue
            foreground='white',
            font=("Helvetica", 10)
        )
        self.style.map(
            'Primary.TButton', 
            background=[('active', '#2a5d84')],  # Darker Slate Blue on Active
            foreground=[('active', 'white')]
        )

        self.style.configure(
            'Success.TButton', 
            background='#28a745',  # Green
            foreground='white',
            font=("Helvetica", 10)
        )
        self.style.map(
            'Success.TButton', 
            background=[('active', '#218838')],  # Darker Green on Active
            foreground=[('active', 'white')]
        )

        self.style.configure(
            'Danger.TButton', 
            background='#dc3545',  # Red
            foreground='white',
            font=("Helvetica", 10)
        )
        self.style.map(
            'Danger.TButton', 
            background=[('active', '#c82333')],  # Darker Red on Active
            foreground=[('active', 'white')]
        )

        self.style.configure(
            'Secondary.TButton', 
            background='#6c757d',  # Gray
            foreground='white',
            font=("Helvetica", 10)
        )
        self.style.map(
            'Secondary.TButton', 
            background=[('active', '#5a6268')],  # Darker Gray on Active
            foreground=[('active', 'white')]
        )

        # --------------------------
        # Buttons
        # --------------------------

        # Start/Stop button
        self.start_stop_button = ttk.Button(
            self.root, 
            text="Record", 
            command=self.toggle_recording, 
            style='Success.TButton'
        )
        self.start_stop_button.grid(row=1, column=0, padx=10, pady=10, sticky="s")
        self.root.bind('<Control-r>', self.toggle_recording)

        # --------------------------

        # --------------------------
        # Labels/Text
        # --------------------------
        
        # Status label
        self.status_label = tk.Label(
            self.root, 
            text="", 
            bg="black", 
            fg="lime"
        )
        self.status_label.grid(
            row=2, column=0, columnspan=2, sticky="sw", padx=10, pady=10)
        
        # Console Display
        # Make the console display resizable
        self.console_display.text_widget.grid(
            row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)
        self.root.grid_columnconfigure(2, weight=0)

        # --------------------------
        # Menu
        # --------------------------

        menubar = tk.Menu(self.root)
        menubar.configure(bg="black", fg="lime")
        
        # = File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)

        # == Quit
        file_menu.add_command(label="Quit", command=self.on_closing)

        # = Options menu
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)
        
        # == Screen recording option
        self.screen_record_allow = tk.IntVar(value=True)
        options_menu.add_checkbutton(
            label='Allow Screen Recording', 
            variable=self.screen_record_allow,
            command=self.toggle_screen_recording
        )

        # == Assistant voice option
        self.voice_assistant_allow = tk.IntVar(value=True)
        options_menu.add_checkbutton(
            label='Enable Assistant Voice', 
            variable=self.voice_assistant_allow,
            command=self.toggle_eav
        )

        # == Assistant voice option
        self.convo_mode_allow = tk.IntVar(value=True)
        options_menu.add_checkbutton(
            label='Enable Conversation Mode', 
            variable=self.convo_mode_allow,
            command=self.toggle_eav
        )

        # == LLM Provider submenu
        llm_provider_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label="TTS Provider", menu=llm_provider_menu)

        # LLM Provider options
        self.tts_provider = tk.StringVar(value="openai")
        llm_provider_menu.add_radiobutton(
            label='OpenAI TTS', 
            variable=self.tts_provider,
            value="openai"
        )
        llm_provider_menu.add_radiobutton(
            label='ElevenLabs TTS', 
            variable=self.tts_provider,
            value="elevenlabs"
        )

        # == LLM Temperature control submenu
        llm_temp_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label="LLM Temperature", menu=llm_temp_menu)

        # LLM Temperature control
        llm_temp_menu.add_command(
            label="Adjust Temperature", 
            command=self.show_temp_control_dialog
        )

        # = Monitors/Webcams menu
        monitors_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Select Monitor/Webcam", menu=monitors_menu)

        # == Monitors and Webcam options
        self.monitor_list = self.get_monitor_and_webcam_list()
        self.monitor_var = tk.StringVar(value=self.monitor_list[0] if self.monitor_list else "")
        for monitor in self.monitor_list:
            monitors_menu.add_radiobutton(
                label=monitor,
                variable=self.monitor_var,
                value=monitor,
                command=self.select_monitor_or_webcam,
            )

        # = Microphones menu
        microphones_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Select Microphone", menu=microphones_menu)

        # == Microphone options
        self.microphone_list = self.get_microphone_list()
        self.microphone_var = tk.StringVar(value=self.microphone_list[0] if self.monitor_list else "")
        self.microphone_var.set(self.microphone_list[0])
        for microphone in self.microphone_list:
            microphones_menu.add_radiobutton(
                label=microphone,
                variable=self.microphone_var,
                value=microphone,
                command=self.select_microphone
            )

        # == frame display
        # label
        self.label = tk.Label(root, text="Recording Camera Display")
        self.label.grid(row=1, column=3, padx=10, pady=10, columnspan=2)
        self.label.config(bg="black", fg="lime")

        # Create a canvas for image display
        self.frame_canvas = tk.Canvas(root, width=305, height=305)
        self.frame_canvas.grid(row=0, column=3, padx=10, pady=10, columnspan=1, rowspan=1)
        self.frame_canvas.config(bg="black")

        # Configure the root window to display the menubar
        self.root.config(menu=menubar)

        # -----------------------------

        self.console_display.add_text(f"Hello! Press Start and begin speaking. You are talking to LLM model \"{self.llm.gpt_model}\" from provider {self.llm.llm_provider}")

        self.logger.info(f"Platform Detected - {platform.platform().lower()}")

        if platform.system().lower() == "windows":
            self.show_popup(
                "!! Windows User Warning !!",
                "Windows users might have an issue with monitor numbering being backwards. This means monitor 1 will be monitor 2 and other such cases. Fix/workaround in the works."
            )

    
    def show_popup(self, title, content):
        """
        Show a popup with a title and the content

        Parameters:
        - title: text title of popup
        - content: text content of popup

        Returns:
        - None
        """
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("400x150")  # Set a fixed size for the window
        popup.resizable(False, False)  # Make the window non-resizable
        popup.transient(root)  # Make it transient to the main window

        frame = tk.Frame(popup)
        frame.pack(expand=True, fill='both', padx=10, pady=10)

        tk.Label(
            frame,
            text=content,
            font=("Consolas", 10),
            wraplength=380,  # Adjust this value based on your window width
            justify='center'
        ).pack(expand=True, fill='both')

        popup.lift()
        popup.attributes('-topmost', True)
        popup.focus_force()  # Force focus on the pop-up
        popup.after_idle(popup.attributes, '-topmost', False)

    def get_monitor_and_webcam_list(self):
        monitors = [f"Monitor {i}" for i in range(1, len(mss.mss().monitors))]
        webcams = []

        # Get list of available webcams
        index = 0
        while index < 6:
            self.logger.info(f"Check cam index {index}")

            if platform.system().lower() == "windows":
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(index)

            if cap.read()[0]:
                webcams.append(f"Webcam {index}")
                cap.release()
            index += 1

        return ["All Monitors 0"] + monitors + webcams

    def select_monitor_or_webcam(self):
        selected_item = self.monitor_var.get()
        if selected_item.startswith("Monitor"):
            self.monitor_number = int(selected_item.split(" ")[1])
            self.use_webcam = False
        elif selected_item.startswith("Webcam"):
            self.webcam_index = int(selected_item.split(" ")[1])
            self.use_webcam = True
        print(f"Selected: {selected_item}")

    def get_microphone_list(self):
        p = pyaudio.PyAudio()
        mic_list = []
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                mic_listed_check = any(device_info['name'] in x for x in mic_list)
                if not mic_listed_check:
                    mic_list.append(f"{i}: {device_info['name']}")
        return mic_list

    def select_microphone(self):
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
        self.allow_screen_recording = bool(self.screen_record_allow.get())

    def toggle_eav(self):
        self.enable_assistant_voice = bool(self.voice_assistant_allow.get())

    def update_temperature(self, val):
        val = round(float(val), 2)
        self.temp_label.config(text=f"Temp @ {val}")
        self.llm.llm_temp = val
        self.logger.info(f"Updating llm temp to {val}")
        
    def show_temp_control_dialog(self):
        temp_control_dialog = tk.Toplevel(self.root)
        temp_control_dialog.title("Adjust LLM Temperature")
        temp_control_dialog.configure(bg='#2b2b2b')

        ts_style = ttk.Style()
        ts_style.configure("Horizontal.TScale", length=300)

        self.temp_var = tk.DoubleVar(value=self.llm.llm_temp)
        temp_knob = ttk.Scale(
            temp_control_dialog, 
            from_=0, 
            to=1, 
            orient='horizontal', 
            variable=self.temp_var, 
            command=self.update_temperature,
            style="Horizontal.TScale"
        )
        temp_knob.grid(row=0, column=0, padx=10, pady=10)

        self.temp_label = tk.Label(
            temp_control_dialog, 
            text=f"Temp @ {self.llm.llm_temp}", 
            bg="black", 
            fg="lime"
        )
        self.temp_label.grid(row=1, column=0, padx=10, pady=10)

    
    def start_recording(self):
        self.update_status("Recording & Transcribing...")
        self.console_display.add_text(f"Recording from {self.microphone_var.get()} and {self.monitor_var.get()}")
        self.logger.info("Recording & Transcribing...")
        self.is_recording = True

        # stop any audio
        self.logger.info("Stopping TTS if any")
        if self.tts and self.tts.is_playing:
            self.tts.stop_audio()

        # record monitor
        if not self.use_webcam and self.allow_screen_recording:
            # get monitor selection and start
            if self.monitor_number > 0:
                self.console_display.add_text(
                    f"Screen Recording Started on Monitor {self.monitor_number}",
                    "system"
                )
            else:
                self.console_display.add_text(
                    f"Screen Recording Started on all monitors",
                    "system"
                )

            self.logger.info("Starting screen recording thread")

            self.screen_recorder = ScreenRecorder(
                self.monitor_number
            )
            self.video_rec_thread = threading.Thread(
                target=self.screen_recorder.start_recording)
            self.video_rec_thread.start()
        elif self.use_webcam:
            self.console_display.add_text(
                f"Camera Recording Started on Camera {self.webcam_index}",
                "system"
            )
            self.logger.info("Starting camera recording thread")
            self.cam_recorder = CamRecorder(
                self.frame_canvas,
                self.webcam_index
            )
            self.video_rec_thread = threading.Thread(
                target=self.cam_recorder.start_recording)
            self.video_rec_thread.start()

        
        # start mic and record for transcribe
        self.console_display.add_text(
            "Audio and Transcribing Started",
            "system"
        )
        self.logger.info("Starting record_transcribe thread")
        
        self.audio_rec_thread = threading.Thread(
            target=self.transcriber.record_transcribe)
        self.audio_rec_thread.start()

        self.start_stop_button.config(text="Stop", style='Red.TButton')
        
    def stop_recording(self):
        self.update_status("Stopping Recording & Transcribing")
        self.logger.info("Stopping Recording & Transcribing...")
        self.console_display.add_text("Stopping recordings...")

        self.logger.debug("Changing to Processing button...")        
        self.start_stop_button.config(text="Record", style='Gray.TButton')
        self.start_stop_button.config(state='disabled')

        processing_thread = threading.Thread(target=self._process_stop_recording)
        processing_thread.start()

    def _process_stop_recording(self):
        """
        Thread to close all audio recording threads
        and to independently update the UI
        """
        if self.tts and self.tts.is_playing:
            self.tts.stop_audio()

        self.is_recording = False

        self.transcriber.audio_recorder.stop()
        self.logger.info("self.audio_rec_thread.join()")
        self.audio_rec_thread.join(timeout=10)

        if not self.use_webcam and self.allow_screen_recording:
            self.logger.info("self.screen_recorder.stop_recording()")
            self.screen_recorder.stop_recording()
        
            self.logger.info("self.video_rec_thread.join()")
            self.video_rec_thread.join(timeout=10)

            self.console_display.add_text(
                f"Screen Recording Stopped\n{len(self.screen_recorder.base64_frames)} frames captured",
                "system"
            )
        elif self.use_webcam:
            self.logger.info("self.cam_recorder.stop_recording()")
            self.cam_recorder.stop_recording()
        
            self.logger.info("self.video_rec_thread.join()")
            self.video_rec_thread.join(timeout=10)

            self.console_display.add_text(
                f"Webcam Stopped\n{len(self.cam_recorder.base64_frames)} frames captured",
                "system"
            )

        self.logger.info("self.audio_rec_thread.join()")
        
        self.console_display.add_text(
            "Audio and Transcribing Stopped",
            "system"
        )
        self.update_status("Recording stopped")
        self.logger.info("Recording stopped")

        self.frame_canvas.delete("all")

        self.console_display.add_text(f"{self.transcriber.transcribed_text}", ftype="user")
        
        if self.is_agent:
            self.ai_thread = threading.Thread(target=self._loop_process_ai_assistant)
        else:
            self.ai_thread = threading.Thread(target=self.process_ai_assistant)

        self.ai_thread.start()

    def _update_button_to_start(self):
        self.logger.info("Changing to Start button...")
        self.start_stop_button.config(text="Start Recording", style='Green.TButton')
        self.start_stop_button.config(state='normal')

    def _loop_process_ai_assistant(self):
        while self.llm.llmfunc.loop_active and self.is_agent:
            self.logger.info("looping assistant")

            # get a screen capture
            if self.allow_screen_recording and self.agent_loop > 1:
                monitor_number = int(self.monitor_var.get().split()[-1])
                self.screen_recorder = ScreenRecorder(monitor_number)
                self.screen_recorder.get_frame()

            self.process_ai_assistant()
            self.agent_loop += 1
            time.sleep(2)
        
        self.agent_loop = 0 # reset for next loop
        self.is_agent = False

    def process_ai_assistant(self):
        self.console_display.add_text("Interfacing with AI...", "system")
        self.update_status("AI processing....")
        self.logger.info(f"transcription_text: {self.transcriber.transcribed_text}")
        try:
            if not self.allow_screen_recording:
                resp = self.llm.run(
                    frames_hw=None,
                    sbframes=None,
                    transcription_text=self.transcriber.transcribed_text
                )
            else:
                if not self.use_webcam:
                    resp = self.llm.run(
                        frames_hw=self.screen_recorder.frames[0].shape,
                        sbframes=self.screen_recorder.base64_frames,
                        transcription_text=self.transcriber.transcribed_text
                    )
                elif self.use_webcam:
                    resp = self.llm.run(
                        frames_hw=self.cam_recorder.frames[0].shape,
                        sbframes=self.cam_recorder.base64_frames,
                        transcription_text=self.transcriber.transcribed_text
                    )
            
            # clear frames and text
            self.transcriber.transcribed_text = ""

            if resp and self.enable_assistant_voice:
                self.tts = TTS(self.console_display, self.tts_provider)
                self.tts_thread = threading.Thread(
                    target=self.tts.run_speech, args=(resp,)
                )
                self.tts_thread.start()
                self.tts_thread.join()

            self.logger.info("done processing")

            if not self.is_agent:
                if not self.convo_mode_allow:
                    # Update the UI in the main thread with start recording btn
                    self.start_stop_button.after(0, self._update_button_to_start)
                else:
                    # Open back up the mic for a response
                    self.console_display.add_text("Conversation Mode enabled, Opening Mic for Response", "system")
                    self.start_recording()

        except Exception as err:
            self.update_status("Error with LLM! Please retry...", error=True)
            self.console_display.add_text("Error with LLM! Please try again...")
            self.logger.error(err)

    def update_status(self, message, error=False):
        if error:
            self.status_label.config(fg="red", text=message)
        else:
            self.status_label.config(fg="lime", text=message)

    def on_closing(self):
        if self.tts and self.tts.is_playing:
            if self.tts_thread.is_alive:
                self.tts_thread.join(timeout=1)
            
            self.tts.stop_audio()

        if self.screen_recorder:
            if self.video_rec_thread.is_alive:
                self.video_rec_thread.join(timeout=1)
            self.screen_recorder.stop_recording()
        
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    load_dotenv()
    root = tk.Tk()
    app = Tamagg(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
