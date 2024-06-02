import cv2
import numpy as np
import mss
import logging

class ScreenRecorder:
    def __init__(self, monitor_number=1, output_file="screen_recording.avi"):
        self.monitor_number = monitor_number
        self.output_file = output_file
        self.recording = False
        self.buffer = []
        self.logger = logging.getLogger(__name__)

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
