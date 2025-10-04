"""
Color fidelity scoring for ePaper images.
"""

import logging
from PIL import Image, ImageStat
from pathlib import Path

logger = logging.getLogger(__name__)


def calculate_color_fidelity_score(original_path: Path, converted_path: Path) -> float:
    """Score how well the converted image preserves the original's color characteristics."""
    try:
        with Image.open(original_path) as orig, Image.open(converted_path) as conv:
            # Resize original to match converted
            orig_resized = orig.resize((400, 600), Image.Resampling.LANCZOS)
            
            # Get color statistics
            orig_stat = ImageStat.Stat(orig_resized)
            conv_stat = ImageStat.Stat(conv)
            
            # Compare mean brightness across RGB channels
            orig_means = orig_stat.mean[:3] if len(orig_stat.mean) >= 3 else orig_stat.mean
            conv_means = conv_stat.mean[:3] if len(conv_stat.mean) >= 3 else conv_stat.mean
            
            # Calculate difference in mean values
            mean_diff = sum(abs(o - c) for o, c in zip(orig_means, conv_means)) / len(orig_means)
            
            # Convert to penalty score (0-100 scale)
            penalty = min(mean_diff / 2.55, 100)  # Normalize to 0-100
            
            return penalty
            
    except Exception as e:
        logger.error(f"Error calculating color fidelity: {e}")
        return 100
