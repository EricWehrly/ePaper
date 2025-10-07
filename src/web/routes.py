"""
API routes for ePaper display control

Defines REST endpoints for interacting with the ePaper display system,
including image management, display control, and status monitoring.
"""

import logging
import json
from pathlib import Path
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)

def register_routes(app):
    """Register all API routes with the Flask app"""
    
    @app.route('/api/status', methods=['GET'])
    def get_status():
        """Get current system status"""
        try:
            controller = current_app.epaper_controller
            if not controller:
                return jsonify({"error": "Controller not initialized"}), 500
                
            return jsonify({
                "status": "running" if controller.running else "stopped",
                "display_initialized": controller.display_manager is not None,
                "source_dir": str(controller.source_dir),
                "output_dir": str(controller.output_dir),
                "display_interval": controller.display_interval
            })
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/images', methods=['GET'])
    def list_images():
        """List available images in pic-raw and pic directories"""
        try:
            controller = current_app.epaper_controller
            if not controller:
                return jsonify({"error": "Controller not initialized"}), 500
                
            # Get source images
            source_images = []
            if controller.source_dir.exists():
                for ext in controller.supported_extensions:
                    source_images.extend([
                        {"name": f.name, "path": str(f), "type": "source"}
                        for f in controller.source_dir.glob(f"*{ext}")
                    ])
            
            # Get converted images
            converted_images = []
            if controller.output_dir.exists():
                converted_images = [
                    {"name": f.name, "path": str(f), "type": "converted"}
                    for f in controller.output_dir.glob("*.bmp")
                ]
                
            return jsonify({
                "source_images": source_images,
                "converted_images": converted_images,
                "total_source": len(source_images),
                "total_converted": len(converted_images)
            })
        except Exception as e:
            logger.error(f"Image listing failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/display/image', methods=['POST'])
    def display_image():
        """Display a specific image on the ePaper display"""
        try:
            controller = current_app.epaper_controller
            if not controller:
                return jsonify({"error": "Controller not initialized"}), 500
                
            if not controller.display_manager:
                return jsonify({"error": "Display not initialized"}), 500
                
            data = request.get_json()
            if not data or 'image_path' not in data:
                return jsonify({"error": "image_path required"}), 400
                
            image_path = Path(data['image_path'])
            if not image_path.exists():
                return jsonify({"error": "Image file not found"}), 404
                
            controller.display_manager.show_image(str(image_path))
            return jsonify({"success": True, "displayed_image": str(image_path)})
            
        except Exception as e:
            logger.error(f"Display image failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/display/cycle', methods=['POST'])
    def start_display_cycle():
        """Start cycling through available images"""
        try:
            controller = current_app.epaper_controller
            if not controller:
                return jsonify({"error": "Controller not initialized"}), 500
                
            if not controller.display_manager:
                return jsonify({"error": "Display not initialized"}), 500
                
            # Get available converted images
            converted_images = []
            if controller.output_dir.exists():
                converted_images = list(controller.output_dir.glob("*.bmp"))
                
            if not converted_images:
                return jsonify({"error": "No converted images available"}), 400
                
            # Note: This will run the cycle synchronously
            # In a production system, you might want to run this in a background thread
            controller.display_cycle(converted_images)
            
            return jsonify({
                "success": True,
                "images_displayed": len(converted_images)
            })
            
        except Exception as e:
            logger.error(f"Display cycle failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/convert', methods=['POST'])
    def convert_images():
        """Convert source images to display format"""
        try:
            controller = current_app.epaper_controller
            if not controller:
                return jsonify({"error": "Controller not initialized"}), 500
                
            converted_images = controller.scan_and_convert_images()
            
            return jsonify({
                "success": True,
                "converted_count": len(converted_images),
                "converted_images": [str(img) for img in converted_images]
            })
            
        except Exception as e:
            logger.error(f"Image conversion failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/control/stop', methods=['POST'])
    def stop_controller():
        """Stop the controller gracefully"""
        try:
            controller = current_app.epaper_controller
            if not controller:
                return jsonify({"error": "Controller not initialized"}), 500
                
            controller.running = False
            return jsonify({"success": True, "message": "Controller stop requested"})
            
        except Exception as e:
            logger.error(f"Controller stop failed: {e}")
            return jsonify({"error": str(e)}), 500