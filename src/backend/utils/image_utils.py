from concurrent.futures import ThreadPoolExecutor

import csv
import cv2
import math
import numpy as np
from PIL import Image

from backend.config import SAMPLE_RES_SCALE


def merge_images_collage(image_paths, margin=5, scale=1.0):
    """
    Merges images into a square-shaped collage efficiently using multithreading.

    Args:
        image_paths (list): A list of image file paths.
        margin (int, optional): Margin between images in pixels. Defaults to 5.
        scale (float, optional): Scale factor for resizing images. Defaults to 1.0.

    Returns:
        Image.Image: The merged collage image, or None if no valid images are found.
    """

    def load_and_scale_image(img_path):
        """Loads and scales an image, handling potential errors."""
        try:
            img = Image.open(img_path)
            if scale != 1.0:
                img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
            return img
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")
            return None

    with ThreadPoolExecutor() as executor:
        images = list(executor.map(load_and_scale_image, image_paths))

    images = [img for img in images if img is not None]

    if not images:
        print("Error: No valid images found for collage.")
        return None

    num_images = len(images)
    grid_size = math.ceil(math.sqrt(num_images))

    max_width = max(img.size[0] for img in images)
    max_height = max(img.size[1] for img in images)

    merged_image_size = ((max_width + margin) * grid_size - margin,
                         (max_height + margin) * grid_size - margin)
    merged_image = Image.new('RGBA', merged_image_size)

    for index, img in enumerate(images):
        x_offset = (index % grid_size) * (max_width + margin)
        y_offset = (index // grid_size) * (max_height + margin)
        merged_image.paste(img, (x_offset, y_offset))

    return merged_image


import cv2
import numpy as np

def enhance_mask_visualization(image, mask, opacity=0.5, contour_color=(0, 255, 0), fill_color=(0, 0, 255), scale_factor=SAMPLE_RES_SCALE):
    """
    Enhance the visualization of a segmentation mask on an image with optional resolution scaling.

    Args:
    image (np.array): The original image (in RGB format).
    mask (np.array): The binary segmentation mask.
    opacity (float): The opacity of the mask overlay (0-1).
    contour_color (tuple): The color of the contour (in BGR format).
    fill_color (tuple): The color to fill the mask (in BGR format).
    scale_factor (float): The factor by which to scale the image resolution (e.g., 0.5 for half resolution).

    Returns:
    np.array: The enhanced image with the mask overlay.
    """
    # Ensure the image and mask have the same dimensions
    if image.shape[:2] != mask.shape:
        image = cv2.resize(image, (mask.shape[1], mask.shape[0]))

    # Downscale the image if scale_factor < 1
    if scale_factor != 1.0:
        small_image = cv2.resize(image, (int(image.shape[1] * scale_factor), int(image.shape[0] * scale_factor)))
    else:
        small_image = image

    # Create a colored mask
    colored_mask = np.zeros((*mask.shape, 3), dtype=np.uint8)
    colored_mask[mask > 0] = fill_color

    # Resize the colored mask if scale_factor < 1
    if scale_factor != 1.0:
        small_colored_mask = cv2.resize(colored_mask, (small_image.shape[1], small_image.shape[0]))
    else:
        small_colored_mask = colored_mask

    # Find contours on the small mask
    small_mask = cv2.resize(mask.astype(np.uint8), (small_image.shape[1], small_image.shape[0]))
    contours, _ = cv2.findContours(small_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create a blended image
    blended = cv2.addWeighted(small_image, 1, small_colored_mask, opacity, 0)

    # Draw contours on the blended image
    cv2.drawContours(blended, contours, -1, contour_color, 2)

    # Upscale the blended image back to the original size if scale_factor < 1
    if scale_factor != 1.0:
        blended = cv2.resize(blended, (image.shape[1], image.shape[0]))

    return blended


def combine_image_and_mask(image, mask, **kwargs):
    """
    Combine an image and its segmentation mask into an enhanced visualization.

    Args:
    image (np.array or str): The original image or path to the image file.
    mask (np.array): The binary segmentation mask.
    **kwargs: Additional arguments to pass to enhance_mask_visualization function.

    Returns:
    np.array: The combined image with enhanced mask visualization.
    """
    # Load the image if a file path is provided
    if isinstance(image, str):
        image = cv2.imread(image)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Convert image to RGB before any processing with PIL (or other libraries if necessary)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Ensure the mask is binary
    mask = (mask > 0).astype(np.uint8) * 255

    # Enhance the mask visualization
    return enhance_mask_visualization(image, mask, **kwargs)

