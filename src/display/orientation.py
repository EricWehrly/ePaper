"""
Display Orientation Module

Handles display orientation configuration and dimension calculations
for the Waveshare 4inch e-Paper HAT+ (E).
"""

import logging

logger = logging.getLogger(__name__)

# Global display orientation configuration
SHORT_SIDE = 400
LONG_SIDE = 600
_IS_PORTRAIT = True  # Default orientation


def set_display_orientation(portrait_mode=True):
    """Set the global display orientation for all display operations."""
    global _IS_PORTRAIT
    _IS_PORTRAIT = portrait_mode
    orientation = "portrait" if _IS_PORTRAIT else "landscape"
    width = get_display_width()
    height = get_display_height()
    logger.info(f"Display orientation set to: {orientation} ({width}x{height})")


def get_display_orientation():
    """Get the current display orientation."""
    return _IS_PORTRAIT


def get_display_width():
    """Get the current display width based on orientation."""
    return SHORT_SIDE if _IS_PORTRAIT else LONG_SIDE


def get_display_height():
    """Get the current display height based on orientation."""
    return LONG_SIDE if _IS_PORTRAIT else SHORT_SIDE