"""
Structural similarity scoring for ePaper images.
"""

import logging
import numpy as np
from PIL import Image
from pathlib import Path

logger = logging.getLogger(__name__)


def calculate_structural_similarity(original_path: Path, converted_path: Path) -> float:
    """Calculate structural similarity between original and converted images."""
    try:
        with Image.open(original_path) as orig, Image.open(converted_path) as conv:
            # Resize original to match converted (400x600)
            orig_resized = orig.resize((400, 600), Image.Resampling.LANCZOS)
            
            # Convert both to grayscale for structural comparison
            orig_gray = np.array(orig_resized.convert('L'), dtype=np.float32)
            conv_gray = np.array(conv.convert('L'), dtype=np.float32)
            
            # Calculate mean squared error
            mse = np.mean((orig_gray - conv_gray) ** 2)
            
            # Convert MSE to penalty score (0-100 scale)
            # MSE of 0 = perfect match, MSE of 10000+ = very different
            penalty = min(mse / 100, 100)
            
            return penalty
            
    except Exception as e:
        logger.error(f"Error calculating structural similarity: {e}")
        return 100
