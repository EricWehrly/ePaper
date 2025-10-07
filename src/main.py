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
        # Path to the currently displayed image (str) or None
        self.current_image = None
        # Container to hold server instance when running web server
        self._server_container = None
        
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
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except Exception as e:
            # Signals may only be set from the main thread; if we're not in main thread
            # just log a warning and continue. This makes the method safe to call from
            # background threads during tests or programmatic usage.
            logger.warning(f"Unable to set signal handlers (not main thread?): {e}")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Shutdown requested, finishing current operation...")
        self.running = False
        # If we have a WSGI server, request it to shutdown immediately to avoid hangs
        try:
            if self._server_container and isinstance(self._server_container, dict):
                srv = self._server_container.get('server')
                if srv:
                    try:
                        srv.shutdown()
                    except Exception:
                        pass
        except Exception:
            pass
        
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
                # Use helper to show and track current image
                self.show_image(str(image_path))
                
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

        # Reset current image on shutdown
        self.current_image = None

    def show_image(self, image_path):
        """Show an image on the display and update current_image state.

        This centralizes tracking so the web UI can report the active image.
        """
        if not self.display_manager:
            raise RuntimeError("Display manager not initialized")

        self.display_manager.show_image(image_path)
        # Store the path (string) for status reporting
        self.current_image = image_path
        
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
        self._web_mode = True
        try:
            self.setup_signal_handlers()
            
            # Ensure directories exist
            filesystem.ensure_directory(self.source_dir)
            filesystem.ensure_directory(self.output_dir)
            
            # Initialize display (but don't fail if it's not available)
            display_initialized = self.initialize_display()
            if not display_initialized:
                logger.warning("Display initialization failed - web server will run with limited functionality")
            else:
                # In web mode we prefer to preserve the display content on shutdown
                # to avoid long blocking blank operations. Make cleanup best-effort.
                try:
                    self.display_manager.blank_on_cleanup = False
                except Exception:
                    pass
            
            # Start web server in a background thread so we can handle signals
            import threading
            server_container = {}
            # remember server container so signal handler can access it
            self._server_container = server_container
            server_thread = threading.Thread(
                target=start_server,
                kwargs={"epaper_controller": self, "host": host, "port": port, "debug": debug, "server_container": server_container},
                daemon=True,
            )
            server_thread.start()

            # Main loop: wait until running becomes False (e.g., via signal or API)
            import requests
            # If bound to all interfaces, use localhost for shutdown request
            shutdown_host = '127.0.0.1' if host in ('0.0.0.0', '::') else host
            server_base = f'http://{shutdown_host}:{port}'
            while self.running:
                time.sleep(0.2)

            # Shutdown the WSGI server if we captured it
            srv = server_container.get('server') if 'server_container' in locals() else None
            if srv:
                try:
                    srv.shutdown()
                except Exception:
                    pass

            # Wait briefly for thread to exit
            server_thread.join(timeout=5)
                
        except Exception as e:
            logger.error(f"Web server error: {e}")
            return 1
            
        finally:
            # Perform cleanup asynchronously to avoid blocking shutdown (e.g., long display blanking)
            try:
                import threading
                cleanup_thread = threading.Thread(target=self.shutdown, daemon=True)
                cleanup_thread.start()
            except Exception:
                # Fallback to synchronous cleanup if thread creation fails
                try:
                    self.shutdown()
                except Exception:
                    pass

            self._web_mode = False
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