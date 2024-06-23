"""
OpenAI Image Coordinate Translator

Takes coordinates from OpenAI drived from an image sent to it and translates it back to the image's native resolution. This is done due to OpenAI Vision shrinking images for processing.
"""
import logging
import pyautogui as pag
import numpy as np


class OpenAIImageCoordinateTranslator:
    def __init__(self, original_width, original_height, quality='high'):
        """
        Initialize the ImageCoordinateTranslator class.

        Parameters:
        original_width (int): The original width of the image.
        original_height (int): The original height of the image.
        quality (str): The quality setting for resizing ('high' or 'low').

        This method sets up the original and resized dimensions, calculates scaling factors,
        and initializes logging.
        """
        self.original_width = original_width
        self.original_height = original_height
        self.quality = quality
        self.resized_width, self.resized_height = self.calculate_resized_dimensions()
        self.scale_x = self.original_width / self.resized_width
        self.scale_y = self.original_height / self.resized_height
        self.logger = logging.getLogger(__name__)

        self.logger.info(f"org_w: {self.original_width} and org_h: {self.original_height}")
        self.logger.info(f"resize_w: {self.resized_width} and resize_h: {self.resized_height}")

    def calculate_resized_dimensions(self):
        """
        Calculate the resized dimensions of the image based on the quality setting.

        This method maintains the aspect ratio of the original image while resizing.

        Returns:
        tuple: A tuple containing the resized width and height.
        """
        if self.quality == 'low':
            max_size = 512
        else:
            max_size = 2048

        # Fit within the specified max_size square
        max_dimension = max(self.original_width, self.original_height)
        if max_dimension > max_size:
            scale_factor = max_size / max_dimension
            temp_width = self.original_width * scale_factor
            temp_height = self.original_height * scale_factor
        else:
            temp_width = self.original_width
            temp_height = self.original_height

        # Scale the shortest side to 768 pixels for high quality
        if self.quality == 'high':
            min_dimension = min(temp_width, temp_height)
            scale_factor = 768 / min_dimension
            resized_width = temp_width * scale_factor
            resized_height = temp_height * scale_factor
        else:
            resized_width = temp_width
            resized_height = temp_height

        return resized_width, resized_height

    def translate_coordinates(self, resized_x: int, resized_y: int) -> tuple[int, int]:
        """
        Translate coordinates from the resized image to the original image dimensions.

        Parameters:
        resized_x (int): The x coordinate in the resized image.
        resized_y (int): The y coordinate in the resized image.

        Returns:
        tuple: A tuple containing the translated x and y coordinates in the original image.
        """
        self.logger.info(f"Translating coordinates x: {resized_x} y: {resized_y}")
        
        # Apply the scaling factors to map coordinates from resized to original image
        target_x = int(np.floor(resized_x * self.scale_x))
        target_y = int(np.floor(resized_y * self.scale_y))

        self.logger.info(f"Translated coordinates: x: {target_x} y: {target_y}")
        
        return target_x, target_y