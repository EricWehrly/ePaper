"""
Batch Processing Module

Handles batch conversion operations and comparison functions.
"""

import logging
import numpy as np
from PIL import Image
from pathlib import Path
from .dithering import PALETTE_6COLOR, find_closest_palette_color
from .preprocessing import preprocess_image_for_epaper
from .core import convert_to_6color_with_dithering, convert_image_to_6color_dithered

logger = logging.getLogger(__name__)


def convert_image_comparison(input_path, output_dir):
    """
    Create comparison images showing original vs simple vs dithered conversion.
    
    Args:
        input_path: Path to source image
        output_dir: Directory to save comparison images
        
    Returns:
        dict: Paths to generated comparison images
    """
    try:
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        stem = input_path.stem
        
        # Original approach (simple nearest color)
        simple_output = output_dir / f"{stem}_simple.bmp"
        
        # Enhanced approach (Floyd-Steinberg dithering) 
        dithered_output = output_dir / f"{stem}_dithered.bmp"
        
        # Load image once
        with Image.open(input_path) as img:
            processed_img = preprocess_image_for_epaper(img)
            
            # Simple conversion (old method)
            img_array = np.array(processed_img)
            height, width = img_array.shape[:2]
            pixels = img_array.reshape(-1, 3)
            
            simple_indices = np.array([find_closest_palette_color(pixel.astype(np.float32))[0] 
                                     for pixel in pixels])
            simple_indices = simple_indices.reshape(height, width)
            
            # Create simple output
            simple_img = Image.new('RGB', (width, height))
            simple_pixels = []
            for row in simple_indices:
                for pixel_idx in row:
                    rgb = tuple(PALETTE_6COLOR[pixel_idx].astype(np.uint8))
                    simple_pixels.append(rgb)
            simple_img.putdata(simple_pixels)
            simple_img.save(simple_output, format='BMP')
            
            # Dithered conversion (new method)
            dithered_indices = convert_to_6color_with_dithering(processed_img)
            
            dithered_img = Image.new('RGB', (width, height))
            dithered_pixels = []
            for row in dithered_indices:
                for pixel_idx in row:
                    rgb = tuple(PALETTE_6COLOR[pixel_idx].astype(np.uint8))
                    dithered_pixels.append(rgb)
            dithered_img.putdata(dithered_pixels)
            dithered_img.save(dithered_output, format='BMP')
        
        return {
            'simple': simple_output,
            'dithered': dithered_output
        }
        
    except Exception as e:
        logger.error(f"Failed to create comparison for {input_path}: {e}")
        return {}


# TODO: Set up visual comparison test between JPG and PNG source formats
#       to determine if there are quality differences in conversion
# TODO: Make duplicate display conditional - may want to show both formats
#       in the future for comparison purposes
def convert_images_batch(source_dir, output_dir, supported_extensions, filesystem_module):
    """
    Convert a batch of images from source directory to output directory.
    
    Handles the complete workflow:
    1. Scan source directory for images (via filesystem module)
    2. Convert images to 6-color format with deduplication
    3. Return list of successfully converted image paths
    
    Args:
        source_dir: Path to source directory containing images
        output_dir: Path to output directory for converted BMPs  
        supported_extensions: Set of supported file extensions (e.g., {'.png', '.jpg', '.jpeg'})
        filesystem_module: Reference to filesystem module for directory scanning
        
    Returns:
        list: Paths to successfully converted BMP files
    """
    try:
        # Use filesystem module to scan for source images
        source_images = filesystem_module.scan_directory(
            source_dir, 
            extensions=supported_extensions
        )
        
        if not source_images:
            logger.warning("No source images found in directory scanning")
            return []
            
        logger.info(f"Found {len(source_images)} source images to process")
        
        converted_images = []
        converted_names = set()  # Track unique output filenames to avoid duplicates
        
        for source_path in source_images:
            try:
                # Generate output filename (stem + .bmp)
                output_filename = source_path.stem + '.bmp'
                output_path = output_dir / output_filename
                
                # Skip if we've already processed this output filename
                # This prevents duplicate display when both .jpg and .png exist
                if output_filename in converted_names:
                    logger.debug(f"Skipping duplicate output: {output_filename} (from {source_path.name})")
                    continue
                
                # Skip if already converted and up to date (using filesystem module)
                if filesystem_module.is_file_newer(output_path, source_path):
                    converted_images.append(output_path)
                    converted_names.add(output_filename)
                    logger.debug(f"Using existing up-to-date conversion: {output_filename}")
                    continue
                    
                # Convert image using dithered conversion
                success = convert_image_to_6color_dithered(
                    str(source_path), 
                    str(output_path)
                )
                
                if success:
                    converted_images.append(output_path)
                    converted_names.add(output_filename)
                    logger.info(f"Converted {source_path.name} -> {output_filename}")
                else:
                    logger.error(f"Failed to convert {source_path.name}")
                    
            except Exception as e:
                logger.error(f"Error converting {source_path.name}: {e}")
        
        logger.info(f"Successfully converted {len(converted_images)} unique images")        
        return converted_images
        
    except Exception as e:
        logger.error(f"Batch conversion failed: {e}")
        return []