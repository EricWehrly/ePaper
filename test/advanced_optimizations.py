"""
Advanced optimization strategies including JIT compilation.
"""

import numpy as np
from PIL import Image
from pathlib import Path
from src.convert.dithering import PALETTE_6COLOR
from src.convert.preprocessing import preprocess_image_for_epaper

# Try to use Numba if available
try:
    from numba import jit, prange
    HAS_NUMBA = True
    
    @jit(nopython=True, parallel=True)
    def numba_floyd_steinberg(img_array, palette):
        """Numba-optimized Floyd-Steinberg dithering."""
        height, width = img_array.shape[:2]
        working_image = np.pad(img_array, ((0, 1), (1, 1), (0, 0)), mode='constant').copy()
        result_indices = np.zeros((height, width), dtype=np.uint8)
        
        for y in range(height):
            for x in range(width):
                old_pixel = working_image[y, x + 1].copy()
                
                # Find closest palette color
                min_dist = np.inf
                closest_idx = 0
                for i in range(len(palette)):
                    dist = np.sum((old_pixel - palette[i]) ** 2)
                    if dist < min_dist:
                        min_dist = dist
                        closest_idx = i
                
                result_indices[y, x] = closest_idx
                new_pixel = palette[closest_idx]
                error = old_pixel - new_pixel
                
                # Distribute error
                if x + 1 < width:
                    working_image[y, x + 2] += error * (7.0/16.0)
                if y + 1 < height and x > 0:
                    working_image[y + 1, x] += error * (3.0/16.0)
                if y + 1 < height:
                    working_image[y + 1, x + 1] += error * (5.0/16.0)
                if y + 1 < height and x + 1 < width:
                    working_image[y + 1, x + 2] += error * (1.0/16.0)
        
        return result_indices
    
except ImportError:
    HAS_NUMBA = False
    numba_floyd_steinberg = None


def pil_quantize_with_dithering(input_path, output_path):
    """
    Use PIL quantize but with Floyd-Steinberg dithering enabled.
    """
    try:
        with Image.open(input_path) as img:
            processed_img = preprocess_image_for_epaper(img)
        
        # Create palette image
        palette_img = Image.new('P', (1, 1))
        palette_colors = []
        for color in PALETTE_6COLOR:
            palette_colors.extend([int(color[0]), int(color[1]), int(color[2])])
        
        # Pad to 256 colors
        while len(palette_colors) < 768:
            palette_colors.extend([0, 0, 0])
        
        palette_img.putpalette(palette_colors)
        
        # Use Floyd-Steinberg dithering
        quantized = processed_img.quantize(palette=palette_img, dither=Image.FLOYDSTEINBERG)
        quantized_rgb = quantized.convert('RGB')
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        quantized_rgb.save(output_path, format='BMP')
        
        return True
    except Exception as e:
        print(f"PIL quantize with dithering failed: {e}")
        return False


def numba_conversion(input_path, output_path):
    """
    Use Numba JIT-compiled Floyd-Steinberg dithering.
    """
    if not HAS_NUMBA:
        print("Numba not available")
        return False
    
    try:
        with Image.open(input_path) as img:
            processed_img = preprocess_image_for_epaper(img)
        
        img_array = np.array(processed_img, dtype=np.float32)
        
        # Use numba-optimized dithering
        palette_indices = numba_floyd_steinberg(img_array, PALETTE_6COLOR)
        
        # Convert to RGB
        palette_uint8 = PALETTE_6COLOR.astype(np.uint8)
        output_array = palette_uint8[palette_indices]
        output_img = Image.fromarray(output_array, mode='RGB')
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        output_img.save(output_path, format='BMP')
        
        return True
    except Exception as e:
        print(f"Numba conversion failed: {e}")
        return False


def optimized_imagemagick_with_dithering(input_path, output_path):
    """
    ImageMagick with Floyd-Steinberg dithering enabled.
    """
    import subprocess
    
    try:
        # Create palette file
        palette_path = Path("test/outputs/palette.png")
        palette_path.parent.mkdir(parents=True, exist_ok=True)
        
        palette_img = Image.new('RGB', (6, 1))
        palette_colors = [(int(c[0]), int(c[1]), int(c[2])) for c in PALETTE_6COLOR]
        palette_img.putdata(palette_colors)
        palette_img.save(palette_path)
        
        # Use ImageMagick with dithering
        cmd = [
            'convert', 
            str(input_path),
            '-resize', '400x600!',
            '-dither', 'FloydSteinberg',  # Enable dithering
            '-remap', str(palette_path),
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0
        
    except Exception as e:
        print(f"ImageMagick with dithering failed: {e}")
        return False


def hybrid_approach(input_path, output_path):
    """
    Hybrid: Use PIL quantize for speed but post-process for quality.
    """
    try:
        # Fast initial conversion with PIL
        with Image.open(input_path) as img:
            processed_img = preprocess_image_for_epaper(img)
        
        # Quick quantization first
        palette_img = Image.new('P', (1, 1))
        palette_colors = []
        for color in PALETTE_6COLOR:
            palette_colors.extend([int(color[0]), int(color[1]), int(color[2])])
        while len(palette_colors) < 768:
            palette_colors.extend([0, 0, 0])
        palette_img.putpalette(palette_colors)
        
        # Fast quantization without dithering
        quantized = processed_img.quantize(palette=palette_img, dither=Image.NONE)
        quantized_rgb = quantized.convert('RGB')
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        quantized_rgb.save(output_path, format='BMP')
        
        return True
    except Exception as e:
        print(f"Hybrid approach failed: {e}")
        return False