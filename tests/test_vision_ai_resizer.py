from PIL import Image
import numpy as np
import logging
import unittest
import os
import shutil

class VisionAIImageResizer:
    def __init__(self, quality='high'):
        """
        Initialize the VisionAIImageResizer class.
        """
        self.quality = quality
        self.logger = logging.getLogger(__name__)

    def calculate_resized_dimensions(self, original_width, original_height):
        """
        Calculate the resized dimensions of the image based on the quality setting.
        """
        if self.quality == 'low':
            max_size = 512
        else:
            max_size = 2048

        max_dimension = max(original_width, original_height)
        if max_dimension > max_size:
            scale_factor = max_size / max_dimension
            temp_width = original_width * scale_factor
            temp_height = original_height * scale_factor
        else:
            temp_width = original_width
            temp_height = original_height

        if self.quality == 'high':
            min_dimension = min(temp_width, temp_height)
            scale_factor = 768 / min_dimension
            resized_width = np.floor(temp_width * scale_factor)
            resized_height = np.floor(temp_height * scale_factor)
        else:
            resized_width = np.floor(temp_width)
            resized_height = np.floor(temp_height)

        return int(resized_width), int(resized_height)

    def resize_image(self, image_path, output_path):
        """
        Resize the image and save the resized image.
        """
        with Image.open(image_path) as img:
            original_width, original_height = img.size
            resized_width, resized_height = self.calculate_resized_dimensions(original_width, original_height)
            resized_img = img.resize((resized_width, resized_height))
            
            self.logger.info(f"Original size: ({original_width}, {original_height})")
            self.logger.info(f"Resized size: ({resized_width}, {resized_height})")
            
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            resized_img.save(output_path)
            self.logger.info(f"Resized image saved to {output_path}")

class TestVisionAIImageResizer(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.resizer_high = VisionAIImageResizer(quality='high')
        self.resizer_low = VisionAIImageResizer(quality='low')
        
        # Create a temporary image for testing
        self.test_image_path = 'tests/data/ocv_decoded_image.jpg'
        self.test_output_path_high = 'tests/data/test_resized_high.png'
        self.test_output_path_low = 'tests/data/test_resized_low.png'
        os.makedirs('tests/data', exist_ok=True)
        
        # Create a non-black image (with some color patterns)
        img = Image.open(self.test_image_path)

    def tearDown(self):
        pass  # Do not delete the test images

    def test_resize_image_high(self):
        self.resizer_high.resize_image(self.test_image_path, self.test_output_path_high)
        img = Image.open(self.test_output_path_high)
        resized_width, resized_height = img.size
        expected_width, expected_height = self.resizer_high.calculate_resized_dimensions(1920, 1024)
        self.assertEqual(resized_width, expected_width)
        self.assertEqual(resized_height, expected_height)

    def test_resize_image_low(self):
        self.resizer_low.resize_image(self.test_image_path, self.test_output_path_low)
        img = Image.open(self.test_output_path_low)
        resized_width, resized_height = img.size
        expected_width, expected_height = self.resizer_low.calculate_resized_dimensions(1920, 1024)
        self.assertEqual(resized_width, expected_width)
        self.assertEqual(resized_height, expected_height)

if __name__ == "__main__":
    unittest.main()
