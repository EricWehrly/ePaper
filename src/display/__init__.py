"""
Display Package - ePaper Display Interface

Provides a modular interface for controlling the Waveshare 4inch e-Paper HAT+ (E) display.
The package is organized into separate modules for extensibility:

- manager: Main DisplayManager class and DisplayError exception
- orientation: Display orientation configuration and dimension utilities  
- convenience: Quick one-shot display functions

This module exposes the main public API for display operations.
"""

from .manager import DisplayManager, DisplayError
from .orientation import (
    set_display_orientation, 
    get_display_orientation,
    get_display_width,
    get_display_height
)
from .convenience import quick_display_image, quick_display_text

__all__ = [
    # Main classes and exceptions
    'DisplayManager', 
    'DisplayError',
    
    # Orientation functions
    'set_display_orientation',
    'get_display_orientation', 
    'get_display_width',
    'get_display_height',
    
    # Convenience functions
    'quick_display_image',
    'quick_display_text'
]