"""
Google Photos Authentication Routes

Flask routes for handling Google OAuth flow:
- /auth/google - Redirect to Google OAuth consent screen  
- /auth/callback - Handle OAuth callback and token exchange
- /auth/status - Check authentication status
- /auth/logout - Clear authentication session
"""

import logging
from flask import Blueprint, request, redirect, jsonify, session, url_for, current_app
from .google_auth import GooglePhotosAuth

logger = logging.getLogger(__name__)

def get_base_url(request):
    """
    Get the correct base URL for the current request, handling proxies properly.
    
    This works with:
    - ngrok tunnels (X-Forwarded-Proto: https)
    - Cloudflare/load balancers (X-Forwarded-Proto: https)  
    - Direct HTTPS access (request.is_secure)
    - Local development (HTTP)
    
    Args:
        request: Flask request object
        
    Returns:
        str: Base URL (e.g., "https://example.com" or "http://localhost:5000")
    """
    if request.headers.get('X-Forwarded-Proto') == 'https':
        # Behind HTTPS proxy (ngrok, cloudflare, load balancer, etc.)
        return f"https://{request.headers.get('Host')}"
    else:
        # Direct access (HTTPS or HTTP)
        return request.url_root.rstrip('/')

# Create blueprint for auth routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize Google Photos auth handler
google_auth = GooglePhotosAuth()

@auth_bp.route('/google')
def google_login():
    """
    Initiate Google OAuth flow
    
    Query parameters:
        redirect_uri: Where to redirect after authentication (optional)
        
    Returns:
        Redirect to Google OAuth consent screen
    """
    if not google_auth.is_configured():
        return jsonify({
            'error': 'Google Photos authentication not configured',
            'details': 'Missing OAuth credentials in config/google_photos_credentials.json'
        }), 500
    
    # Determine redirect URI based on request
    base_url = get_base_url(request)
    callback_uri = f"{base_url}/auth/callback"
    
    try:
        # Generate OAuth authorization URL
        auth_url = google_auth.get_auth_url(callback_uri)
        
        logger.info(f"Redirecting to Google OAuth with callback: {callback_uri}")
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"Failed to initiate OAuth flow: {e}")
        return jsonify({
            'error': 'Failed to initiate authentication',
            'details': str(e)
        }), 500

@auth_bp.route('/callback')
def oauth_callback():
    """
    Handle OAuth callback from Google
    
    Query parameters:
        code: Authorization code from Google
        state: State parameter for security verification
        error: Error code if OAuth failed
        
    Returns:
        Redirect to success page or error response
    """
    # Check for OAuth errors
    error = request.args.get('error')
    if error:
        error_description = request.args.get('error_description', 'Unknown error')
        logger.error(f"OAuth error: {error} - {error_description}")
        return jsonify({
            'error': 'OAuth authentication failed',
            'details': error_description
        }), 400
    
    # Get authorization code and state
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        return jsonify({
            'error': 'Missing authorization code',
            'details': 'OAuth callback did not include required authorization code'
        }), 400
    
    try:
        # Determine redirect URI (must match what was used in auth request)
        base_url = get_base_url(request)
        callback_uri = f"{base_url}/auth/callback"
        
        # Exchange code for tokens
        tokens = google_auth.handle_callback(code, state, callback_uri)
        
        # Get user information
        access_token = tokens.get('access_token')
        if access_token:
            user_info = google_auth.get_user_info(access_token)
            session['user_info'] = user_info
            logger.info(f"User authenticated: {user_info.get('email', 'unknown')}")
        
        # Redirect to main app with success
        return redirect('/?auth=success')
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return jsonify({
            'error': 'Authentication failed',
            'details': str(e)
        }), 500

@auth_bp.route('/status')
def auth_status():
    """
    Check current authentication status
    
    Returns:
        JSON with authentication status and user info
    """
    try:
        is_configured = google_auth.is_configured()
        is_authenticated = google_auth.is_authenticated()
        user_info = session.get('user_info') if is_authenticated else None
        
        return jsonify({
            'configured': is_configured,
            'authenticated': is_authenticated,
            'user': user_info,
            'has_access_token': google_auth.get_access_token() is not None
        })
        
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return jsonify({
            'error': 'Failed to check authentication status',
            'details': str(e)
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Log out user and clear authentication session
    
    Returns:
        JSON confirmation of logout
    """
    try:
        # Optionally revoke tokens
        if google_auth.is_authenticated():
            access_token = google_auth.get_access_token()
            if access_token:
                google_auth.revoke_token(access_token)
        
        # Clear session
        google_auth.logout()
        session.pop('user_info', None)
        
        logger.info("User logged out successfully")
        return jsonify({'message': 'Logged out successfully'})
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({
            'error': 'Logout failed',
            'details': str(e)
        }), 500

@auth_bp.route('/test')
def test_auth():
    """
    Test endpoint for authentication debugging
    
    Returns:
        JSON with authentication configuration and status
    """
    try:
        # Determine correct base URL (same logic as auth endpoints)
        base_url = get_base_url(request)
        
        config_status = {
            'credentials_configured': google_auth.is_configured(),
            'credentials_path': str(google_auth.credentials_path),
            'credentials_exist': google_auth.credentials_path.exists(),
            'session_keys': list(session.keys()),
            'base_url': base_url,
            'callback_uri': f"{base_url}/auth/callback",
            'request_headers': dict(request.headers)  # Debug info
        }
        
        if google_auth.credentials:
            config_status['client_id'] = google_auth.credentials.get('client_id', 'Not found')[:20] + '...'
        
        return jsonify(config_status)
        
    except Exception as e:
        logger.error(f"Auth test error: {e}")
        return jsonify({
            'error': 'Auth test failed',
            'details': str(e)
        }), 500