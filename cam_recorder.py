"""
CamRecorder

handles camera recording and convert to jpeg then base64
"""
import cv2
import numpy as np
import base64
import shortuuid
import logging
import os
import threading
import platform
from PIL import Image, ImageTk
import tkinter as tk
import queue

class CamRecorder:
    def __init__(self, frame_canvas, camera_index: int=0):
        self.record_id = shortuuid.uuid()
        self.camera_index = camera_index
        self.frames: list[np.ndarray] = []
        self.max_frames = 3000
        self.base64_frames: list[str] = []
        self.is_recording = False
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.cam_display_thread = None
        self.frame_queue = queue.Queue()
        self.frame_canvas = frame_canvas
    
    def show_cam_display(self):
        """
        Display cam to show what is being captured
        """
        while self.is_recording or not self.frame_queue.empty():
            try:
                if self.frame_canvas:
                    logging.info("show frame in frame canvas")
                    frame = self.frame_queue.get(timeout=1)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    img = img.resize((300,300), Image.Resampling.NEAREST)
                    imgtk = ImageTk.PhotoImage(image=img)

                    # Calculate the center position
                    canvas_width = self.frame_canvas.winfo_width()
                    canvas_height = self.frame_canvas.winfo_height()
                    img_width = imgtk.width()
                    img_height = imgtk.height()
                    x_center = (canvas_width - img_width) // 2
                    y_center = (canvas_height - img_height) // 2

                    self.frame_canvas.create_image(x_center, y_center, anchor=tk.NW, image=imgtk)
                    self.frame_canvas.imgtk = imgtk
                
                else:
                    logging.error("No frame_canvas found")
                    break

            except queue.Empty:
                continue

    def capture_frames(self):
        """
        Capture cam video via opencv
        """
        try:
            fcnt = 1
            if platform.system().lower() == "windows":
                cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(self.camera_index)

            while self.is_recording:
                if fcnt == self.max_frames:
                    self.logger.info(f"Stopped at frame {self.max_frames} due to AI model space")
                    break

                ret, frame = cap.read()
                if not ret:
                    self.logger.error("Failed to capture frame from camera")
                    break

                self.frame_queue.put(frame.copy())
                self.convert_frames_to_base64(frame)

                self.logger.info(f"Captured frame {fcnt}")
                fcnt += 1

            cap.release()
        except Exception as err:
            self.logger.error(f"Camera Recording failed: {err}")

    def start_recording(self):
        self.is_recording = True
        self.frame_queue = queue.Queue()

        self.logger.info(f"Starting Camera {self.camera_index} Recording...")

        capture_thread = threading.Thread(target=self.capture_frames)
        display_thread = threading.Thread(target=self.show_cam_display)

        capture_thread.start()
        display_thread.start()

        capture_thread.join()
        self.is_recording = False
        display_thread.join()

        self.logger.info("Stopped Camera Recording")

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
