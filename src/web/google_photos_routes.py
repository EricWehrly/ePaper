"""
Google Photos API Routes

Flask routes for Google Photos integration:
- /api/google-photos/albums - List user albums
- /api/google-photos/photos - Search/list photos  
- /api/google-photos/recent - Get recent photos
- /api/google-photos/download - Download selected photos
"""

import logging
from flask import Blueprint, request, jsonify, session
from .google_auth import GooglePhotosAuth
from .google_photos_api import GooglePhotosAPI

logger = logging.getLogger(__name__)

# Create blueprint for Google Photos API routes
google_photos_bp = Blueprint('google_photos', __name__, url_prefix='/api/google-photos')

# Initialize API clients
google_auth = GooglePhotosAuth()
google_api = GooglePhotosAPI()

@google_photos_bp.route('/status')
def photos_status():
    """
    Check Google Photos integration status
    
    Returns:
        JSON with configuration and authentication status
    """
    try:
        return jsonify({
            'configured': google_auth.is_configured(),
            'authenticated': google_auth.is_authenticated(),
            'has_access_token': google_auth.get_access_token() is not None,
            'user': session.get('user_info') if google_auth.is_authenticated() else None
        })
        
    except Exception as e:
        logger.error(f"Error checking Google Photos status: {e}")
        return jsonify({
            'error': 'Failed to check status',
            'details': str(e)
        }), 500

@google_photos_bp.route('/auth')
def start_auth():
    """
    Start Google Photos OAuth authentication flow
    
    Redirects user to Google authorization URL
    """
    try:
        if not google_auth.is_configured():
            return jsonify({
                'error': 'Google Photos not configured',
                'details': 'OAuth credentials not found. Please configure Google Photos integration.'
            }), 500
        
        # Construct redirect URI for the callback - prefer HTTPS ngrok URL if available
        redirect_uri = None
        
        # Try to get ngrok HTTPS URL first
        try:
            import requests
            ngrok_urls = [
                'http://localhost:4040/api/tunnels',
                'http://host.docker.internal:4040/api/tunnels', 
                'http://epaper-ngrok-1:4040/api/tunnels'
            ]
            
            for ngrok_url in ngrok_urls:
                try:
                    response = requests.get(ngrok_url, timeout=2)
                    if response.status_code == 200:
                        tunnels = response.json().get('tunnels', [])
                        https_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None)
                        if https_tunnel:
                            public_url = https_tunnel.get('public_url')
                            redirect_uri = f"{public_url}/auth/callback"
                            break
                except requests.exceptions.RequestException:
                    continue
        except Exception:
            pass
        
        # Fallback to Flask url_for if ngrok not available
        if not redirect_uri:
            from flask import url_for
            redirect_uri = url_for('auth.oauth_callback', _external=True)
        
        # Get authorization URL and redirect user
        auth_url = google_auth.get_auth_url(redirect_uri=redirect_uri)
        logger.info(f"Redirecting to Google Photos auth: {auth_url} with redirect_uri: {redirect_uri}")
        
        from flask import redirect
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"Error starting Google Photos auth: {e}")
        return jsonify({
            'error': 'Failed to start authentication',
            'details': str(e)
        }), 500

@google_photos_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """
    Disconnect from Google Photos by clearing stored tokens
    
    Returns:
        JSON confirmation of disconnection
    """
    try:
        # Clear authentication data
        google_auth.clear_authentication()
        
        # Clear session data
        session.pop('google_access_token', None)
        session.pop('google_refresh_token', None) 
        session.pop('user_info', None)
        
        logger.info("User disconnected from Google Photos")
        
        return jsonify({
            'success': True,
            'message': 'Disconnected from Google Photos'
        })
        
    except Exception as e:
        logger.error(f"Error disconnecting from Google Photos: {e}")
        return jsonify({
            'error': 'Failed to disconnect',
            'details': str(e)
        }), 500

@google_photos_bp.route('/ngrok-info')
def ngrok_info():
    """
    Provide ngrok URL information for OAuth redirect
    
    Returns:
        JSON with ngrok URL and redirect recommendation
    """
    try:
        import requests
        
        # Check if ngrok is running by querying its API
        try:
            response = requests.get('http://ngrok:4040/api/tunnels', timeout=2)
            if response.ok:
                tunnels = response.json().get('tunnels', [])
                https_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None)
                
                if https_tunnel:
                    ngrok_url = https_tunnel['public_url']
                    
                    # Recommend redirect if user is not authenticated and we're on local domain
                    should_redirect = (not google_auth.is_authenticated() and 
                                     request.host.startswith('raspberrypi.local'))
                    
                    return jsonify({
                        'ngrok_url': ngrok_url,
                        'should_redirect': should_redirect,
                        'authenticated': google_auth.is_authenticated()
                    })
        except:
            pass  # Ngrok not available
        
        return jsonify({
            'ngrok_url': None,
            'should_redirect': False,
            'authenticated': google_auth.is_authenticated()
        })
        
    except Exception as e:
        logger.error(f"Error getting ngrok info: {e}")
        return jsonify({
            'error': 'Failed to get ngrok info',
            'details': str(e)
        }), 500

@google_photos_bp.route('/albums')
def list_albums():
    """
    List user's Google Photos albums
    
    Query parameters:
        page_size: Number of albums per page (default: 20, max: 50)
        page_token: Pagination token
        
    Returns:
        JSON with albums list and pagination info
    """
    if not google_auth.is_authenticated():
        return jsonify({
            'error': 'Not authenticated',
            'details': 'Please authenticate with Google Photos first'
        }), 401
    
    try:
        access_token = google_auth.get_access_token()
        if not access_token:
            return jsonify({
                'error': 'No access token',
                'details': 'Authentication expired or invalid'
            }), 401
        
        # Get query parameters
        page_size = min(int(request.args.get('page_size', 20)), 50)
        page_token = request.args.get('page_token')
        
        # Fetch albums from Google Photos API
        result = google_api.get_albums(
            access_token=access_token,
            page_size=page_size,
            page_token=page_token
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error listing albums: {e}")
        return jsonify({
            'error': 'Failed to list albums',
            'details': str(e)
        }), 500

@google_photos_bp.route('/photos')
def search_photos():
    """
    Search for photos with optional filters
    
    Query parameters:
        album_id: Search within specific album (optional)
        page_size: Number of photos per page (default: 25, max: 100) 
        page_token: Pagination token
        
    Returns:
        JSON with photos list and pagination info
    """
    if not google_auth.is_authenticated():
        return jsonify({
            'error': 'Not authenticated',
            'details': 'Please authenticate with Google Photos first'
        }), 401
    
    try:
        access_token = google_auth.get_access_token()
        if not access_token:
            return jsonify({
                'error': 'No access token', 
                'details': 'Authentication expired or invalid'
            }), 401
        
        # Get query parameters
        album_id = request.args.get('album_id')
        page_size = min(int(request.args.get('page_size', 25)), 100)
        page_token = request.args.get('page_token')
        
        # Search photos
        result = google_api.search_photos(
            access_token=access_token,
            album_id=album_id,
            page_size=page_size,
            page_token=page_token
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error searching photos: {e}")
        return jsonify({
            'error': 'Failed to search photos',
            'details': str(e)
        }), 500

@google_photos_bp.route('/recent')
def recent_photos():
    """
    Get recent photos from user's library
    
    Query parameters:
        page_size: Number of photos per page (default: 25, max: 100)
        page_token: Pagination token
        
    Returns:
        JSON with recent photos
    """
    if not google_auth.is_authenticated():
        return jsonify({
            'error': 'Not authenticated',
            'details': 'Please authenticate with Google Photos first'  
        }), 401
    
    try:
        access_token = google_auth.get_access_token()
        if not access_token:
            return jsonify({
                'error': 'No access token',
                'details': 'Authentication expired or invalid'
            }), 401
        
        # Get query parameters
        page_size = min(int(request.args.get('page_size', 25)), 100)
        page_token = request.args.get('page_token')
        
        # Get recent photos
        result = google_api.get_recent_photos(
            access_token=access_token,
            page_size=page_size,
            page_token=page_token
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting recent photos: {e}")
        return jsonify({
            'error': 'Failed to get recent photos',
            'details': str(e)
        }), 500

@google_photos_bp.route('/download', methods=['POST'])
def download_photos():
    """
    Download selected photos and add to conversion queue
    
    JSON payload:
        {
            "photos": [
                {
                    "id": "photo_id",
                    "baseUrl": "photo_base_url", 
                    "filename": "photo_filename"
                }
            ]
        }
        
    Returns:
        JSON with download results
    """
    if not google_auth.is_authenticated():
        return jsonify({
            'error': 'Not authenticated',
            'details': 'Please authenticate with Google Photos first'
        }), 401
    
    try:
        access_token = google_auth.get_access_token()
        if not access_token:
            return jsonify({
                'error': 'No access token',
                'details': 'Authentication expired or invalid'
            }), 401
        
        # Get request data
        data = request.get_json()
        if not data or 'photos' not in data:
            return jsonify({
                'error': 'Invalid request',
                'details': 'Missing photos array in request body'
            }), 400
        
        photos_to_download = data['photos']
        if not photos_to_download:
            return jsonify({
                'error': 'No photos specified',
                'details': 'Photos array is empty'
            }), 400
        
        # Download photos and add to conversion queue
        from flask import current_app
        controller = current_app.epaper_controller
        if not controller:
            return jsonify({
                'error': 'Controller not available',
                'details': 'ePaper controller not initialized'
            }), 500
        
        downloaded_photos = []
        failed_downloads = []
        
        for photo in photos_to_download:
            try:
                photo_id = photo.get('id')
                base_url = photo.get('baseUrl')
                filename = photo.get('filename', f"google_photo_{photo_id}.jpg")
                
                if not photo_id or not base_url:
                    failed_downloads.append({
                        'photo': photo,
                        'error': 'Missing photo ID or base URL'
                    })
                    continue
                
                # Download photo data
                photo_data = google_api.download_photo(access_token, photo_id, base_url)
                
                # Save to pic-raw directory
                import os
                from pathlib import Path
                
                # Ensure safe filename
                safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
                if not safe_filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    safe_filename += '.jpg'
                
                # Handle duplicate filenames
                file_path = controller.source_dir / safe_filename
                counter = 1
                original_path = file_path
                while file_path.exists():
                    name_parts = original_path.stem, counter, original_path.suffix
                    file_path = original_path.parent / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                    counter += 1
                
                # Write photo data to file
                with open(file_path, 'wb') as f:
                    f.write(photo_data)
                
                # Add to conversion queue if available
                queue_id = None
                if controller.conversion_queue:
                    queue_id = controller.conversion_queue.add_file(file_path)
                
                downloaded_photos.append({
                    'photo_id': photo_id,
                    'filename': file_path.name,
                    'path': str(file_path),
                    'size': len(photo_data),
                    'queue_id': queue_id
                })
                
                logger.info(f"Downloaded Google Photo: {file_path.name}")
                
            except Exception as e:
                logger.error(f"Failed to download photo {photo.get('id', 'unknown')}: {e}")
                failed_downloads.append({
                    'photo': photo,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'downloaded': downloaded_photos,
            'failed': failed_downloads,
            'summary': {
                'total_requested': len(photos_to_download),
                'successful': len(downloaded_photos),
                'failed': len(failed_downloads)
            }
        })
        
    except Exception as e:
        logger.error(f"Error downloading photos: {e}")
        return jsonify({
            'error': 'Failed to download photos',
            'details': str(e)
        }), 500