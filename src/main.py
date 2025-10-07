#!/usr/bin/env python3
"""
ePaper Display Main Program

This program orchestrates the ePaper display workflow in two modes:

Standalone Mode:
1. Scan for source images in pic-raw/
2. Convert them to 6-color format and save to pic/
3. Cycle through converted images on the e-paper display
4. Handle graceful shutdown on Ctrl+C

Web Server Mode:
1. Initialize the ePaper controller
2. Start a Flask web server for API-based control
3. Provide REST endpoints for remote display management
"""

import sys
import os
import signal
import logging
import time
import argparse
from pathlib import Path

# Setup project paths for imports
from src.path_utils import setup_project_paths, get_project_root
setup_project_paths()

from src import convert, filesystem, display
from src.scoring import sort_images_by_quality
from src.web import start_server

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
        
        # Display orientation - set via display module
        # Portrait: 400x600 (tall), Landscape: 600x400 (wide)  
        # Default to portrait mode (can be changed via set_orientation)
        display.set_display_orientation(portrait_mode=True)
        
        # Directory paths
        project_root = get_project_root()
        self.source_dir = project_root / 'pic-raw'
        self.output_dir = project_root / 'pic'
        
        # Supported image extensions
        self.supported_extensions = {'.png', '.jpg', '.jpeg'}
        
        # Display timing
        # TODO: 22 in "release" build, 2 in "demo / test" mode ...
        self.display_interval = 2.0  # seconds between images
    
    def set_orientation(self, portrait_mode):
        """
        Set display orientation. Note: This should be called before initialize_display().
        
        Args:
            portrait_mode: True for portrait (400x600), False for landscape (600x400)
        """
        display.set_display_orientation(portrait_mode)
        
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
        orientation_str = "portrait" if display.get_display_orientation() else "landscape"
        logger.info(f"Converting images for {orientation_str} display orientation")
        
        converted_images = convert.convert_images_batch(
            source_dir=self.source_dir,
            output_dir=self.output_dir,
            supported_extensions=self.supported_extensions,
            filesystem_module=filesystem
        )
        
        return converted_images
        
    def display_cycle(self, image_paths):
        """Cycle through images on the display"""
        if not image_paths:
            logger.warning("No images to display")
            return
            
        # Sort images by quality score (best first)
        sorted_images = sort_images_by_quality(image_paths)
            
        logger.info(f"Displaying {len(sorted_images)} images in quality order...")
        
        for image_path in sorted_images:
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
        
    def run_standalone(self):
        """Run in standalone mode - convert and display images in a loop"""
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
    
    def run_web_server(self, host='0.0.0.0', port=5000, debug=False):
        """Run in web server mode - provide API endpoints for remote control"""
        try:
            self.setup_signal_handlers()
            
            # Ensure directories exist
            filesystem.ensure_directory(self.source_dir)
            filesystem.ensure_directory(self.output_dir)
            
            # Initialize display (but don't fail if it's not available)
            display_initialized = self.initialize_display()
            if not display_initialized:
                logger.warning("Display initialization failed - web server will run with limited functionality")
            
            # Start web server (this will block until shutdown)
            start_server(
                epaper_controller=self,
                host=host,
                port=port,
                debug=debug
            )
                
        except Exception as e:
            logger.error(f"Web server error: {e}")
            return 1
            
        finally:
            self.shutdown()
            
        return 0


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description='ePaper Display Controller')
    parser.add_argument(
        '--mode', 
        choices=['standalone', 'web'], 
        default='web',
        help='Run mode: standalone (direct display cycle) or web (API server) - default: web'
    )
    parser.add_argument(
        '--host', 
        default='0.0.0.0',
        help='Host address for web server (web mode only) - default: 0.0.0.0'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=5000,
        help='Port for web server (web mode only) - default: 5000'
    )
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug mode for web server (web mode only)'
    )
    parser.add_argument(
        '--portrait', 
        action='store_true', 
        default=True,
        help='Use portrait orientation (400x600) - default: True'
    )
    parser.add_argument(
        '--landscape', 
        action='store_true',
        help='Use landscape orientation (600x400)'
    )
    
    args = parser.parse_args()
    
    # Create controller
    controller = ePaperController()
    
    # Set orientation
    portrait_mode = not args.landscape  # Default to portrait unless --landscape is specified
    controller.set_orientation(portrait_mode)
    
    # Run in specified mode
    if args.mode == 'standalone':
        logger.info("Starting in standalone mode")
        exit_code = controller.run_standalone()
    else:  # web mode
        logger.info(f"Starting web server on {args.host}:{args.port}")
        exit_code = controller.run_web_server(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()