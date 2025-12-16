#!/usr/bin/env python3
"""
Reconvert all images using the current best conversion method.
This ensures all images use the latest optimized conversion algorithm.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.convert.core import convert_image_to_6color_dithered
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.heic'}

def reconvert_all_images():
    """Reconvert all images in pic-raw/ to pic/ using current best method"""
    
    source_dir = project_root / 'pic-raw'
    output_dir = project_root / 'pic'
    
    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        return
    
    output_dir.mkdir(exist_ok=True)
    
    # Get all source images
    source_images = []
    for ext in SUPPORTED_EXTENSIONS:
        source_images.extend(source_dir.glob(f'*{ext}'))
        source_images.extend(source_dir.glob(f'*{ext.upper()}'))
    
    if not source_images:
        logger.warning(f"No images found in {source_dir}")
        return
    
    logger.info(f"Found {len(source_images)} images to convert")
    logger.info("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for idx, source_path in enumerate(sorted(source_images), 1):
        output_path = output_dir / f"{source_path.stem}.bmp"
        
        logger.info(f"[{idx}/{len(source_images)}] Converting {source_path.name}...")
        
        try:
            success = convert_image_to_6color_dithered(source_path, output_path)
            if success:
                success_count += 1
                logger.info(f"  ✓ Saved to {output_path.name}")
            else:
                fail_count += 1
                logger.error(f"  ✗ Conversion failed")
        except Exception as e:
            fail_count += 1
            logger.error(f"  ✗ Error: {e}")
    
    logger.info("=" * 60)
    logger.info(f"Conversion complete!")
    logger.info(f"  Success: {success_count}")
    logger.info(f"  Failed:  {fail_count}")
    logger.info(f"  Total:   {len(source_images)}")

if __name__ == '__main__':
    reconvert_all_images()
