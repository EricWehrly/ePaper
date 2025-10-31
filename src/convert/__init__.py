"""
Convert Package - Enhanced Image Conversion with Floyd-Steinberg Dithering

Provides modular image conversion functionality for e-Paper displays with
6-color palette support and dithering algorithms. The package is organized
into separate modules for extensibility:

- core: Main conversion functions and image-to-BMP conversion
- dithering: Floyd-Steinberg dithering algorithm and color palette management
- preprocessing: Image preparation and resizing for e-Paper displays
- batch: Batch processing operations and comparison utilities

This module exposes the main public API for conversion operations.
"""

from .core import convert_image_to_6color_dithered
from .batch import convert_images_batch, convert_image_comparison
from .preprocessing import preprocess_image_for_epaper, resize_image_to_display
from .dithering import PALETTE_6COLOR, find_closest_palette_color, floyd_steinberg_dither

__all__ = [
    # Core conversion functions
    'convert_image_to_6color_dithered', 
    
    # Batch processing
    'convert_images_batch',
    'convert_image_comparison',
    
    # Preprocessing utilities
    'preprocess_image_for_epaper',
    'resize_image_to_display',
    
    # Dithering and palette
    'PALETTE_6COLOR',
    'find_closest_palette_color',
    'floyd_steinberg_dither'
]


# Removed __main__ block - use cli.py convert command instead