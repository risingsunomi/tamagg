import cv2
import numpy as np
import mss
import logging
import os
from datetime import datetime

class ScreenRecorder:
    def __init__(self, monitor_number: int=1, output_file: str=None):
        self.monitor_number = monitor_number
        self.output_file = output_file
        self.recording = False
        self.buffer = []
        self.logger = logging.getLogger(__name__)

        if not output_file:
            nn = datetime.now().strftime("%Y%M%d_%h%m%s")
            root_dir = os.path.dirname(os.path.abspath(__file__))
            self.output_file = f"{root_dir}/data/recording{nn}.avi"

    def start_recording(self):
        self.buffer = []  # Clear the buffer at the start of each new recording
        self.recording = True

        self.logger.info(f"Starting Monitor {self.monitor_number} Recording...")

        with mss.mss() as sct:
            monitor = sct.monitors[self.monitor_number]
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(self.output_file, fourcc, 20.0, (monitor["width"], monitor["height"]))

            while self.recording:
                frame = np.array(sct.grab(monitor))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                out.write(frame)
                self.buffer.append(frame)

            out.release()

    def stop_recording(self):
        self.logger.debug("Stopping recording")
        self.recording = False

    def get_buffer(self):
        return self.buffer
