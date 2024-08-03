import unittest
import numpy as np
from PIL import Image
import logging
from pathlib import Path

from dolphin_vision_model import DolphinVisionModel

class TestDolphinVisionModel(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.model = DolphinVisionModel()

    def test_describe_image_from_path(self):
        image_path = Path("./data/ocv_decoded_image.jpg")
        description = self.model.describe_image(image_path)
        logging.info(f"model description\n{description}")
        self.assertIsInstance(description, str)
        self.assertTrue(len(description) > 0)

    # def test_describe_image_from_array(self):
    #     # Create a dummy image array (e.g., 100x100 RGB image)
    #     image_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    #     description = self.model.describe_image(image_array)
    #     self.assertIsInstance(description, str)
    #     self.assertTrue(len(description) > 0)

    # Uncomment to visualize the result (for debugging purposes)
    # def test_visualize_description(self):
    #     description = self.model.describe_image('/path/to/test_image.png')
    #     print(description)

if __name__ == '__main__':
    unittest.main()
