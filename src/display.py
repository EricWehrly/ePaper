"""
Display Module - ePaper Display Interface

Provides an interface for controlling the Waveshare 4inch e-Paper HAT+ (E) display.
This module contains stubs for the main functionality to be implemented later.
"""

import sys
import logging
from pathlib import Path
from .path_utils import setup_project_paths, get_project_root

project_root = get_project_root()

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    Image = ImageDraw = ImageFont = None
    PIL_AVAILABLE = False

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
                logger.info("Display clear (stubbed)")
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
                logger.info(f"Display image (stubbed): {image_path.name}")
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
                logger.info(f"Display text (stubbed): {text}")
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
            # TODO: Why bother with this logger and encapsulating if condition?
            # Should just be a no-op when epd is none
            if self.epd is None:
                logger.info("Display sleep (stubbed)")
                return
                
            logger.info("Putting display to sleep...")
            self.epd.sleep()
            logger.info("Display is now in sleep mode")
            
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
            'blank_on_cleanup': self.blank_on_cleanup,
            'colors': ['BLACK', 'WHITE', 'YELLOW', 'RED', 'BLUE', 'GREEN'],
            'type': 'Waveshare 4inch e-Paper HAT+ (E)'
        }
        
    def test_display(self):
        """
        Test display functionality with built-in patterns.
        
        Raises:
            DisplayError: If test fails
        """
        try:
            if self.epd is None:
                logger.info("Display test (stubbed)")
                return
                
            if not PIL_AVAILABLE:
                raise DisplayError("PIL (Pillow) library not available for display test")
            
            import time
            
            logger.info("Running display test...")
            
            # Clear display first
            self.clear_display()
            time.sleep(1)
            
            # Create test image
            image = Image.new('RGB', (self.width, self.height), self.epd.WHITE)
            draw = ImageDraw.Draw(image)
            
            # Color test blocks (top section)
            colors = {
                'BLACK': self.epd.BLACK,
                'WHITE': self.epd.WHITE,
                'YELLOW': self.epd.YELLOW,
                'RED': self.epd.RED,
                'BLUE': self.epd.BLUE,
                'GREEN': self.epd.GREEN
            }
            
            block_width = self.width // 3
            block_height = 80
            
            x = 0
            y = 50
            for i, (name, color) in enumerate(colors.items()):
                if i > 0 and i % 3 == 0:
                    x = 0
                    y += block_height + 10
                    
                # Draw color block
                draw.rectangle([x, y, x + block_width - 5, y + block_height], fill=color)
                
                # Label (in contrasting color)
                label_color = self.epd.WHITE if color == self.epd.BLACK else self.epd.BLACK
                try:
                    font = ImageFont.load_default()
                    draw.text((x + 10, y + 10), name, font=font, fill=label_color)
                except:
                    pass
                    
                x += block_width
            
            # Test text (bottom section)
            try:
                font = ImageFont.load_default()
                test_texts = [
                    "ePaper Display Test",
                    f"Resolution: {self.width}x{self.height}",
                    "6-Color Support",
                    "Waveshare 4inch HAT+ (E)"
                ]
                
                text_y = y + block_height + 50
                for text in test_texts:
                    draw.text((20, text_y), text, font=font, fill=self.epd.BLACK)
                    text_y += 30
            except:
                pass
            
            # Draw simple geometric shapes
            # Rectangle outline
            draw.rectangle([20, text_y + 20, 180, text_y + 80], outline=self.epd.BLACK, width=2)
            
            # Filled circle (approximate with polygon)
            center_x, center_y = 100, text_y + 120
            radius = 30
            # Simple circle approximation
            draw.ellipse([center_x - radius, center_y - radius, 
                         center_x + radius, center_y + radius], 
                        fill=self.epd.BLUE, outline=self.epd.BLACK)
            
            # Display the test pattern
            self.epd.display(self.epd.getbuffer(image))
            logger.info("Display test pattern shown successfully")
            
        except Exception as e:
            logger.error(f"Display test failed: {e}")
            raise DisplayError(f"Display test failed: {e}")


# Convenience functions for simple operations
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


if __name__ == "__main__":
    # Test display functionality if run directly
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        display = DisplayManager()
        display.initialize()
        
        info = display.get_display_info()
        print(f"Display info: {info}")
        
        display.test_display()
        display.cleanup()
        
        print("Display test completed successfully (stub mode)")
        
    except DisplayError as e:
        print(f"Display test failed: {e}")
        sys.exit(1)