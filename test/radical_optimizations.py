"""
Multiple optimization strategies for dramatic performance improvement.
"""

import time
import numpy as np
from PIL import Image
import subprocess
import os
from pathlib import Path
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import tempfile

from src.convert.dithering import PALETTE_6COLOR
from src.convert.preprocessing import preprocess_image_for_epaper


def simple_nearest_color_conversion(input_path, output_path):
    """
    Strategy 1: Skip dithering entirely, use simple nearest-color mapping.
    Should be 50-100x faster but lower quality.
    """
    try:
        # Load and preprocess
        with Image.open(input_path) as img:
            processed_img = preprocess_image_for_epaper(img)
        
        # Convert to numpy
        img_array = np.array(processed_img, dtype=np.float32)
        height, width = img_array.shape[:2]
        
        # Reshape for vectorized distance calculation
        pixels = img_array.reshape(-1, 3)  # (N, 3)
        palette = PALETTE_6COLOR[None, :, :]  # (1, 6, 3)
        pixels_expanded = pixels[:, None, :]  # (N, 1, 3)
        
        # Vectorized distance calculation for all pixels at once
        distances = np.sum((pixels_expanded - palette) ** 2, axis=2)  # (N, 6)
        closest_indices = np.argmin(distances, axis=1)  # (N,)
        
        # Reshape back to image
        palette_indices = closest_indices.reshape(height, width)
        
        # Convert to RGB
        palette_uint8 = PALETTE_6COLOR.astype(np.uint8)
        output_array = palette_uint8[palette_indices]
        
        # Save
        output_img = Image.fromarray(output_array, mode='RGB')
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        output_img.save(output_path, format='BMP')
        
        return True
    except Exception as e:
        print(f"Simple conversion failed: {e}")
        return False


def ordered_dither_conversion(input_path, output_path):
    """
    Strategy 2: Use ordered (Bayer) dithering instead of Floyd-Steinberg.
    Parallelizable and much faster.
    """
    try:
        # Load and preprocess
        with Image.open(input_path) as img:
            processed_img = preprocess_image_for_epaper(img)
        
        img_array = np.array(processed_img, dtype=np.float32)
        height, width = img_array.shape[:2]
        
        # 4x4 Bayer dithering matrix (normalized to 0-1)
        bayer_4x4 = np.array([
            [0, 8, 2, 10],
            [12, 4, 14, 6], 
            [3, 11, 1, 9],
            [15, 7, 13, 5]
        ], dtype=np.float32) / 16.0
        
        # Create dithering threshold for each pixel
        bayer_tiled = np.tile(bayer_4x4, (height // 4 + 1, width // 4 + 1))[:height, :width]
        
        # Apply ordered dithering
        result_indices = np.zeros((height, width), dtype=np.uint8)
        
        for y in range(height):
            for x in range(width):
                pixel = img_array[y, x]
                threshold = bayer_tiled[y, x] * 64  # Scale threshold
                
                # Add dithering noise
                dithered_pixel = pixel + (threshold - 32)  # Center around 0
                dithered_pixel = np.clip(dithered_pixel, 0, 255)
                
                # Find closest color
                distances = np.sum((PALETTE_6COLOR - dithered_pixel) ** 2, axis=1)
                result_indices[y, x] = np.argmin(distances)
        
        # Convert to RGB and save
        palette_uint8 = PALETTE_6COLOR.astype(np.uint8)
        output_array = palette_uint8[result_indices]
        output_img = Image.fromarray(output_array, mode='RGB')
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        output_img.save(output_path, format='BMP')
        
        return True
    except Exception as e:
        print(f"Ordered dither failed: {e}")
        return False


def imagemagick_conversion(input_path, output_path):
    """
    Strategy 3: Use ImageMagick command line - might be much faster.
    """
    try:
        # Create custom palette file
        palette_path = Path("test/outputs/palette.png")
        palette_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create 1x6 palette image
        palette_img = Image.new('RGB', (6, 1))
        palette_colors = [(int(c[0]), int(c[1]), int(c[2])) for c in PALETTE_6COLOR]
        palette_img.putdata(palette_colors)
        palette_img.save(palette_path)
        
        # Use ImageMagick convert command with our palette
        cmd = [
            'convert', 
            str(input_path),
            '-resize', '400x600!',  # Force exact size
            '+dither',  # Try without dithering first for speed
            '-remap', str(palette_path),
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return True
        else:
            print(f"ImageMagick failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("ImageMagick timed out")
        return False
    except FileNotFoundError:
        print("ImageMagick not installed")
        return False
    except Exception as e:
        print(f"ImageMagick error: {e}")
        return False


def pil_quantize_conversion(input_path, output_path):
    """
    Strategy 4: Use PIL's built-in quantization with our palette.
    """
    try:
        # Load and preprocess
        with Image.open(input_path) as img:
            processed_img = preprocess_image_for_epaper(img)
        
        # Create palette image for PIL
        palette_img = Image.new('P', (1, 1))
        palette_colors = []
        for color in PALETTE_6COLOR:
            palette_colors.extend([int(color[0]), int(color[1]), int(color[2])])
        
        # Pad to 256 colors (PIL requirement)
        while len(palette_colors) < 768:  # 256 * 3
            palette_colors.extend([0, 0, 0])
        
        palette_img.putpalette(palette_colors)
        
        # Quantize using our palette
        quantized = processed_img.quantize(palette=palette_img, dither=Image.FLOYDSTEINBERG)
        
        # Convert back to RGB for consistent output
        quantized_rgb = quantized.convert('RGB')
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        quantized_rgb.save(output_path, format='BMP')
        
        return True
    except Exception as e:
        print(f"PIL quantize failed: {e}")
        return False


def lookup_table_conversion(input_path, output_path):
    """
    Strategy 5: Pre-computed lookup table for common RGB values.
    """
    try:
        # Load and preprocess
        with Image.open(input_path) as img:
            processed_img = preprocess_image_for_epaper(img)
        
        img_array = np.array(processed_img, dtype=np.uint8)
        height, width = img_array.shape[:2]
        
        # Create lookup table (simplified - sample every 8th value for speed)
        # This creates a 32x32x32 lookup table
        lut = np.zeros((32, 32, 32), dtype=np.uint8)
        
        for r in range(32):
            for g in range(32):
                for b in range(32):
                    rgb = np.array([r * 8, g * 8, b * 8], dtype=np.float32)
                    distances = np.sum((PALETTE_6COLOR - rgb) ** 2, axis=1)
                    lut[r, g, b] = np.argmin(distances)
        
        # Convert image using lookup table
        r_idx = img_array[:, :, 0] // 8
        g_idx = img_array[:, :, 1] // 8  
        b_idx = img_array[:, :, 2] // 8
        
        # Clamp to valid range
        r_idx = np.clip(r_idx, 0, 31)
        g_idx = np.clip(g_idx, 0, 31)
        b_idx = np.clip(b_idx, 0, 31)
        
        palette_indices = lut[r_idx, g_idx, b_idx]
        
        # Convert to RGB and save
        palette_uint8 = PALETTE_6COLOR.astype(np.uint8)
        output_array = palette_uint8[palette_indices]
        output_img = Image.fromarray(output_array, mode='RGB')
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        output_img.save(output_path, format='BMP')
        
        return True
    except Exception as e:
        print(f"Lookup table conversion failed: {e}")
        return False