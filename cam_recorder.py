"""
CamRecorder

handles camera recording and convert to jpeg then base64
"""
import cv2
import ctypes
import numpy as np
import base64
import shortuuid
import logging
import os
import threading
from PIL import Image, ImageDraw

class CamRecorder:
    def __init__(self, camera_index: int=0):
        self.record_id = shortuuid.uuid()
        self.camera_index = camera_index
        self.frames: list[np.ndarray] = []
        self.max_frames = 3000
        self.base64_frames: list[str] = []
        self.is_recording = False
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
    
    def start_recording(self):
        self.is_recording = True

        self.logger.info(f"Starting Camera {self.camera_index} Recording...")

        try:
            fcnt = 1
            cap = cv2.VideoCapture(self.camera_index)
            while self.is_recording:
                if fcnt == self.max_frames:
                    self.logger.info(f"Stopped at frame {self.max_frames} due to AI model space")
                    break

                ret, frame = cap.read()
                if not ret:
                    self.logger.error("Failed to capture frame from camera")
                    break

                self.convert_frames_to_base64(frame)

                self.logger.info(f"Captured frame {fcnt}")
                fcnt += 1

            cap.release()
            self.logger.info("Stopped Camera Recording")
        except Exception as err:
            self.logger.error(f"Camera Recording failed: {err}")

    def stop_recording(self):
        self.logger.debug("stop_recording called")
        self.is_recording = False

    def get_frame(self):
        cap = cv2.VideoCapture(self.camera_index)
        ret, frame = cap.read()
        cap.release()
        if ret:
            self.process_frame(frame)

    def put_frame(self, bframe):
        if not np.isin(bframe, self.frames):
            self.base64_frames.append(bframe)
        else:
            self.logger.info("Skipping frame, already present")
    
    def frame_in_list(self, frame):
        for f in self.frames:
            if np.array_equal(frame, f):
                return True
        return False

    def convert_frames_to_base64(self, frame: np.ndarray):
        if not self.frame_in_list(frame):
            self.frames.append(frame)
            self.logger.info(f"[ocv] converting frame to b64")

            _, buffer = cv2.imencode('.jpg', frame)
            self.put_frame(base64.b64encode(buffer).decode('utf-8'))

            self.logger.info("conversion completed")
        else:
            self.logger.info("Frame already present in memory, skipping")
