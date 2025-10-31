"""
Optimized conversion functions for performance testing.
"""

import logging
import numpy as np
from PIL import Image
from pathlib import Path
from src.convert.dithering import PALETTE_6COLOR, floyd_steinberg_dither
from src.convert.preprocessing import preprocess_image_for_epaper
from test.optimized_dithering import (
    floyd_steinberg_dither_optimized,
    floyd_steinberg_dither_ultra_optimized
)

logger = logging.getLogger(__name__)


def convert_to_6color_with_dithering_optimized(image):
    """
    Optimized version of 6-color conversion with dithering.
    
    Args:
        image: PIL Image object in RGB mode
        
    Returns:
        numpy array with palette indices for each pixel
    """
    # Convert to numpy array - use uint8 instead of float32 for initial conversion
    img_array = np.array(image, dtype=np.float32)
    
    # Apply Floyd-Steinberg dithering
    palette_indices = floyd_steinberg_dither(img_array, PALETTE_6COLOR)
    
    return palette_indices


def convert_image_to_6color_dithered_optimized(input_path, output_path):
    """
    Optimized version of image conversion function.
    
    Major optimizations:
    1. Vectorized palette mapping instead of nested loops
    2. Direct array manipulation instead of pixel-by-pixel operations
    3. More efficient PIL operations
    
    Args:
        input_path: Path to source image file (str or Path)
        output_path: Path for output BMP file (str or Path)
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        logger.info(f"Converting {input_path.name} to 6-color e-Paper format (optimized)")
        
        # Load and preprocess image
        try:
            with Image.open(input_path) as img:
                logger.info(f"Loaded image: {img.format} {img.size} {img.mode}")
                processed_img = preprocess_image_for_epaper(img)
        except Exception as e:
            logger.error(f"Failed to load image {input_path}: {e}")
            raise
            
        # Convert to 6-color palette with dithering
        palette_indices = convert_to_6color_with_dithering_optimized(processed_img)
        
        # OPTIMIZATION: Vectorized palette mapping instead of nested loops
        height, width = palette_indices.shape
        
        # Create palette as uint8 for efficiency
        palette_uint8 = PALETTE_6COLOR.astype(np.uint8)
        
        # Vectorized mapping: palette_indices -> RGB colors
        # This replaces the slow nested loop with a single numpy operation
        output_array = palette_uint8[palette_indices]  # Shape: (height, width, 3)
        
        # Create PIL image directly from array
        output_img = Image.fromarray(output_array, mode='RGB')
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as BMP
        output_img.save(output_path, format='BMP')
        logger.info(f"Successfully converted {input_path.name} to {output_path.name}")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert {input_path.name}: {e}")
        return False


def convert_image_to_6color_dithered_ultra_optimized(input_path, output_path):
    """
    Ultra-optimized version with optimized dithering algorithm.
    
    Uses optimized dithering that reduces function call overhead.
    
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
            
        # Convert using optimized dithering
        palette_indices = floyd_steinberg_dither_optimized(
            np.array(processed_img, dtype=np.float32), 
            PALETTE_6COLOR
        )
        
        # Vectorized conversion
        palette_uint8 = PALETTE_6COLOR.astype(np.uint8)
        output_array = palette_uint8[palette_indices]
        
        # Create and save image
        output_img = Image.fromarray(output_array, mode='RGB')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_img.save(output_path, format='BMP')
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert {input_path.name}: {e}")
        return False


def convert_image_to_6color_dithered_extreme_optimized(input_path, output_path):
    """
    Extreme optimization using manual distance calculations.
    
    Uses ultra-optimized dithering with manual distance calculations
    to minimize function call overhead in the hot loop.
    
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
            
        # Convert using ultra-optimized dithering
        palette_indices = floyd_steinberg_dither_ultra_optimized(
            np.array(processed_img, dtype=np.float32), 
            PALETTE_6COLOR
        )
        
        # Vectorized conversion
        palette_uint8 = PALETTE_6COLOR.astype(np.uint8)
        output_array = palette_uint8[palette_indices]
        
        # Create and save image
        output_img = Image.fromarray(output_array, mode='RGB')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_img.save(output_path, format='BMP')
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert {input_path.name}: {e}")
        return False