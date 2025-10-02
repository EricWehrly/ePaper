"""
Enhanced Image Conversion Module with Floyd-Steinberg Dithering

Implements Floyd-Steinberg dithering algorithm for much better image quality
on e-Paper displays with limited color palettes.
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
    
    # Resize image with high-quality resampling
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create new image with display dimensions and paste resized image centered
    final_image = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), (255, 255, 255))
    
    # Calculate position to center the image
    x_offset = (DISPLAY_WIDTH - new_width) // 2
    y_offset = (DISPLAY_HEIGHT - new_height) // 2
    
    final_image.paste(resized, (x_offset, y_offset))
    
    return final_image


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


# Update the main conversion function to use dithering by default
def convert_image_to_6color(input_path, output_path):
    """
    Convert an image using the enhanced Floyd-Steinberg dithering method.
    
    This replaces the original simple conversion method.
    """
    return convert_image_to_6color_dithered(input_path, output_path)


if __name__ == "__main__":
    # Test conversion with comparison if run directly
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python enhanced_convert.py <input_image> [output_dir]")
        print("  Creates both simple and dithered versions for comparison")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "comparison_output"
    
    print(f"Creating comparison conversions for: {input_file}")
    
    results = convert_image_comparison(input_file, output_dir)
    
    if results:
        print(f"✅ Conversion complete!")
        print(f"   Simple: {results['simple']}")
        print(f"   Dithered: {results['dithered']}")
        print(f"\\n💡 Compare the results:")
        print(f"   feh {results['simple']} {results['dithered']}")
    else:
        print("❌ Conversion failed")
        sys.exit(1)