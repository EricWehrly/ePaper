"""
Image Conversion Module

Converts images to 6-color palette format suitable for the Waveshare e-Paper display.
Now uses Floyd-Steinberg dithering for much better image quality.
"""

import logging
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
from pathlib import Path

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

# Target display resolution
DISPLAY_WIDTH = 400
DISPLAY_HEIGHT = 600


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
    
    # Floyd-Steinberg error diffusion
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


def preprocess_image_for_epaper(image):
    """
    Preprocess image to optimize for e-paper display characteristics.
    
    Args:
        image: PIL Image object
        
    Returns:
        PIL Image optimized for e-paper
    """
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize to display resolution with good resampling
    image = resize_image_to_display(image)
    
    # Enhance contrast slightly for better e-paper visibility
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)
    
    # Enhance saturation to make colors more distinct
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.3)
    
    # Slight sharpening to counteract e-paper softness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.1)
    
    return image


def resize_image_to_display(image):
    """
    Resize image to fit the display resolution while maintaining aspect ratio.
    
    Args:
        image: PIL Image object
        
    Returns:
        PIL Image resized to display dimensions
    """
    # Calculate aspect ratios
    img_aspect = image.width / image.height
    display_aspect = DISPLAY_WIDTH / DISPLAY_HEIGHT
    
    if img_aspect > display_aspect:
        # Image is wider - fit to width
        new_width = DISPLAY_WIDTH
        new_height = int(DISPLAY_WIDTH / img_aspect)
    else:
        # Image is taller - fit to height
        new_height = DISPLAY_HEIGHT
        new_width = int(DISPLAY_HEIGHT * img_aspect)
    
    # Resize image
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create new image with display dimensions and paste resized image centered
    final_image = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), (255, 255, 255))
    
    # Calculate position to center the image
    x_offset = (DISPLAY_WIDTH - new_width) // 2
    y_offset = (DISPLAY_HEIGHT - new_height) // 2
    
    final_image.paste(resized, (x_offset, y_offset))
    
    return final_image


def convert_to_6color_palette(image):
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


def pack_palette_data(palette_indices):
    """
    Pack palette indices into bytes for display (2 pixels per byte).
    
    Args:
        palette_indices: 2D numpy array of palette indices
        
    Returns:
        bytes object with packed pixel data
    """
    height, width = palette_indices.shape
    
    # Ensure width is even for packing
    if width % 2 != 0:
        logger.warning(f"Width {width} is odd, padding with one column")
        # Pad with white pixels (index 1)
        palette_indices = np.pad(palette_indices, ((0, 0), (0, 1)), constant_values=1)
        width += 1
    
    packed_data = []
    
    for row in palette_indices:
        for i in range(0, width, 2):
            # Pack two pixels into one byte (first pixel in upper 4 bits)
            pixel1 = row[i]
            pixel2 = row[i + 1] if i + 1 < width else 1  # Default to white if odd width
            
            packed_byte = (pixel1 << 4) | pixel2
            packed_data.append(packed_byte)
    
    return bytes(packed_data)


def convert_image_to_6color(input_path, output_path):
    """
    Convert an image file to 6-color BMP format for e-paper display.
    
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
            # Preprocess for e-paper optimization
            processed_img = preprocess_image_for_epaper(img)
            
            # Convert to 6-color palette with dithering
            palette_indices = convert_to_6color_palette(processed_img)
            
            # Create output image with palette colors for visualization
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


def convert_image_to_display_data(input_path):
    """
    Convert image directly to packed display data.
    
    TODO: Support bytestream input in addition to file paths
    
    Args:
        input_path: Path to source image file (str or Path)
        
    Returns:
        bytes: Packed pixel data for e-paper display, or None if failed
    """
    try:
        input_path = Path(input_path)
        
        # Load and process image
        with Image.open(input_path) as img:
            processed_img = preprocess_image_for_epaper(img)
            palette_indices = convert_to_6color_palette(processed_img)
            
            # Pack into display format
            packed_data = pack_palette_data(palette_indices)
            
        return packed_data
        
    except Exception as e:
        logger.error(f"Failed to convert {input_path} to display data: {e}")
        return None


# TODO: Add support for bytestream input
def convert_bytestream_to_6color(image_data, output_path):
    """
    Convert image from bytestream to 6-color BMP format.
    
    TODO: Implement this method for direct memory processing
    
    Args:
        image_data: Raw image data as bytes
        output_path: Path for output BMP file (str or Path)
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    logger.warning("convert_bytestream_to_6color not yet implemented")
    return False


if __name__ == "__main__":
    # Test conversion if run directly
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python convert.py <input_image> <output_bmp>")
        sys.exit(1)
        
    success = convert_image_to_6color(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)