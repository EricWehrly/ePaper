"""
API routes for ePaper display control

Defines REST endpoints for interacting with the ePaper display system,
including image management, display control, and status monitoring.
"""

import logging
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import request, jsonify, current_app

from .api_utils import (
    api_route, create_success_response, create_error_response,
    validate_image_file, count_files_by_extension, get_controller,
    safe_int, SUPPORTED_IMAGE_EXTENSIONS
)
from .auth_routes import auth_bp

logger = logging.getLogger(__name__)

def register_routes(app):
    """Register all API routes with the Flask app"""
    
    # Register authentication blueprint
    app.register_blueprint(auth_bp)
    
    @app.route('/api/status', methods=['GET'])
    @api_route(require_controller=True)
    def get_status():
        """Get current system status"""
        controller = get_controller()
        
        # Count available images using utility function
        source_count = count_files_by_extension(controller.source_dir, SUPPORTED_IMAGE_EXTENSIONS)
        converted_count = count_files_by_extension(controller.output_dir, {'.bmp'})
        
        return jsonify({
            "status": "running" if controller.running else "stopped",
            "display_initialized": controller.display_manager is not None,
            "source_dir": str(controller.source_dir),
            "output_dir": str(controller.output_dir),
            "display_interval": controller.display_interval,
            "current_image": controller.current_image,
            "busy": controller.is_busy(),
            "carousel_active": getattr(controller, '_carousel_active', False),
            "last_display_completion": getattr(controller, '_last_display_completion', None),
            "settings": controller.settings,
            "image_counts": {
                "source": source_count,
                "converted": converted_count
            }
        })
    
    @app.route('/api/images', methods=['GET'])
    @api_route(require_controller=True)
    def list_images():
        """List available images in pic-raw and pic directories"""
        controller = get_controller()
            
        # Get source images using supported extensions
        source_images = []
        if controller.source_dir.exists():
            for ext in SUPPORTED_IMAGE_EXTENSIONS:
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
    
    @app.route('/api/display/image', methods=['POST'])
    @api_route(require_controller=True, require_display=True)
    def display_image():
        """Display a specific image on the ePaper display"""
        controller = get_controller()
        
        data = request.get_json()
        if not data or 'image_path' not in data:
            return create_error_response("image_path required", 400)
            
        image_path = Path(data['image_path'])
        if not image_path.exists():
            return create_error_response("Image file not found", 404)
            
        # Use controller helper so current_image is tracked
        controller.show_image(str(image_path))
        return create_success_response({"displayed_image": str(image_path)})
    
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

    @app.route('/api/display/blank', methods=['POST'])
    def blank_display():
        """Blank the e-paper display to white"""
        try:
            controller = current_app.epaper_controller
            if not controller:
                return jsonify({"error": "Controller not initialized"}), 500

            if not controller.display_manager:
                return jsonify({"error": "Display not initialized"}), 500

            if controller.is_busy():
                return jsonify({"error": "Display busy"}), 409

            controller.clear_display()
            return jsonify({"success": True})

        except Exception as e:
            logger.error(f"Blank display failed: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/display/clear', methods=['POST'])
    @api_route(require_controller=True, require_display=True)
    def clear_display_route():
        """Clear the e-paper display to white (alias of blank)"""
        controller = get_controller()
        controller.clear_display()
        return create_success_response()

    @app.route('/api/display/orientation', methods=['POST'])
    def set_orientation():
        """Set display orientation (portrait or landscape)"""
        try:
            controller = current_app.epaper_controller
            if not controller:
                return jsonify({"error": "Controller not initialized"}), 500

            data = request.get_json(force=True, silent=True) or {}
            orientation = data.get('orientation')
            if orientation not in ('portrait', 'landscape'):
                return jsonify({"error": "orientation must be 'portrait' or 'landscape'"}), 400

            portrait_mode = orientation == 'portrait'
            # Update orientation via controller helper
            controller.set_orientation(portrait_mode)
            # Reinitialize display if already initialized (optional)
            try:
                if controller.display_manager:
                    # Cleanup and re-init to apply new dimensions if required
                    controller.display_manager.cleanup()
                    controller.initialize_display()
            except Exception as e:
                logger.warning(f"Reinitializing display after orientation change failed: {e}")

            return jsonify({"success": True, "orientation": orientation})
        except Exception as e:
            logger.error(f"Set orientation failed: {e}")
            return jsonify({"error": str(e)}), 500

    # ------------- Settings Endpoints -------------
    @app.route('/api/settings', methods=['GET','POST'])
    @api_route(require_controller=True)
    def settings_handler():
        """Handle settings GET and POST operations"""
        controller = get_controller()
        
        if request.method == 'GET':
            return jsonify(controller.settings)
        
        data = request.get_json(force=True, silent=True) or {}
        
        # Update interval with validation
        if 'interval_sec' in data:
            interval = safe_int(data['interval_sec'], minimum=5)
            if interval is None:
                return create_error_response("invalid interval: must be integer >= 5", 400)
            controller.set_interval(interval)
        
        # Update mode / autoplay
        if 'mode' in data:
            controller.set_mode(data['mode'])
        if 'autoplay' in data:
            if data['autoplay']:
                controller.start_carousel()
            else:
                controller.stop_carousel()
        
        return create_success_response({"settings": controller.settings})

    # ------------- Navigation Endpoints -------------
    @app.route('/api/display/next', methods=['POST'])
    @api_route(require_controller=True, require_display=True)
    def api_next_image():
        """Navigate to next image in sequence"""
        controller = get_controller()
        img = controller.next_image()
        if not img:
            return create_error_response("No images", 400)
        return create_success_response({"current_image": img})

    @app.route('/api/display/prev', methods=['POST'])
    @api_route(require_controller=True, require_display=True)
    def api_prev_image():
        """Navigate to previous image in sequence"""
        controller = get_controller()
        img = controller.prev_image()
        if not img:
            return create_error_response("No images", 400)
        return create_success_response({"current_image": img})

    @app.route('/api/upload', methods=['POST'])
    @api_route(require_controller=True)
    def upload_files():
        """Upload image files to pic-raw directory"""
        controller = get_controller()
        
        # Check if files were uploaded
        if 'files' not in request.files:
            return create_error_response("No files uploaded", 400)
        
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return create_error_response("No files selected", 400)
        
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
            
            # Validate file extension using utility
            if not validate_image_file(file.filename):
                logger.warning(f"Unsupported file type: {file.filename}")
                continue
            
            # Secure the filename
            safe_filename = secure_filename(file.filename)
            if not safe_filename:
                logger.warning(f"Invalid filename: {file.filename}")
                continue
            
            # Save to pic-raw directory with duplicate handling
            file_path = controller.source_dir / safe_filename
            counter = 1
            original_path = file_path
            while file_path.exists():
                name_parts = original_path.stem, counter, original_path.suffix
                file_path = original_path.parent / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                counter += 1
            
            # Save the file
            file.save(str(file_path))
            uploaded_files.append({
                "filename": file_path.name,
                "path": str(file_path),
                "size": file_path.stat().st_size
            })
            
            logger.info(f"Uploaded file: {file_path.name}")
            
            # Add to conversion queue
            if controller.conversion_queue:
                queue_id = controller.conversion_queue.add_file(file_path)
                uploaded_files[-1]["queue_id"] = queue_id
        
        if not uploaded_files:
            return create_error_response("No valid image files uploaded", 400)
        
        return create_success_response({
            "uploaded_files": uploaded_files,
            "count": len(uploaded_files)
        }, f"Uploaded {len(uploaded_files)} file(s) and added to conversion queue")

    @app.route('/api/queue/status', methods=['GET'])
    def get_queue_status():
        """Get conversion queue status"""
        try:
            controller = current_app.epaper_controller
            if not controller or not controller.conversion_queue:
                return jsonify({"error": "Queue not initialized"}), 500
            
            status = controller.conversion_queue.get_status()
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Queue status failed: {e}")
            return jsonify({"error": str(e)}), 500