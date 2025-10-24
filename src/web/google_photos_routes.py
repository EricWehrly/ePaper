"""
Google Photos Picker API routes for web interface
"""

import logging
import requests
from flask import Blueprint, jsonify, session, request
from .google_auth import GooglePhotosAuth
from .google_photos_picker_api import GooglePhotosPickerAPI

logger = logging.getLogger(__name__)

# Create blueprint
google_photos_bp = Blueprint('google_photos', __name__)

# Initialize API clients
google_auth = GooglePhotosAuth()
picker_api = GooglePhotosPickerAPI()

@google_photos_bp.route('/status')
def photos_status():
    """
    Check Google Photos integration status
    
    Returns:
        JSON with configuration and authentication status
    """
    try:
        # Add token scope debugging
        token_info = None
        if google_auth.is_authenticated():
            try:
                access_token = google_auth.get_access_token()
                if access_token:
                    # Check token info to see what scopes we actually have
                    response = requests.get(
                        f'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}',
                        timeout=5
                    )
                    if response.ok:
                        token_info = response.json()
                        logger.info(f"Current token scopes: {token_info.get('scope', 'No scope info')}")
            except Exception as e:
                logger.warning(f"Failed to get token info: {e}")

        return jsonify({
            'configured': google_auth.is_configured(),
            'authenticated': google_auth.is_authenticated(),
            'has_access_token': google_auth.get_access_token() is not None,
            'user': session.get('user_info') if google_auth.is_authenticated() else None,
            'token_scopes': token_info.get('scope') if token_info else None,
            'debug_token_info': token_info  # Remove this after debugging
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
        
        # Fallback to localhost if ngrok not available
        if not redirect_uri:
            redirect_uri = request.url_root.rstrip('/') + '/auth/callback'
        
        # Generate and redirect to OAuth URL
        auth_url = google_auth.get_auth_url(redirect_uri)
        logger.info(f"Redirecting to Google Photos auth: {auth_url} with redirect_uri: {redirect_uri}")
        
        return jsonify({'redirect_url': auth_url}), 302, {'Location': auth_url}
        
    except Exception as e:
        logger.error(f"Error starting Google Photos auth: {e}")
        return jsonify({
            'error': 'Failed to start authentication',
            'details': str(e)
        }), 500

@google_photos_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """
    Disconnect from Google Photos (logout)
    
    Returns:
        JSON confirmation of disconnection
    """
    try:
        # Clear authentication
        google_auth.logout()
        
        # Clear any active picker session
        session.pop('picker_session_id', None)
        session.pop('user_info', None)
        
        logger.info("User disconnected from Google Photos")
        return jsonify({
            'success': True,
            'message': 'Successfully disconnected from Google Photos'
        })
        
    except Exception as e:
        logger.error(f"Error disconnecting from Google Photos: {e}")
        return jsonify({
            'error': 'Failed to disconnect',
            'details': str(e)
        }), 500

@google_photos_bp.route('/create-session', methods=['POST'])
def create_session():
    """
    Create a new Google Photos picking session
    
    Returns:
        JSON with session info including pickerUri
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
        
        # Create picker session
        session_data = picker_api.create_session(access_token)
        
        # Store session ID in user session for tracking
        session['picker_session_id'] = session_data['id']
        
        return jsonify({
            'success': True,
            'session': session_data
        })
        
    except Exception as e:
        logger.error(f"Error creating picker session: {e}")
        return jsonify({
            'error': 'Failed to create picker session',
            'details': str(e)
        }), 500

@google_photos_bp.route('/session-status')
def get_session_status():
    """
    Get status of current picking session
    
    Returns:
        JSON with session status and media items availability
    """
    if not google_auth.is_authenticated():
        return jsonify({
            'error': 'Not authenticated',
            'details': 'Please authenticate with Google Photos first'
        }), 401
    
    session_id = session.get('picker_session_id')
    if not session_id:
        return jsonify({
            'error': 'No active session',
            'details': 'No picking session found. Create a session first.'
        }), 400
    
    try:
        access_token = google_auth.get_access_token()
        if not access_token:
            return jsonify({
                'error': 'No access token',
                'details': 'Authentication expired or invalid'
            }), 401
        
        # Get session status
        session_info = picker_api.get_session(access_token, session_id)
        
        return jsonify({
            'success': True,
            'session': session_info
        })
        
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({
            'error': 'Failed to get session status',
            'details': str(e)
        }), 500

@google_photos_bp.route('/selected-photos')
def get_selected_photos():
    """
    Get photos selected by user in current session
    
    Query parameters:
        page_size: Number of photos per page (default: 25, max: 100)
        page_token: Pagination token
        
    Returns:
        JSON with selected photos
    """
    if not google_auth.is_authenticated():
        return jsonify({
            'error': 'Not authenticated',
            'details': 'Please authenticate with Google Photos first'
        }), 401
    
    session_id = session.get('picker_session_id')
    if not session_id:
        return jsonify({
            'error': 'No active session',
            'details': 'No picking session found. Create a session first.'
        }), 400
    
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
        
        # First check if session has media items
        session_info = picker_api.get_session(access_token, session_id)
        if not session_info.get('mediaItemsSet', False):
            return jsonify({
                'error': 'No media items selected',
                'details': 'User has not completed photo selection yet'
            }), 400
        
        # Get selected media items
        result = picker_api.list_media_items(
            access_token=access_token,
            session_id=session_id,
            page_size=page_size,
            page_token=page_token
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting selected photos: {e}")
        return jsonify({
            'error': 'Failed to get selected photos',
            'details': str(e)
        }), 500

@google_photos_bp.route('/download', methods=['POST'])
def download_photos():
    """
    Download selected photos and add to conversion queue
    
    This endpoint works with photos selected via the Picker API
        
    Returns:
        JSON with download results
    """
    if not google_auth.is_authenticated():
        return jsonify({
            'error': 'Not authenticated',
            'details': 'Please authenticate with Google Photos first'
        }), 401
    
    session_id = session.get('picker_session_id')
    if not session_id:
        return jsonify({
            'error': 'No active session',
            'details': 'No picking session found. Create a session first.'
        }), 400
    
    try:
        access_token = google_auth.get_access_token()
        if not access_token:
            return jsonify({
                'error': 'No access token',
                'details': 'Authentication expired or invalid'
            }), 401
        
        # Get all selected photos from the session
        result = picker_api.list_media_items(access_token, session_id)
        photos = result.get('photos', [])
        
        if not photos:
            return jsonify({
                'error': 'No photos to download',
                'details': 'No photos selected in current session'
            }), 400
        
        # Import download functionality
        from ..google_photos.downloader import GooglePhotosDownloader
        from google.oauth2.credentials import Credentials
        
        # Create credentials object for downloader
        tokens = session.get('google_tokens', {})
        credentials = Credentials(
            token=access_token,
            refresh_token=tokens.get('refresh_token'),
            client_id=google_auth.credentials.get('client_id'),
            client_secret=google_auth.credentials.get('client_secret'),
            token_uri=google_auth.oauth_config['token_uri']
        )
        
        # Download photos
        downloader = GooglePhotosDownloader(credentials)
        downloaded_files = []
        
        for photo in photos:
            # Convert to expected format for downloader
            media_item = {
                'id': photo['id'],
                'filename': photo['filename'],
                'mediaFile': {
                    'baseUrl': photo['baseUrl'],
                    'mimeType': photo['mimeType']
                }
            }
            
            file_path = downloader.download_media_item(media_item)
            if file_path:
                downloaded_files.append(file_path)
        
        logger.info(f"Downloaded {len(downloaded_files)} photos from Google Photos")
        
        return jsonify({
            'success': True,
            'downloaded_count': len(downloaded_files),
            'failed_count': len(photos) - len(downloaded_files),
            'files': downloaded_files
        })
        
    except Exception as e:
        logger.error(f"Error downloading photos: {e}")
        return jsonify({
            'error': 'Failed to download photos',
            'details': str(e)
        }), 500