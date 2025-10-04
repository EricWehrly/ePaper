"""
Utility functions for scoring modules.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def find_original_image(converted_path: Path) -> Optional[Path]:
    """Find the original image that corresponds to a converted BMP file."""
    # Extract base name (remove _dithered.bmp suffix)
    base_name = converted_path.stem.replace('_dithered', '').replace('_simple', '')
    
    # Look in pic-raw directory for PNG or JPG versions
    # Handle different directory structures
    if 'test' in str(converted_path):
        # Test output directory - go up to project root
        # test/outputs/dithering_comparison -> go up 3 levels to project root
        pic_raw_dir = converted_path.parent.parent.parent.parent / 'pic-raw'
    else:
        # Regular pic directory - go up one level then to pic-raw
        pic_raw_dir = converted_path.parent.parent / 'pic-raw'
    
    for ext in ['.png', '.jpg', '.jpeg']:
        original_path = pic_raw_dir / f"{base_name}{ext}"
        if original_path.exists():
            return original_path
            
    return None