"""
Skin tone detection and scoring for ePaper images.
"""

import logging
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


def is_skin_tone(rgb_pixel, skin_tone_ranges):
    """Check if a pixel color represents a skin tone."""
    r, g, b = rgb_pixel[:3]  # Handle both RGB and RGBA
    
    for (min_rgb, max_rgb) in skin_tone_ranges:
        min_r, min_g, min_b = min_rgb
        max_r, max_g, max_b = max_rgb
        
        if (min_r <= r <= max_r and 
            min_g <= g <= max_g and 
            min_b <= b <= max_b):
            return True
    return False


def calculate_skin_tone_score(original_path: Path, converted_path: Path) -> Dict[str, float]:
    """Calculate skin tone preservation score and surface area coverage."""
    
    # Define skin tone ranges in RGB for detecting people in photos
    skin_tone_ranges = [
        # Light skin tones
        ([180, 120, 90], [255, 200, 170]),
        # Medium skin tones  
        ([120, 80, 50], [200, 140, 100]),
        # Darker skin tones
        ([70, 50, 30], [140, 100, 80]),
    ]
    
    try:
        with Image.open(original_path) as orig, Image.open(converted_path) as conv:
            # Resize original to match converted (400x600)
            orig_resized = orig.resize((400, 600), Image.Resampling.LANCZOS)
            
            # Convert to numpy arrays
            orig_array = np.array(orig_resized)
            conv_array = np.array(conv)
            
            # Find skin tone pixels in original
            orig_flat = orig_array.reshape(-1, 3)
            skin_mask = np.array([is_skin_tone(pixel, skin_tone_ranges) for pixel in orig_flat])
            
            total_pixels = len(orig_flat)
            skin_pixels = np.sum(skin_mask)
            
            if skin_pixels == 0:
                # No skin tones detected
                return {
                    'skin_tone_score': 0,
                    'skin_coverage_percent': 0,
                    'weighted_skin_score': 0
                }
            
            skin_coverage_percent = (skin_pixels / total_pixels) * 100
            
            # Get original and converted skin tone pixels
            conv_flat = conv_array.reshape(-1, 3)
            orig_skin_pixels = orig_flat[skin_mask]
            conv_skin_pixels = conv_flat[skin_mask]
            
            # Calculate MSE for skin tone areas only
            skin_mse = np.mean((orig_skin_pixels.astype(float) - conv_skin_pixels.astype(float)) ** 2)
            
            # Convert MSE to penalty score (0-100 scale)
            skin_tone_score = min(skin_mse / 100, 100)
            
            # Weight the score by coverage area - more coverage = more important
            coverage_weight = min(skin_coverage_percent / 10, 5)  # Cap at 5x weight
            weighted_skin_score = skin_tone_score * (1 + coverage_weight)
            
            return {
                'skin_tone_score': round(skin_tone_score, 2),
                'skin_coverage_percent': round(skin_coverage_percent, 2), 
                'weighted_skin_score': round(weighted_skin_score, 2)
            }
            
    except Exception as e:
        logger.error(f"Error calculating skin tone score: {e}")
        return {
            'skin_tone_score': 100,
            'skin_coverage_percent': 0,
            'weighted_skin_score': 100
        }
