"""
Dithering Module

Implements Floyd-Steinberg dithering algorithm and color palette management
for e-Paper display conversion.
"""

import logging
import numpy as np

logger = logging.getLogger(__name__)

# 6-color palette matching the e-Paper display capabilities
# Colors: BLACK, WHITE, YELLOW, RED, BLUE, GREEN
PALETTE_6COLOR = np.array([
    [0, 0, 0],        # BLACK
    [255, 255, 255],  # WHITE  
    [255, 243, 56],   # YELLOW
    [191, 0, 0],      # RED
    [100, 64, 255],   # BLUE
    [67, 138, 28],    # GREEN
], dtype=np.float32)


def find_closest_palette_color(rgb_color):
    """
    Find the closest color in the 6-color palette using Euclidean distance.
    
    Args:
        rgb_color: RGB color as [r, g, b] array (float32)
        
    Returns:
        tuple: (closest_index, closest_color_rgb)
    """
    # Calculate squared euclidean distance to each palette color
    diff = PALETTE_6COLOR - rgb_color
    distances = np.sum(diff * diff, axis=1)
    
    # Find the index with minimum distance
    closest_idx = np.argmin(distances)
    
    return closest_idx, PALETTE_6COLOR[closest_idx]


def floyd_steinberg_dither(image_array, palette):
    """
    Apply Floyd-Steinberg dithering to an RGB image array.
    
    The Floyd-Steinberg algorithm propagates quantization errors to neighboring
    pixels, creating the illusion of intermediate colors and smooth gradients
    even with a limited palette.
    
    Args:
        image_array: numpy array of shape (height, width, 3) with float32 RGB values
        palette: numpy array of available colors
        
    Returns:
        numpy array of palette indices for each pixel
    """
    height, width = image_array.shape[:2]
    
    # Create a working copy with padding for error diffusion
    working_image = np.pad(image_array, ((0, 1), (1, 1), (0, 0)), mode='edge')
    
    # Output array for palette indices
    result_indices = np.zeros((height, width), dtype=np.uint8)
    
    # Floyd-Steinberg error diffusion matrix
    # Distributes error to: [right, bottom-left, bottom, bottom-right]
    # with weights: [7/16, 3/16, 5/16, 1/16]
    
    for y in range(height):
        for x in range(width):
            # Get current pixel (accounting for padding)
            old_pixel = working_image[y, x + 1].copy()
            
            # Find closest palette color
            closest_idx, new_pixel = find_closest_palette_color(old_pixel)
            result_indices[y, x] = closest_idx
            
            # Calculate quantization error
            error = old_pixel - new_pixel
            
            # Distribute error to neighboring pixels
            # Right pixel (x+1, y)
            if x + 1 < width:
                working_image[y, x + 2] += error * (7/16)
            
            # Bottom-left pixel (x-1, y+1) 
            if y + 1 < height and x > 0:
                working_image[y + 1, x] += error * (3/16)
            
            # Bottom pixel (x, y+1)
            if y + 1 < height:
                working_image[y + 1, x + 1] += error * (5/16)
            
            # Bottom-right pixel (x+1, y+1)
            if y + 1 < height and x + 1 < width:
                working_image[y + 1, x + 2] += error * (1/16)
    
    return result_indices