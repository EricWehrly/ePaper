"""
Google Photos Picker API routes for web interface
"""

import json
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
            logger.warning("No access token available for session status check")
            return jsonify({
                'error': 'No access token',
                'details': 'Authentication expired or invalid'
            }), 401
        
        logger.info(f"Checking status for session: {session_id}")
        
        # Get session status
        session_info = picker_api.get_session(access_token, session_id)
        
        logger.info(f"Session {session_id} status: mediaItemsSet={session_info.get('mediaItemsSet', False)}")
        
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

@google_photos_bp.route('/debug-session/<session_id>')
def debug_session(session_id):
    """
    Debug endpoint to check a specific session ID
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
        
        logger.info(f"Debug check for session: {session_id}")
        
        # Get session status directly
        session_info = picker_api.get_session(access_token, session_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'session_info': session_info,
            'raw_response': 'check logs for details'
        })
        
    except Exception as e:
        logger.error(f"Error in debug session check: {e}")
        return jsonify({
            'error': 'Debug check failed',
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
        
        # Handle Picker API limitation
        if 'error' in result:
            return jsonify({
                'error': 'Picker API Limitation',
                'details': result.get('message', 'Cannot list selected media items with current Picker API'),
                'mediaItemsSet': True,
                'pickedMediaItems': [],
                'pickedAlbums': []
            }), 200  # Return 200 but with explanation
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting selected photos: {e}")
        return jsonify({
            'error': 'Failed to get selected photos',
            'details': str(e)
        }), 500

@google_photos_bp.route('/picker-callback', methods=['POST'])
def picker_callback():
    """
    Receive selection data from Google Photos Picker callback
    
    This endpoint receives the actual selection data when photos are selected
    in the picker, bypassing the API limitation of listing media items later.
    
    Returns:
        JSON confirmation of received selection data
    """
    logger.info("Received picker callback")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No data received',
                'details': 'Request body must contain JSON data'
            }), 400
        
        session_id = data.get('sessionId')
        selection_data = data.get('selectionData')
        
        if not session_id:
            return jsonify({
                'error': 'Missing session ID',
                'details': 'sessionId is required'
            }), 400
        
        if not selection_data:
            return jsonify({
                'error': 'Missing selection data',
                'details': 'selectionData is required'
            }), 400
        
        logger.info(f"Picker callback for session {session_id}")
        logger.info(f"Selection data received: {json.dumps(selection_data, indent=2)}")
        
        # Store the selection data in the session for later processing
        session['picker_selection_data'] = selection_data
        session['picker_selection_received'] = True
        session.modified = True
        
        # TODO: Process the selection data to extract media items
        # For now, just log what we received so we can see the structure
        
        return jsonify({
            'success': True,
            'message': 'Selection data received successfully',
            'sessionId': session_id,
            'dataReceived': True,
            'selectionSummary': {
                'keys': list(selection_data.keys()) if isinstance(selection_data, dict) else 'not_dict',
                'type': str(type(selection_data).__name__)
            }
        })
        
    except Exception as e:
        logger.error(f"Error processing picker callback: {e}")
        return jsonify({
            'error': 'Failed to process callback',
            'details': str(e)
        }), 500

@google_photos_bp.route('/recent-photos')
def get_recent_photos():
    """
    Get recent photos from Google Photos Library API
    
    This provides an alternative way to access photos when the Picker API
    cannot provide the exact selection data.
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
        
        limit = request.args.get('limit', '50', type=int)
        limit = min(limit, 100)  # Cap at 100
        
        logger.info(f"Getting recent photos from Google Photos Library API (limit: {limit})")
        
        # Use Google Photos Library API to get recent photos
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'pageSize': limit
        }
        
        response = requests.get(
            'https://photoslibrary.googleapis.com/v1/mediaItems',
            headers=headers,
            params=params
        )
        
        if not response.ok:
            logger.error(f"Library API error: {response.status_code} - {response.text}")
            return jsonify({
                'error': 'Failed to get photos from library',
                'details': f'API returned {response.status_code}'
            }), response.status_code
        
        data = response.json()
        photos = data.get('mediaItems', [])
        
        logger.info(f"Retrieved {len(photos)} photos from Google Photos Library API")
        
        return jsonify({
            'success': True,
            'photos': photos,
            'count': len(photos),
            'source': 'library_api'
        })
        
    except Exception as e:
        logger.error(f"Error getting recent photos: {e}")
        return jsonify({
            'error': 'Failed to get recent photos',
            'details': str(e)
        }), 500

@google_photos_bp.route('/library-photos')
def get_library_photos():
    """
    Get photos from Google Photos Library API with optional search
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
        
        limit = request.args.get('limit', '100', type=int)
        limit = min(limit, 100)  # Cap at 100
        
        logger.info(f"Getting library photos (limit: {limit})")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'pageSize': limit
        }
        
        response = requests.get(
            'https://photoslibrary.googleapis.com/v1/mediaItems',
            headers=headers,
            params=params
        )
        
        if not response.ok:
            logger.error(f"Library API error: {response.status_code} - {response.text}")
            return jsonify({
                'error': 'Failed to get library photos',
                'details': f'API returned {response.status_code}'
            }), response.status_code
        
        data = response.json()
        photos = data.get('mediaItems', [])
        
        logger.info(f"Retrieved {len(photos)} photos from library")
        
        return jsonify({
            'success': True,
            'photos': photos,
            'count': len(photos),
            'source': 'library_api'
        })
        
    except Exception as e:
        logger.error(f"Error getting library photos: {e}")
        return jsonify({
            'error': 'Failed to get library photos',
            'details': str(e)
        }), 500

@google_photos_bp.route('/download-library-photos', methods=['POST'])
def download_library_photos():
    """
    Download specific photos by ID from Google Photos Library API
    """
    if not google_auth.is_authenticated():
        return jsonify({
            'error': 'Not authenticated',
            'details': 'Please authenticate with Google Photos first'
        }), 401
    
    try:
        data = request.get_json()
        if not data or 'photoIds' not in data:
            return jsonify({
                'error': 'Missing photo IDs',
                'details': 'Request must include photoIds array'
            }), 400
        
        photo_ids = data['photoIds']
        if not isinstance(photo_ids, list) or len(photo_ids) == 0:
            return jsonify({
                'error': 'Invalid photo IDs',
                'details': 'photoIds must be a non-empty array'
            }), 400
        
        logger.info(f"Downloading {len(photo_ids)} photos from library")
        
        access_token = google_auth.get_access_token()
        if not access_token:
            return jsonify({
                'error': 'No access token',
                'details': 'Authentication expired or invalid'
            }), 401
        
        # Get photo details and download them
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        downloaded_photos = []
        failed_downloads = []
        
        for photo_id in photo_ids:
            try:
                # Get photo details
                response = requests.get(
                    f'https://photoslibrary.googleapis.com/v1/mediaItems/{photo_id}',
                    headers=headers
                )
                
                if response.ok:
                    photo_data = response.json()
                    downloaded_photos.append({
                        'id': photo_id,
                        'filename': photo_data.get('filename', f'photo_{photo_id}'),
                        'baseUrl': photo_data.get('baseUrl'),
                        'status': 'ready_for_download'
                    })
                else:
                    failed_downloads.append({
                        'id': photo_id,
                        'error': f'Failed to get photo details: {response.status_code}'
                    })
                    
            except Exception as e:
                failed_downloads.append({
                    'id': photo_id,
                    'error': str(e)
                })
        
        logger.info(f"Prepared {len(downloaded_photos)} photos for download, {len(failed_downloads)} failed")
        
        return jsonify({
            'success': True,
            'downloaded': downloaded_photos,
            'failed': failed_downloads,
            'total_requested': len(photo_ids),
            'total_ready': len(downloaded_photos)
        })
        
    except Exception as e:
        logger.error(f"Error downloading library photos: {e}")
        return jsonify({
            'error': 'Failed to download photos',
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