"""
Core Conversion Module

Main image conversion functions for 6-color e-Paper display format.
"""

import logging
import numpy as np
from PIL import Image
from pathlib import Path
from .dithering import PALETTE_6COLOR, floyd_steinberg_dither
from .preprocessing import preprocess_image_for_epaper

logger = logging.getLogger(__name__)


def convert_to_6color_with_dithering(image):
    """
    Convert PIL image to 6-color palette using Floyd-Steinberg dithering.
    
    Args:
        image: PIL Image object in RGB mode
        
    Returns:
        numpy array with palette indices for each pixel
    """
    # Convert to numpy array with float32 for better precision
    img_array = np.array(image, dtype=np.float32)
    
    # Apply Floyd-Steinberg dithering
    palette_indices = floyd_steinberg_dither(img_array, PALETTE_6COLOR)
    
    return palette_indices


def convert_image_to_6color_dithered(input_path, output_path):
    """
    Convert an image file to 6-color BMP format using Floyd-Steinberg dithering.
    
    Args:
        input_path: Path to source image file (str or Path)
        output_path: Path for output BMP file (str or Path)
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        # Load and preprocess image
        with Image.open(input_path) as img:
            processed_img = preprocess_image_for_epaper(img)
            
            # Convert to 6-color palette with dithering
            palette_indices = convert_to_6color_with_dithering(processed_img)
            
            # Create output image with palette colors
            height, width = palette_indices.shape
            output_img = Image.new('RGB', (width, height))
            output_pixels = []
            
            for row in palette_indices:
                for pixel_idx in row:
                    # Map palette index to RGB color
                    if pixel_idx < len(PALETTE_6COLOR):
                        rgb = tuple(PALETTE_6COLOR[pixel_idx].astype(np.uint8))
                    else:
                        rgb = (255, 255, 255)  # Default to white
                    output_pixels.append(rgb)
            
            output_img.putdata(output_pixels)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save as BMP
            output_img.save(output_path, format='BMP')
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert {input_path}: {e}")
        return False