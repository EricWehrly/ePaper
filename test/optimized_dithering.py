"""
Highly optimized dithering implementation.
"""

import numpy as np
from src.convert.dithering import PALETTE_6COLOR


def find_closest_palette_color_vectorized(rgb_colors, palette):
    """
    Vectorized version of palette color finding.
    
    Args:
        rgb_colors: Array of RGB colors, shape (..., 3)
        palette: Palette array, shape (N, 3)
        
    Returns:
        Array of closest palette indices
    """
    # Reshape inputs for broadcasting
    colors = rgb_colors.reshape(-1, 1, 3)  # (pixels, 1, 3)
    palette_expanded = palette[None, :, :]  # (1, palette_size, 3)
    
    # Calculate squared distances using broadcasting
    diff = colors - palette_expanded  # (pixels, palette_size, 3)
    distances = np.sum(diff * diff, axis=2)  # (pixels, palette_size)
    
    # Find closest indices
    closest_indices = np.argmin(distances, axis=1)
    
    return closest_indices.reshape(rgb_colors.shape[:-1])


def floyd_steinberg_dither_optimized(image_array, palette):
    """
    Optimized Floyd-Steinberg dithering with vectorized palette lookup.
    
    Key optimizations:
    1. Pre-compute some operations outside the loop
    2. Use more efficient array operations
    3. Minimize memory allocations in the hot loop
    
    Args:
        image_array: numpy array of shape (height, width, 3) with float32 RGB values
        palette: numpy array of available colors
        
    Returns:
        numpy array of palette indices for each pixel
    """
    height, width = image_array.shape[:2]
    
    # Create a working copy with padding for error diffusion
    working_image = np.pad(image_array, ((0, 1), (1, 1), (0, 0)), mode='edge').copy()
    
    # Output array for palette indices
    result_indices = np.zeros((height, width), dtype=np.uint8)
    
    # Pre-compute error diffusion weights
    error_weights = np.array([7/16, 3/16, 5/16, 1/16])
    
    for y in range(height):
        for x in range(width):
            # Get current pixel (accounting for padding)
            old_pixel = working_image[y, x + 1]
            
            # Find closest palette color using vectorized function
            # For single pixel, we still need the loop structure for error propagation
            colors_reshaped = old_pixel.reshape(1, 3)
            closest_idx = find_closest_palette_color_vectorized(colors_reshaped, palette)[0]
            new_pixel = palette[closest_idx]
            
            result_indices[y, x] = closest_idx
            
            # Calculate quantization error
            error = old_pixel - new_pixel
            
            # Distribute error to neighboring pixels (unrolled for speed)
            # Right pixel (x+1, y)
            if x + 1 < width:
                working_image[y, x + 2] += error * error_weights[0]
            
            # Bottom-left pixel (x-1, y+1) 
            if y + 1 < height and x > 0:
                working_image[y + 1, x] += error * error_weights[1]
            
            # Bottom pixel (x, y+1)
            if y + 1 < height:
                working_image[y + 1, x + 1] += error * error_weights[2]
            
            # Bottom-right pixel (x+1, y+1)
            if y + 1 < height and x + 1 < width:
                working_image[y + 1, x + 2] += error * error_weights[3]
    
    return result_indices


def floyd_steinberg_dither_ultra_optimized(image_array, palette):
    """
    Ultra-optimized dithering using numba-style optimizations without numba.
    
    Key optimizations:
    1. Minimize function calls in hot loops
    2. Pre-compute distance lookup table for common colors
    3. Use fastest possible array access patterns
    
    Args:
        image_array: numpy array of shape (height, width, 3) with float32 RGB values
        palette: numpy array of available colors
        
    Returns:
        numpy array of palette indices for each pixel
    """
    height, width = image_array.shape[:2]
    
    # Create working copy
    working_image = np.pad(image_array, ((0, 1), (1, 1), (0, 0)), mode='edge').copy()
    result_indices = np.zeros((height, width), dtype=np.uint8)
    
    # Pre-compute palette for fast access (convert to regular Python arrays for speed)
    palette_list = [tuple(color) for color in palette]
    
    # Error weights as constants
    ERR_RIGHT = 7/16
    ERR_BOTTOM_LEFT = 3/16  
    ERR_BOTTOM = 5/16
    ERR_BOTTOM_RIGHT = 1/16
    
    for y in range(height):
        for x in range(width):
            # Get pixel values directly
            old_r, old_g, old_b = working_image[y, x + 1]
            
            # Manual distance calculation (faster than vectorized for single pixel)
            min_dist = float('inf')
            closest_idx = 0
            
            for i, (pal_r, pal_g, pal_b) in enumerate(palette_list):
                dist = (old_r - pal_r)**2 + (old_g - pal_g)**2 + (old_b - pal_b)**2
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i
            
            result_indices[y, x] = closest_idx
            
            # Get new pixel color
            new_r, new_g, new_b = palette[closest_idx]
            
            # Calculate errors
            err_r = old_r - new_r
            err_g = old_g - new_g 
            err_b = old_b - new_b
            
            # Distribute errors with manual bounds checking
            # Right pixel
            if x + 1 < width:
                working_image[y, x + 2, 0] += err_r * ERR_RIGHT
                working_image[y, x + 2, 1] += err_g * ERR_RIGHT
                working_image[y, x + 2, 2] += err_b * ERR_RIGHT
            
            # Bottom row pixels
            if y + 1 < height:
                # Bottom-left
                if x > 0:
                    working_image[y + 1, x, 0] += err_r * ERR_BOTTOM_LEFT
                    working_image[y + 1, x, 1] += err_g * ERR_BOTTOM_LEFT
                    working_image[y + 1, x, 2] += err_b * ERR_BOTTOM_LEFT
                
                # Bottom
                working_image[y + 1, x + 1, 0] += err_r * ERR_BOTTOM
                working_image[y + 1, x + 1, 1] += err_g * ERR_BOTTOM
                working_image[y + 1, x + 1, 2] += err_b * ERR_BOTTOM
                
                # Bottom-right
                if x + 1 < width:
                    working_image[y + 1, x + 2, 0] += err_r * ERR_BOTTOM_RIGHT
                    working_image[y + 1, x + 2, 1] += err_g * ERR_BOTTOM_RIGHT
                    working_image[y + 1, x + 2, 2] += err_b * ERR_BOTTOM_RIGHT
    
    return result_indices