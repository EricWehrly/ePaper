"""
Edge/detail preservation scoring for ePaper images.
"""

import logging
import numpy as np
from PIL import Image, ImageFilter
from pathlib import Path

logger = logging.getLogger(__name__)


def calculate_edge_preservation_score(original_path: Path, converted_path: Path) -> float:
    """Score how well edges and details are preserved in the conversion."""
    try:
        with Image.open(original_path) as orig, Image.open(converted_path) as conv:
            # Resize original to match converted
            orig_resized = orig.resize((400, 600), Image.Resampling.LANCZOS)
            
            # Apply edge detection to both images
            orig_edges = orig_resized.convert('L').filter(ImageFilter.FIND_EDGES)
            conv_edges = conv.convert('L').filter(ImageFilter.FIND_EDGES)
            
            # Convert to numpy arrays
            orig_edge_array = np.array(orig_edges, dtype=np.float32)
            conv_edge_array = np.array(conv_edges, dtype=np.float32)
            
            # Calculate correlation between edge maps
            # Higher correlation = better edge preservation
            orig_flat = orig_edge_array.flatten()
            conv_flat = conv_edge_array.flatten()
            
            # Avoid division by zero
            if np.std(orig_flat) == 0 or np.std(conv_flat) == 0:
                return 50  # Moderate penalty for flat images
            
            correlation = np.corrcoef(orig_flat, conv_flat)[0, 1]
            
            # Convert correlation to penalty (1.0 correlation = 0 penalty)
            penalty = (1.0 - max(correlation, 0)) * 100
            
            return penalty
            
    except Exception as e:
        logger.error(f"Error calculating edge preservation: {e}")
        return 100
