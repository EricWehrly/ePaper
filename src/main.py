#!/usr/bin/env python3
"""
ePaper Display Main Program

This program orchestrates the ePaper display workflow:
1. Scan for source images in pic-raw/
2. Convert them to 6-color format and save to pic/
3. Cycle through converted images on the e-paper display
4. Handle graceful shutdown on Ctrl+C
"""

import sys
import os
import signal
import logging
import time
from pathlib import Path

# Add the project root to Python path to import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'lib'))

from src import convert, filesystem, display

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ePaperController:
    """Main controller for the ePaper display program"""
    
    def __init__(self):
        self.running = True
        self.display_manager = None
        
        # Directory paths
        self.source_dir = project_root / 'pic-raw'
        self.output_dir = project_root / 'pic'
        
        # Supported image extensions
        self.supported_extensions = {'.png', '.jpg', '.jpeg'}
        
        # Display timing
        self.display_interval = 3.0  # seconds between images
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Shutdown requested, finishing current operation...")
        self.running = False
        
    def initialize_display(self):
        """Initialize the e-paper display"""
        try:
            self.display_manager = display.DisplayManager()
            self.display_manager.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize display: {e}")
            return False
        return True
        
    def scan_and_convert_images(self):
        """Scan source directory and convert images to display format"""
        source_images = filesystem.scan_directory(
            self.source_dir, 
            extensions=self.supported_extensions
        )
        
        if not source_images:
            logger.warning("No source images found")
            return []
            
        logger.info(f"Converting {len(source_images)} images...")
        
        converted_images = []
        
        for source_path in source_images:
            try:
                # Generate output filename
                output_filename = source_path.stem + '.bmp'
                output_path = self.output_dir / output_filename
                
                # Skip if already converted and up to date
                if filesystem.is_file_newer(output_path, source_path):
                    converted_images.append(output_path)
                    continue
                    
                # Convert image
                success = convert.convert_image_to_6color(
                    str(source_path), 
                    str(output_path)
                )
                
                if success:
                    converted_images.append(output_path)
                else:
                    logger.error(f"Failed to convert {source_path.name}")
                    
            except Exception as e:
                logger.error(f"Error converting {source_path.name}: {e}")
                
        return converted_images
        
    def display_cycle(self, image_paths):
        """Cycle through images on the display"""
        if not image_paths:
            logger.warning("No images to display")
            return
            
        logger.info(f"Displaying {len(image_paths)} images...")
        
        for image_path in image_paths:
            if not self.running:
                break
                
            try:
                self.display_manager.show_image(str(image_path))
                
                # Wait between images (with interrupt check)
                start_time = time.time()
                while time.time() - start_time < self.display_interval:
                    if not self.running:
                        break
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error displaying {image_path.name}: {e}")
        
    def shutdown(self):
        """Perform cleanup and shutdown"""
        if self.display_manager:
            try:
                self.display_manager.cleanup()
            except Exception as e:
                logger.error(f"Error during display cleanup: {e}")
        
    def run(self):
        """Main program loop"""
        try:
            self.setup_signal_handlers()
            
            # Ensure directories exist
            filesystem.ensure_directory(self.source_dir)
            filesystem.ensure_directory(self.output_dir)
            
            # Initialize display
            if not self.initialize_display():
                return 1
                
            # Main workflow
            converted_images = self.scan_and_convert_images()
            
            if converted_images and self.running:
                self.display_cycle(converted_images)
                
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return 1
            
        finally:
            self.shutdown()
            
        return 0


def main():
    """Entry point"""
    controller = ePaperController()
    exit_code = controller.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()