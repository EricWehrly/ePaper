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
from .google_photos_routes import google_photos_bp

logger = logging.getLogger(__name__)

def register_routes(app):
    """Register all API routes with the Flask app"""
    
    # Register authentication blueprint
    app.register_blueprint(auth_bp)
    
    # Register Google Photos API blueprint
    app.register_blueprint(google_photos_bp, url_prefix='/api/google-photos')
    
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
            "display_initialized": controller.display_available,
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
            },
            "queue": controller.conversion_queue.get_status() if controller.conversion_queue else None
        })
    
    @app.route('/api/images', methods=['GET'])
    @api_route(require_controller=True)
    def list_images():
        """List available images in pic-raw and pic directories"""
        controller = get_controller()
            
        # Get source images using supported extensions with creation times
        source_images = []
        if controller.source_dir.exists():
            for ext in SUPPORTED_IMAGE_EXTENSIONS:
                for f in controller.source_dir.glob(f"*{ext}"):
                    try:
                        created_time = f.stat().st_ctime
                        source_images.append({
                            "name": f.name, 
                            "path": str(f), 
                            "type": "source",
                            "created_time": created_time
                        })
                    except OSError:
                        source_images.append({
                            "name": f.name, 
                            "path": str(f), 
                            "type": "source", 
                            "created_time": 0
                        })
            
            # Sort source images by creation time, oldest first
            source_images.sort(key=lambda x: x['created_time'])
        
        # Get converted images with creation time for sorting
        converted_images = []
        if controller.output_dir.exists():
            for f in controller.output_dir.glob("*.bmp"):
                try:
                    # Use creation time (st_ctime) for chronological ordering
                    created_time = f.stat().st_ctime
                    converted_images.append({
                        "name": f.name, 
                        "path": str(f), 
                        "type": "converted",
                        "created_time": created_time
                    })
                except OSError:
                    # Fallback without timestamp if file access fails
                    converted_images.append({
                        "name": f.name, 
                        "path": str(f), 
                        "type": "converted",
                        "created_time": 0
                    })
            
            # Sort by creation time, oldest first
            converted_images.sort(key=lambda x: x['created_time'])
            
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
                
            if not controller.display_available:
                return jsonify({"error": "Display hardware not available"}), 503
                
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

            if not controller.display_available:
                return jsonify({"error": "Display hardware not available"}), 503

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
            settings = controller.settings.copy()
            # Add max upload size in bytes (16MB default for Flask)
            settings['max_upload_size'] = app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
            return jsonify(settings)
        
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
        
        # Update ngrok_redirect settings
        if 'ngrok_redirect' in data:
            if isinstance(data['ngrok_redirect'], dict):
                controller.settings['ngrok_redirect'].update(data['ngrok_redirect'])
                controller._save_settings()
        
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
        skipped_files = []
        
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
            
            # Check if already converted (deduplication)
            # Use the original base name to check, before duplicate handling
            original_base_name = Path(safe_filename).stem
            converted_path = controller.output_dir / f"{original_base_name}.bmp"
            if converted_path.exists():
                logger.info(f"Skipping {safe_filename} - already converted as {converted_path.name}")
                skipped_files.append({
                    "filename": safe_filename,
                    "reason": "already_converted",
                    "converted_as": converted_path.name
                })
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
        
        if not uploaded_files and not skipped_files:
            return create_error_response("No valid image files uploaded", 400)
        
        message = f"Uploaded {len(uploaded_files)} file(s)"
        if skipped_files:
            message += f", skipped {len(skipped_files)} already converted"
        
        return create_success_response({
            "uploaded_files": uploaded_files,
            "skipped_files": skipped_files,
            "count": len(uploaded_files),
            "skipped_count": len(skipped_files)
        }, message)

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

    @app.route('/api/playlists', methods=['GET'])
    def list_playlists():
        """List available playlists from playlists/ directory"""
        try:
            from pathlib import Path
            import json
            
            playlists_dir = Path.cwd() / 'config' / 'playlists'
            if not playlists_dir.exists():
                return jsonify({'playlists': []})
            
            playlists = []
            for playlist_file in playlists_dir.glob('*.json'):
                try:
                    with open(playlist_file, 'r') as f:
                        playlist_data = json.load(f)
                        playlist_data['id'] = playlist_file.stem  # Use filename without extension as ID
                        playlists.append(playlist_data)
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load playlist {playlist_file}: {e}")
                    continue
            
            # Sort playlists by name for consistent ordering
            playlists.sort(key=lambda x: x.get('name', ''))
            
            return jsonify({'playlists': playlists})
            
        except Exception as e:
            logger.error(f"List playlists failed: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/playlists/<playlist_id>', methods=['GET'])
    def get_playlist(playlist_id):
        """Get details for a specific playlist"""
        try:
            from pathlib import Path
            import json
            
            # Secure the filename
            safe_playlist_id = secure_filename(playlist_id)
            if not safe_playlist_id or safe_playlist_id != playlist_id:
                return jsonify({'error': 'Invalid playlist ID'}), 400
            
            playlist_file = Path.cwd() / 'config' / 'playlists' / f'{playlist_id}.json'
            if not playlist_file.exists():
                return jsonify({'error': 'Playlist not found'}), 404
            
            with open(playlist_file, 'r') as f:
                playlist_data = json.load(f)
                playlist_data['id'] = playlist_id
            
            return jsonify(playlist_data)
            
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load playlist {playlist_id}: {e}")
            return jsonify({'error': 'Failed to load playlist'}), 500
        except Exception as e:
            logger.error(f"Get playlist failed: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/playlists/<playlist_id>/play', methods=['POST'])
    def play_playlist(playlist_id):
        """Start playing a specific playlist"""
        try:
            controller = current_app.epaper_controller
            if not controller:
                return jsonify({'error': 'Controller not initialized'}), 500
            
            # Get start index from request data
            data = request.get_json(force=True, silent=True) or {}
            start_index = safe_int(data.get('start_index', 0), minimum=0) or 0
            
            # Secure the playlist ID
            safe_playlist_id = secure_filename(playlist_id)
            if not safe_playlist_id or safe_playlist_id != playlist_id:
                return jsonify({'error': 'Invalid playlist ID'}), 400
            
            # Start the playlist
            success = controller.start_playlist(playlist_id, start_index)
            if success:
                return jsonify({
                    'success': True,
                    'playlist_id': playlist_id,
                    'start_index': start_index,
                    'mode': 'playlist'
                })
            else:
                return jsonify({'error': 'Failed to start playlist'}), 500
                
        except FileNotFoundError as e:
            logger.error(f"Playlist not found: {e}")
            return jsonify({'error': str(e)}), 404
        except ValueError as e:
            logger.error(f"Invalid playlist: {e}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Play playlist failed: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/playlists', methods=['POST'])
    def create_playlist():
        """Create a new playlist from dropped images"""
        try:
            from pathlib import Path
            import json
            from datetime import datetime
            
            data = request.get_json(force=True, silent=True) or {}
            
            name = data.get('name', '').strip()
            images = data.get('images', [])
            interval = safe_int(data.get('interval', 30), minimum=5) or 30
            orientation = data.get('orientation', 'portrait')
            
            if not name:
                return jsonify({'error': 'Playlist name is required'}), 400
            
            if not images or len(images) == 0:
                return jsonify({'error': 'At least one image is required'}), 400
            
            # Generate safe ID from name
            playlist_id = secure_filename(name.lower().replace(' ', '_'))
            if not playlist_id:
                return jsonify({'error': 'Invalid playlist name'}), 400
            
            # Check for existing playlist
            playlists_dir = Path.cwd() / 'config' / 'playlists'
            playlists_dir.mkdir(parents=True, exist_ok=True)
            
            playlist_file = playlists_dir / f'{playlist_id}.json'
            if playlist_file.exists():
                return jsonify({'error': f'Playlist "{name}" already exists'}), 409
            
            # Create playlist data
            now = datetime.utcnow().isoformat() + 'Z'
            playlist_data = {
                'id': playlist_id,
                'name': name,
                'description': f'Created from drag-and-drop',
                'images': images,
                'interval': interval,
                'orientation': orientation,
                'created': now,
                'modified': now
            }
            
            # Save playlist
            with open(playlist_file, 'w') as f:
                json.dump(playlist_data, f, indent=2)
            
            logger.info(f"Created playlist: {playlist_id} with {len(images)} images")
            
            return jsonify({
                'success': True,
                'playlist': playlist_data
            }), 201
            
        except Exception as e:
            logger.error(f"Create playlist failed: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/playlists/stop', methods=['POST'])
    def stop_playlist():
        """Stop current playlist playback"""
        try:
            controller = current_app.epaper_controller
            if not controller:
                return jsonify({'error': 'Controller not initialized'}), 500
            
            controller.stop_playlist()
            return jsonify({
                'success': True,
                'message': 'Playlist stopped',
                'mode': 'image'
            })
            
        except Exception as e:
            logger.error(f"Stop playlist failed: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/playlists/current', methods=['GET'])
    def get_current_playlist():
        """Get information about currently playing playlist"""
        try:
            controller = current_app.epaper_controller
            if not controller:
                return jsonify({'error': 'Controller not initialized'}), 500
            
            playlist_settings = controller.settings.get('playlist', {})
            current_id = playlist_settings.get('current_id')
            
            if not current_id or controller.settings.get('mode') != 'playlist':
                return jsonify({
                    'playing': False,
                    'playlist_id': None,
                    'current_index': 0,
                    'mode': controller.settings.get('mode', 'image')
                })
            
            # Load playlist data for additional info
            playlist_file = Path.cwd() / 'config' / 'playlists' / f'{current_id}.json'
            playlist_data = {}
            if playlist_file.exists():
                try:
                    import json
                    with open(playlist_file, 'r') as f:
                        playlist_data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass
            
            return jsonify({
                'playing': True,
                'playlist_id': current_id,
                'current_index': playlist_settings.get('current_index', 0),
                'total_images': len(playlist_data.get('images', [])),
                'playlist_name': playlist_data.get('name', current_id),
                'loop': playlist_settings.get('loop', True),
                'mode': 'playlist',
                'carousel_active': getattr(controller, '_carousel_active', False)
            })
            
        except Exception as e:
            logger.error(f"Get current playlist failed: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/ngrok-info', methods=['GET'])
    def get_ngrok_info():
        """Get ngrok tunnel information for OAuth redirects"""
        try:
            import requests
            
            # Check if ngrok is running by trying a few well-known endpoints.
            # Prefer localhost (works when ngrok is bound to host), then
            # host.docker.internal (Docker for Mac/Windows), then container name
            # (works when ngrok runs as a sibling container on the same network).
            ngrok_urls = [
                'http://localhost:4040/api/tunnels',
                'http://host.docker.internal:4040/api/tunnels',
                'http://epaper-ngrok-1:4040/api/tunnels'
            ]

            tunnels_data = None
            for url in ngrok_urls:
                try:
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        tunnels_data = response.json()
                        break
                except requests.exceptions.RequestException:
                    # try next candidate
                    continue

            if not tunnels_data:
                return jsonify({
                    'ngrok_available': False,
                    'message': 'ngrok not running or not accessible'
                })

            # Find HTTPS tunnel
            https_tunnel = None
            for tunnel in tunnels_data.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    https_tunnel = tunnel
                    break

            if https_tunnel:
                public_url = https_tunnel.get('public_url')
                return jsonify({
                    'ngrok_available': True,
                    'public_url': public_url,
                    'tunnel_active': True,
                    'oauth_url': f"{public_url}/api/google-photos/auth"
                })

            # ngrok is running but no HTTPS tunnel present
            return jsonify({
                'ngrok_available': True,
                'tunnel_active': False,
                'message': 'ngrok running but no HTTPS tunnel found'
            })
        except Exception as e:
            logger.error(f"ngrok info check failed: {e}")
            return jsonify({
                'ngrok_available': False,
                'error': str(e)
            })