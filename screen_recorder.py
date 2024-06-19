import cv2
import ctypes
import numpy as np
import mss
import base64
import sqlite3
import shortuuid
import logging
import os
import threading
from datetime import datetime

class ScreenRecorder:
    def __init__(self, monitor_number: int=1):
        self.record_id = shortuuid.uuid()
        self.monitor_number = monitor_number
        self.frames = []
        self.max_frames = 3000
        self.base64_frames = []
        self.is_recording = False
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))

        # Load NVJPEG shared library
        self.nvjpeg = ctypes.CDLL('./clib/libnvjpeg_encoder.so')
        self.nvjpeg.initialize_nvjpeg()

        # setup sqlite for desk storage of frames for longer recordings
        cdate = datetime.now().strftime("%Y%d%m_%H%M%S")
        self.sqldb = f"{self.root_dir}/data/sr{cdate}.sql"
        self.sqlconn = sqlite3.connect(
            self.sqldb,
            check_same_thread=False
        )
        self.sqlcursor = self.sqlconn.cursor()
        
        try:
            self.sqlcursor.execute(
                """ CREATE TABLE frames (
                    id INTEGER PRIMARY KEY, record_id TEXT, frame BLOB
                )""")
        except sqlite3.OperationalError:
            pass
    
    def start_recording(self):
        self.is_recording = True

        self.logger.info(f"Starting Monitor {self.monitor_number} Recording...")

        try:
            fcnt = 1
            with mss.mss() as sct:
                monitor = sct.monitors[self.monitor_number]
                while self.is_recording:
                    if fcnt == self.max_frames:
                        self.logger.info(f"Stopped at frame {self.max_frames} due to AI model space")
                        break
                    frame = np.array(sct.grab(monitor))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    # frame = cv2.resize(frame, (1366, 768))
                    self.logger.info("cuda convert frame calling")
                    # self.cuda_convert_frame_to_pybase64(frame)
                    self.convert_frames_to_base64(frame)

                    self.logger.info(f"Captured frame {fcnt}")
                    fcnt += 1
            
                self.logger.info("Stopped Monitor Recording")
        except Exception as err:
            self.logger.error(f"Monitor Recording failed: {err}")

    def stop_recording(self):
        self.logger.debug("stop_recording called")
        self.is_recording = False
        # self.frames = self.get_frames()

    def put_frame(self, bframe):
        """
        Store base64 frame in database
        """
        self.frames.append(bframe)
        # self.sqlcursor.execute(
        #     "INSERT INTO frames (record_id, frame) VALUES (?,?)",
        #     (self.record_id, bframe)
        # )

        # self.sqlconn.commit()

    def get_frames(self):
        """
        Get frames from database per record_id
        """
        self.logger.info(f"getting frames for recording {self.record_id}")
        self.sqlcursor.execute(
            "SELECT frame FROM frames WHERE record_id=?",
            (self.record_id,)
        )
        
        rows = self.sqlcursor.fetchall()
        return [row[0] for row in rows]
    
    def cuda_convert_frame_to_pybase64(self, frame):
        self.logger.info("[cjpeg] converting frame to b64")
        self.logger.info(f"frame shape: {frame.shape}")

        height, width, _ = frame.shape
        d_image = frame.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))

        jpeg_output = ctypes.POINTER(ctypes.c_ubyte)()
        jpeg_length = ctypes.c_size_t()

        self.nvjpeg.encode_image(
            d_image,
            width,
            height,
            ctypes.byref(jpeg_output),
            ctypes.byref(jpeg_length)
        )

        jpeg_image = ctypes.string_at(jpeg_output, jpeg_length.value)

        self.logger.info(f"jpeg_image: {len(jpeg_image)}")

        base64_image = base64.b64encode(jpeg_image).decode('utf-8')

        self.logger.info(f"base64_image: {len(base64_image)}")

        put_thread = threading.Thread(
            target=self.put_frame,
            args=(base64_image,)
        )

        put_thread.start()

        libc = ctypes.CDLL('libc.so.6')
        libc.free(jpeg_output)

        self.logger.info("conversion completed")
    
    def convert_frames_to_base64(self, frame):
        """
        Using python opencv library to encode frame to jpeg image
        then converting to base64
        """
        self.logger.info(f"[ocv] converting frame to b64")

        # Encode frame to JPEG format
        _, buffer = cv2.imencode('.jpg', frame)
        
        # Convert buffer to base64 and store in db
        self.put_frame(
            base64.b64encode(buffer).decode('utf-8')
        )

        self.logger.info("conversion completed")

    def __del__(self):
        self.sqlconn.close()
