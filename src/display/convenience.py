"""
Display Convenience Functions

Provides simple one-shot functions for quick display operations
without needing to manage DisplayManager instances.
"""

import logging
from .manager import DisplayManager, DisplayError

logger = logging.getLogger(__name__)


def quick_display_image(image_path):
    """
    Quickly display an image without managing DisplayManager instance.
    
    Args:
        image_path: Path to image file to display
        
    Returns:
        bool: True if successful
    """
    try:
        display = DisplayManager()
        display.initialize()
        display.show_image(image_path)
        display.cleanup()
        return True
        
    except DisplayError as e:
        logger.error(f"Quick display failed: {e}")
        return False


def quick_display_text(text, position=(10, 10), font_size=24):
    """
    Quickly display text without managing DisplayManager instance.
    
    Args:
        text: Text to display
        position: (x, y) position for text
        font_size: Font size to use
        
    Returns:
        bool: True if successful
    """
    try:
        display = DisplayManager()
        display.initialize()
        display.show_text(text, position, font_size)
        display.cleanup()
        return True
        
    except DisplayError as e:
        logger.error(f"Quick text display failed: {e}")
        return False