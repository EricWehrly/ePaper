"""
Image Preprocessing Module

Handles image preparation and resizing for e-Paper display conversion.
"""

import logging
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)


def preprocess_image_for_epaper(image):
    """
    Preprocess image to optimize for e-paper display characteristics.
    
    Current defaults (October 2025 optimization):
    - Enhanced contrast: 1.3x (reduces washed-out appearance)
    - Enhanced color saturation: 1.3x (makes colors more distinct) 
    - Slight sharpening: 1.1x (counteracts e-paper softness)
    
    Legacy settings (pre-optimization): Basic resize only
    See docs/LEGACY_CONVERSION_SETTINGS.md for historical reference
    
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
    
    # NEW DEFAULT: Enhanced contrast for better e-paper visibility 
    # (Updated from 1.2x to 1.3x based on visual testing)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.3)
    
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
    from ..display import get_display_width, get_display_height
    
    display_width = get_display_width()
    display_height = get_display_height()

    # TODO: Account for whether we should rotate images
    # (e.g. if image is landscape but display is portrait, we should rotate the image to match)
    # For now, just do this to align longer sides (display is currently set to > height, so portrait mode)
    # But we want to allow the display to be set for either presentation orientation,
    # And the user to choose whether to auto-rotate images to fit or not.

    # Calculate aspect ratios
    img_aspect = image.width / image.height
    display_aspect = display_width / display_height
    
    if img_aspect > display_aspect:
        # Image is wider - fit to width
        new_width = display_width
        new_height = int(display_width / img_aspect)
    else:
        # Image is taller - fit to height
        new_height = display_height
        new_width = int(display_height * img_aspect)
    
    # Resize image with high-quality resampling
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create new image with display dimensions and paste resized image centered
    final_image = Image.new('RGB', (display_width, display_height), (255, 255, 255))
    
    # Calculate position to center the image
    x_offset = (display_width - new_width) // 2
    y_offset = (display_height - new_height) // 2
    
    final_image.paste(resized, (x_offset, y_offset))
    
    return final_image