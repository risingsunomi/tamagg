import unittest
import cv2

def list_ports():
    """
    Test the ports and returns a tuple with the available ports and the ones that are working.
    """
    non_working_ports = []
    dev_port = 0
    working_ports = []
    available_ports = []
    while len(non_working_ports) < 6: # if there are more than 5 non working ports stop the testing. 
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            non_working_ports.append(dev_port)
            print("Port %s is not working." %dev_port)
        else:
            is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                print("Port %s is working and reads images (%s x %s)" %(dev_port,h,w))
                working_ports.append(dev_port)
            else:
                print("Port %s for camera ( %s x %s) is present but does not reads." %(dev_port,h,w))
                available_ports.append(dev_port)
        dev_port +=1
    return available_ports,working_ports,non_working_ports

class TestWebcam(unittest.TestCase):

    def setUp(self):
        self.cap = cv2.VideoCapture(2)

    def test_webcam_open(self):
        # Check if the webcam is opened correctly
        self.assertTrue(self.cap.isOpened(), "Webcam is not opened correctly")

    def test_webcam_frame(self):
        # Try to read a frame from the webcam
        ret, frame = self.cap.read()
        self.assertTrue(ret, "Failed to read frame from webcam")
        self.assertIsNotNone(frame, "Frame is None")

        # Check if the frame has the expected properties
        self.assertEqual(len(frame.shape), 3, "Frame does not have 3 dimensions")
        self.assertGreater(frame.shape[0], 0, "Frame height is not greater than 0")
        self.assertGreater(frame.shape[1], 0, "Frame width is not greater than 0")
        self.assertEqual(frame.shape[2], 3, "Frame does not have 3 color channels")

        # Uncomment the following lines to display the frame
        
        cv2.imshow('Webcam Frame', frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def tearDown(self):
        self.cap.release()

if __name__ == '__main__':
    unittest.main()
