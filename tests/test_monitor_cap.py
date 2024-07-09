import unittest
import numpy as np
import cv2  # Used here just for displaying the image, optional
import mss

class TestMonitorCapture(unittest.TestCase):
    def test_all_monitors(self):
        # Initialize mss
        with mss.mss() as sct:
            # List of all monitors
            monitors = sct.monitors

            # Check if there are at least two monitors
            if len(monitors) < 3:
                raise ValueError("Less than two monitors detected.")

            # Capture both screens
            screen1 = np.array(sct.grab(monitors[1]))
            screen2 = np.array(sct.grab(monitors[2]))

            # Assuming horizontal alignment for simplicity
            combined_image = np.hstack((screen1, screen2))

            # cv2.imshow('Combined Image', combined_image)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()

            self.assertNotEqual(combined_image.size, 0)
    
    def test_one_monitors(self):
        # Initialize mss
        with mss.mss() as sct:
            # List of all monitors
            monitors = sct.monitors
            screen = np.array(sct.grab(monitors[2]))

            cv2.imshow('Screen', screen)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            self.assertNotEqual(screen.size, 0)
