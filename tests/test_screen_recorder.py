import os
import unittest
import base64
import ctypes
import numpy as np
import cv2
from mss import mss
from screen_recorder import ScreenRecorder

class TestScreenRecorder(unittest.TestCase):
    def setUp(self):
        self.screen_recorder_instance = ScreenRecorder()

    # def test_cuda_convert_frame_to_pybase64(self):
    #     # Capture a screenshot using mss
    #     with mss() as sct:
    #         monitor = sct.monitors[1]
    #         screenshot = sct.grab(monitor)
    #         frame = np.array(screenshot)
    #         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    #     # Convert the frame to base64
    #     try:
    #         self.screen_recorder_instance.cuda_convert_frame_to_pybase64(frame)
    #         base64_image = self.screen_recorder_instance.frames[0]

    #         # Decode the base64 image back to bytes
    #         jpeg_image = base64.b64decode(base64_image)

    #         # Convert the bytes back to a numpy array for OpenCV
    #         nparr = np.frombuffer(jpeg_image, np.uint8)
    #         img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    #         # Check if the image is valid and can be decoded
    #         self.assertIsNotNone(img_np, "Decoded image is None")

    #         # Display the image using OpenCV (optional, for visual confirmation)
    #         # cv2.imshow('Decoded Image', img_np)
    #         # cv2.waitKey(0)
    #         # cv2.destroyAllWindows()

    #         # Save the image to a local data folder
    #         output_folder = "data/"
    #         output_path = os.path.join(output_folder, 'cuda_decoded_image.jpg')
    #         cv2.imwrite(output_path, img_np)

    #         # check image save
    #         self.assertTrue(os.path.exists(output_path), "Image not saved successfully")

    #         # Additional assertions can be added here if necessary
    #         # Example: Check if the dimensions match
    #         self.assertEqual(frame.shape[0], img_np.shape[0], "Height does not match")
    #         self.assertEqual(frame.shape[1], img_np.shape[1], "Width does not match")
    #     except Exception as err:
    #         self.assertIsNone(err)

    def test_opencv_convert_frame_to_pybase64(self):
        # Capture a screenshot using mss
        with mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)

        # Convert the frame to base64
        try:
            self.screen_recorder_instance.convert_frames_to_base64(frame)
            base64_image = self.screen_recorder_instance.frames[0]

            # Decode the base64 image back to bytes
            jpeg_image = base64.b64decode(base64_image)

            # Convert the bytes back to a numpy array for OpenCV
            nparr = np.frombuffer(jpeg_image, np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Check if the image is valid and can be decoded
            self.assertIsNotNone(img_np, "Decoded image is None")

            # Display the image using OpenCV (optional, for visual confirmation)
            # cv2.imshow('Decoded Image', img_np)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()

            # Save the image to a local data folder
            output_folder = "data/"
            output_path = os.path.join(output_folder, 'ocv_decoded_image.jpg')
            cv2.imwrite(output_path, img_np)

            # check image save
            self.assertTrue(os.path.exists(output_path), "Image not saved successfully")

            # Additional assertions can be added here if necessary
            # Example: Check if the dimensions match
            self.assertEqual(frame.shape[0], img_np.shape[0], "Height does not match")
            self.assertEqual(frame.shape[1], img_np.shape[1], "Width does not match")
        except Exception as err:
            self.assertIsNone(err)

if __name__ == '__main__':
    unittest.main()
