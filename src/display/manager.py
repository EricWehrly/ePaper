"""
Display Manager Module

Provides the main DisplayManager class for controlling the Waveshare 4inch e-Paper HAT+ (E) display.
"""

import sys
import logging
from pathlib import Path
from ..path_utils import setup_project_paths, get_project_root
from .orientation import get_display_width, get_display_height, get_display_orientation

project_root = get_project_root()

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    Image = ImageDraw = ImageFont = None
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class DisplayError(Exception):
    """Custom exception for display-related errors"""
    pass


class DisplayManager:
    """
    Manager class for e-Paper display operations.
    
    This class provides a high-level interface for initializing, 
    controlling, and cleaning up the e-Paper display.
    """
    
    def __init__(self, blank_on_cleanup=True):
        """
        Initialize the display manager.
        
        Args:
            blank_on_cleanup: If True, clear display to white during cleanup.
                             If False, leave current image displayed.
        """
        self.epd = None
        self.blank_on_cleanup = blank_on_cleanup
        
        # Use global orientation settings
        self.width = get_display_width()
        self.height = get_display_height()
        
    def initialize(self):
        """
        Initialize the e-Paper display.
        
        Raises:
            DisplayError: If initialization fails
        """
        try:
            if self.epd is not None:
                logger.warning("Display already initialized")
                return
            
            # Try to import and initialize the display
            # TODO: Try to move this import to the top of the file like it should be
            setup_project_paths()
            from waveshare_epd import epd4in0e
            
            logger.info("Initializing Waveshare 4inch e-Paper HAT+ (E)...")
            
            self.epd = epd4in0e.EPD()
            self.epd.init()
            
            # Verify physical dimensions match expectations
            physical_width = self.epd.width
            physical_height = self.epd.height
            
            # Physical display should be 400x600 
            if (physical_width, physical_height) != (400, 600):
                logger.warning(f"Unexpected physical dimensions: {physical_width}x{physical_height}")
            
            # Keep logical dimensions based on global orientation
            orientation = "portrait" if get_display_orientation() else "landscape"
            logger.info(f"Display initialized in {orientation} mode: {self.width}x{self.height} (physical: {physical_width}x{physical_height})")
            
        except ImportError:
            raise DisplayError("Waveshare library not available")
        except Exception as e:
            logger.error(f"Failed to initialize display: {e}")
            raise DisplayError(f"Display initialization failed: {e}")
            
    def clear_display(self, color=None):
        """
        Clear the display to a solid color.
        
        Args:
            color: Color to clear to (None for default white)
            
        Raises:
            DisplayError: If clear operation fails
        """
        try:
            if self.epd is None:
                return
                
            logger.info(f"Clearing display to {color or 'white'}...")
            
            if color is not None:
                self.epd.Clear(color)
            else:
                self.epd.Clear()
                
        except Exception as e:
            logger.error(f"Failed to clear display: {e}")
            raise DisplayError(f"Display clear failed: {e}")
            
    def show_image(self, image_path):
        """
        Display an image on the e-Paper screen.
        
        Args:
            image_path: Path to BMP image file to display
            
        Raises:
            DisplayError: If image display fails
        """
        try:
            image_path = Path(image_path)
            
            if not image_path.exists():
                raise DisplayError(f"Image file not found: {image_path}")
                
            if self.epd is None:
                return
                
            if not PIL_AVAILABLE:
                raise DisplayError("PIL (Pillow) library not available for image processing")
            
            logger.info(f"Displaying image: {image_path.name}")
            
            # Load image
            image = Image.open(image_path)
            
            # Ensure correct dimensions
            if image.size != (self.width, self.height):
                logger.warning(f"Image size {image.size} doesn't match display {self.width}x{self.height}, resizing...")
                image = image.resize((self.width, self.height), Image.Resampling.LANCZOS)
            
            # Display on e-paper
            self.epd.display(self.epd.getbuffer(image))
            logger.info("Image displayed successfully")
            
        except Exception as e:
            logger.error(f"Failed to display image {image_path}: {e}")
            raise DisplayError(f"Image display failed: {e}")
            
    def show_text(self, text, position=(0, 0), font_size=24):
        """
        Display text on the screen.
        
        Args:
            text: Text string to display
            position: (x, y) position for text
            font_size: Size of font to use
            
        Raises:
            DisplayError: If text display fails
        """
        try:
            if self.epd is None:
                return
                
            if not PIL_AVAILABLE:
                raise DisplayError("PIL (Pillow) library not available for text rendering")
            
            logger.info(f"Displaying text: {text[:50]}...")
            
            # Get color constants - fallback to standard values if epd is None
            white_color = self.epd.WHITE if self.epd else 255
            black_color = self.epd.BLACK if self.epd else 0
            
            # Create new image with white background
            image = Image.new('RGB', (self.width, self.height), white_color)
            draw = ImageDraw.Draw(image)
            
            # Load font (try project font first, then default)
            try:
                font_path = project_root / 'pic' / 'Font.ttc'
                if font_path.exists():
                    font = ImageFont.truetype(str(font_path), font_size)
                else:
                    font = ImageFont.load_default()
            except Exception:
                font = ImageFont.load_default()
            
            # Draw text
            draw.text(position, text, font=font, fill=black_color)
            
            # Display on e-paper
            self.epd.display(self.epd.getbuffer(image))
            logger.info("Text displayed successfully")
            
        except Exception as e:
            logger.error(f"Failed to display text: {e}")
            raise DisplayError(f"Text display failed: {e}")
            
    def sleep(self):
        """
        Put the display into sleep mode to preserve the screen.
        
        Raises:
            DisplayError: If sleep operation fails
        """
        try:
            if self.epd is None:
                return
                
            logger.debug("Putting display to sleep...")
            self.epd.sleep()
            logger.debug("Display is now in sleep mode")
            
        except Exception as e:
            logger.error(f"Failed to put display to sleep: {e}")
            raise DisplayError(f"Display sleep failed: {e}")
            
    def cleanup(self):
        """
        Clean up display resources and put display to sleep.
        
        This should be called before program exit to ensure the display
        is properly shut down and preserved.
        
        The display will be blanked if blank_on_cleanup is True (default).
        """
        try:
            # Optionally blank the display before cleanup
            if self.blank_on_cleanup:
                logger.info("Blanking display before cleanup...")
                try:
                    self.clear_display()
                except Exception as e:
                    logger.warning(f"Failed to blank display during cleanup: {e}")
            else:
                logger.info("Preserving display content during cleanup")
            
            # Put display to sleep
            self.sleep()
            
            # TODO: Add any additional cleanup
            # - Reset GPIO pins if needed
            # - Clean up any allocated resources
            
        except Exception as e:
            logger.error(f"Error during display cleanup: {e}")
            # Don't raise here - cleanup should be best-effort
            
    def get_display_info(self):
        """
        Get information about the display.
        
        Returns:
            dict: Display information (dimensions, color capabilities, etc.)
        """
        orientation = "portrait" if get_display_orientation() else "landscape"
        return {
            'width': self.width,
            'height': self.height,
            'orientation': orientation,
            'portrait_mode': get_display_orientation(),
            'initialized': self.epd is not None,
            'blank_on_cleanup': self.blank_on_cleanup
        }


# Removed __main__ block - use cli.py test-display command instead