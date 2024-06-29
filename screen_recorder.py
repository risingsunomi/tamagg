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
from PIL import Image, ImageDraw, ImageFont

from oai_ict import OpenAIImageCoordinateTranslator

class ScreenRecorder:
    def __init__(self, monitor_number: int=1):
        self.record_id = shortuuid.uuid()
        self.monitor_number = monitor_number
        self.frames: list[np.ndarray] = []
        self.max_frames = 3000
        self.base64_frames: list[str] = []
        self.is_recording = False
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.sampled_coords = []

        # Load NVJPEG shared library
        # self.nvjpeg = ctypes.CDLL('./clib/libnvjpeg_encoder.so')
        # self.nvjpeg.initialize_nvjpeg()

        # setup sqlite for desk storage of frames for longer recordings
        # cdate = datetime.now().strftime("%Y%d%m_%H%M%S")
        # self.sqldb = f"{self.root_dir}/data/sr{cdate}.sql"
        # self.sqlconn = sqlite3.connect(
        #     self.sqldb,
        #     check_same_thread=False
        # )
        # self.sqlcursor = self.sqlconn.cursor()
        
        # try:
        #     self.sqlcursor.execute(
        #         """ CREATE TABLE frames (
        #             id INTEGER PRIMARY KEY, record_id TEXT, frame BLOB
        #         )""")
        # except sqlite3.OperationalError:
        #     pass

    def process_frame(self, frame: np.ndarray, use_cuda=False):
        # process the frame and convert to base64
        # cuda current not working, working on fix

        self.convert_frames_to_base64(frame)

        # if use_cuda:
        #     frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        #     self.cuda_convert_frame_to_pybase64(frame)
        # else:
        #     # uses opencv
        #     self.convert_frames_to_base64(frame)
    
    def start_recording(self):
        self.is_recording = True

        self.logger.info(f"Starting Monitor {self.monitor_number} Recording...")

        try:
            fcnt = 1
            with mss.mss() as sct:
                if self.monitor_number == -1 and len(sct.monitors) >= 3:
                    while self.is_recording:
                        screen_caps = [np.array(sct.grab(sct.monitors[i])) for i in range(1, len(sct.monitors))]
                        # hstack
                        combined_monitors = np.hstack(tuple(screen_caps))

                        # process
                        self.process_frame(
                            combined_monitors,
                            True
                        )

                        self.logger.info(f"Captured frame {fcnt}")
                        fcnt += 1
                else:
                    if self.monitor_number == -1:
                        self.monitor_number == 1

                    monitor = sct.monitors[self.monitor_number]
                    while self.is_recording:
                        if fcnt == self.max_frames:
                            self.logger.info(f"Stopped at frame {self.max_frames} due to AI model space")
                            break

                        self.process_frame(
                            np.array(sct.grab(monitor)), True)
                        
                        self.logger.info(f"Captured frame {fcnt}")
                        fcnt += 1
            
                self.logger.info("Stopped Monitor Recording")
        except Exception as err:
            self.logger.error(f"Monitor Recording failed: {err}")

    def stop_recording(self):
        self.logger.debug("stop_recording called")
        self.is_recording = False
        # self.frames = self.get_frames()

    def get_frame(self):
        with mss.mss() as sct:
            if self.monitor_number == -1 and len(sct.monitors) >= 3:
                screen_caps = [np.array(sct.grab(sct.monitors[i])) for i in range(1, len(sct.monitors))]
                # hstack
                combined_monitors = np.hstack(tuple(screen_caps))

                # process
                self.process_frame(
                    combined_monitors,
                    True
                )
            else:
                if self.monitor_number == -1:
                    self.monitor_number == 1

                monitor = sct.monitors[self.monitor_number]
                self.process_frame(
                    np.array(sct.grab(monitor)), True)
                

    def put_frame(self, bframe):
        """
        Store base64 frame in database
        """
        self.logger.info("Adding frame")
        # self.frames.append(bframe)
        if not np.isin(bframe, self.frames):
            self.base64_frames.append(bframe)
        else:
            self.logger.info("Skipping frame, already present")

        # sql issue not waiting long enough for writes to complete
        # and causing a sig fault when trying to access db
        # working on fix
        # self.sqlcursor.execute(
        #     "INSERT INTO frames (record_id, frame) VALUES (?,?)",
        #     (self.record_id, bframe)
        # )

        # self.sqlconn.commit()

    # def get_frames(self):
    #     """
    #     Get frames from database per record_id
    #     """
    #     self.logger.info(f"getting frames for recording {self.record_id}")
    #     self.sqlcursor.execute(
    #         "SELECT frame FROM frames WHERE record_id=?",
    #         (self.record_id,)
    #     )
        
    #     rows = self.sqlcursor.fetchall()
    #     return [row[0] for row in rows]
    
    def frame_in_list(self, frame):
        """
        Check if a given frame is present in a list of frames.
        """
        for f in self.frames:
            if np.array_equal(frame, f):
                return True
        return False
    
    def add_transparent_text(
            self,
            image, 
            text, 
            position, 
            font_scale, 
            font_color, 
            font_thickness, 
            alpha):
        """
        Add transparent text to an RGBA image.

        Parameters:
        - image: The original RGBA image as a NumPy array.
        - text: The text to add.
        - position: (x, y) coordinates for the text position.
        - font_scale: Scale of the font.
        - font_color: Color of the text in (B, G, R) format.
        - font_thickness: Thickness of the font.
        - alpha: Transparency factor of the text (0.0 to 1.0).

        Returns:
        - image with transparent text.
        """
        overlay = image.copy()
        cv2.putText(overlay, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_color, font_thickness, cv2.LINE_AA)
        cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
        return image
    
    def add_grid_overlay(self, image_array: np.ndarray, grid_size=60) -> np.ndarray:
        """
        Adds a grid overlay to an image with coordinates at each intersection.

        Parameters:
        image_array (np.ndarray): The image array.
        grid_size (int): The size of each grid cell.

        Returns:
        np.ndarray: The image with the grid overlay and coordinates.
        """
        # Ensure image is in RGB mode
        self.logger.info(f"image_array.shape {image_array.shape}")
        if image_array.shape[2] == 4:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_BGRA2BGR)

        # Get image dimensions
        height, width, _ = image_array.shape

        # Convert the PIL image back to a numpy array
        # result_array = np.array(image)

        # Draw coordinates at intersections
        # Using opencv for transparent text

        text_positions = [(x, y) for x in range(0, width, grid_size) for y in range(0, height, grid_size)]
        text_list = [f"{x},{y}" for x, y in text_positions]

        # Draw coordinates at intersections using add_transparent_text method
        for pos, text in zip(text_positions, text_list):
            image_array = self.add_transparent_text(
                image_array, 
                text, 
                (pos[0], pos[1]), 
                0.4, 
                (255, 255, 255, 255), 
                1, 
                0.1)
        
        # for x in range(0, width, grid_size):
        #     for y in range(0, height, grid_size):
        #         image_array = self.add_transparent_text(
        #             image_array, 
        #             f"{x},{y}", 
        #             (x, y), 
        #             0.4, 
        #             (255, 255, 255, 255),
        #             1,
        #             0.1
        #         )
        
        return image_array

    
    def oai_resize_image(self, frame: np.ndarray) -> np.ndarray:
        """
        Resizes the image to OpenAI format.

        Parameters:
        frame (np.ndarray): The input image array.

        Returns:
        np.ndarray: The resized image array.
        """
        # resize to openai format
        oai_coord = OpenAIImageCoordinateTranslator(
            original_width=frame.shape[1],
            original_height=frame.shape[0]
        )

        resized_width, resized_height = oai_coord.calculate_resized_dimensions()

        self.logger.info(f"Resizing to {resized_width}x{resized_height}")
        
        img = Image.fromarray(frame)
        resized_img = img.resize((int(resized_width), int(resized_height)), Image.Resampling.LANCZOS)

        try:
            resized_array = np.array(resized_img)
        except Exception as err:
            self.logger.error("np.array failed", exc_info=err)
            raise

        return resized_array


        
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
    
    def convert_frames_to_base64(self, frame: np.ndarray):
        """
        Using python opencv library to encode frame to jpeg image
        then converting to base64
        """
        if not self.frame_in_list(frame):
            self.frames.append(frame)
            self.logger.info(f"[ocv] converting frame to b64")

            # Add grid overlay
            frame = self.add_grid_overlay(image_array=frame)

            # resize to oai
            frame = self.oai_resize_image(frame)

            # Encode frame to JPEG format
            _, buffer = cv2.imencode('.jpg', frame)

            # Convert buffer to base64 and store in db
            self.put_frame(
                base64.b64encode(buffer).decode('utf-8')
            )

            self.logger.info("conversion completed")
        else:
            self.logger.info("Frame already present in memory, skipping")

    # def __del__(self):
        # self.sqlconn.close()
