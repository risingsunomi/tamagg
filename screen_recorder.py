import cv2
import ctypes
import numpy as np
import mss
import base64
import sqlite3
import logging

class ScreenRecorder:
    def __init__(self, monitor_number: int=1):
        self.monitor_number = monitor_number
        self.frames = []
        self.base64_frames = []
        self.is_recording = False
        self.logger = logging.getLogger(__name__)

        # Load NVJPEG shared library
        self.nvjpeg = ctypes.CDLL('./clib/libnvjpeg_encoder.so')
        self.nvjpeg.initialize_nvjpeg()

        # convert to base64 along with jpeg cuda using c++ lib
        self.nvjpeg64 = ctypes.CDLL('./clib/libnvjpeg_encoder64.so')
        self.nvjpeg64.initialize_nvjpeg()

        # setup sqlite for desk storage of frames for longer recordings
        self.sqlconn = sqlite3.connect("data/screen_recorder.sql")
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            "CREATE TABLE frames (id INTEGER PRIMARY KEY, frame BLOB)")
    
    def start_recording(self):
        self.is_recording = True

        self.logger.info(f"Starting Monitor {self.monitor_number} Recording...")

        try:
            with mss.mss() as sct:
                monitor = sct.monitors[self.monitor_number]
                while self.is_recording:
                    frame = np.array(sct.grab(monitor))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    # self.frames.append(frame)
                    self.cuda_convert_frame_to_pybase64(
                        frame,
                        self.base64_frames
                    )
            
                self.logger.info("Stopped Monitor Recording")
        except Exception as err:
            self.logger.error(f"Monitor Recording failed: {err}")

    def stop_recording(self):
        self.logger.debug("stop_recording called")
        self.is_recording = False

    def store_frame_in_db(self, bframe):
        self.cursor.execute('INSERT INTO frames (frame) VALUES (?)', (bframe,))
        self.conn.commit()

    def cuda_convert_frame_to_cppbase64(self, frame) -> list:
        """
        Converts frames to JPEG using cuda and converts cuda JPEG to
        base64 using cpp-base64 library
        """
        self.logger.info(f"[c++b64] converting frame to b64")

        height, width, _ = frame.shape
        d_image = frame.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))

        base64_output = ctypes.POINTER(ctypes.c_char)()
        self.nvjpeg.encode_image(
            d_image, 
            width, 
            height, 
            ctypes.byref(base64_output)
        )

        base64_image = ctypes.string_at(base64_output)

        # Free the memory allocated by the C++ code
        ctypes.CDLL('libc.so.6').free(base64_output)

        self.base64_frames.append(
            base64_image.decode('utf-8')
        )

        self.logger.info("conversion completed")
    
    def cuda_convert_frame_to_pybase64(self, frame) -> list:
        """
        Using CUDA to convert frame to JPEG
        Then JPEG to base64 list
        """
        self.logger.info(f"[cjpeg] converting frame to b64")

        height, width, _ = frame.shape
        d_image = frame.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
        jpeg_output = (ctypes.POINTER(ctypes.c_ubyte))()
        jpeg_length = ctypes.c_size_t()

        vector_type = ctypes.c_ubyte * (width * height * 3)
        jpeg_vector = vector_type()

        self.nvjpeg.encode_image(
            d_image, 
            width, 
            height, 
            ctypes.byref(jpeg_vector)
        )

        jpeg_image = bytearray(jpeg_vector[:jpeg_length.value])

        # Free the memory allocated by the C++ code
        libc = ctypes.CDLL('libc.so.6')
        libc.free(jpeg_output)

        self.base64_frames.append(
            base64.b64encode(jpeg_image).decode('utf-8')
        )

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
        self.store_frame_in_db(
            base64.b64encode(buffer).decode('utf-8')
        )

        self.logger.info("conversion completed")

    

    def __del__(self):
        self.nvjpeg.cleanup_nvjpeg()
