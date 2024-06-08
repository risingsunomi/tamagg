import cv2
import ctypes
import numpy as np
import mss
import logging

class ScreenRecorder:
    def __init__(self, monitor_number: int=1):
        self.monitor_number = monitor_number
        self.sct = mss.mss()
        self.frames = []
        self.is_recording = False
        self.logger = logging.getLogger(__name__)

        # Load NVJPEG shared library
        self.nvjpeg = ctypes.CDLL('./clib/libnvjpeg_encoder.so')
        self.nvjpeg.initialize_nvjpeg_wrapper()

    def start_recording(self):
        self.buffer = []  # Clear the buffer at the start of each new recording
        self.is_recording = True

        self.logger.info(f"Starting Monitor {self.monitor_number} Recording...")

        try:
            monitor = self.sct.monitors[self.monitor_number]
            while self.is_recording:
                frame = np.array(self.sct.grab(monitor))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                self.frames.append(frame)
            
            self.logger.info("Stopped Monitor Recording")
        except Exception as err:
            self.logger.error(f"Monitor Recording failed: {err}")

    def stop_recording(self):
        self.logger.debug("stop_recording called")
        self.is_recording = False

    def convert_frame_to_base64(self, frame):
        height, width, _ = frame.shape
        d_image = frame.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))

        base64_output = ctypes.POINTER(ctypes.c_char)()
        self.nvjpeg.encode_image_wrapper(d_image, width, height, ctypes.byref(base64_output))

        base64_image = ctypes.string_at(base64_output)

        # Free the memory allocated by the C++ code
        ctypes.CDLL('libc.so.6').free(base64_output)

        return base64_image.decode('utf-8')

    def convert_to_base64(self):
        base64_frames = [self.convert_frame_to_base64(frame) for frame in self.frames]
        return base64_frames

    def __del__(self):
        self.nvjpeg.cleanup_nvjpeg_wrapper()
