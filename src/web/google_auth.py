"""
Google Photos Authentication Module

Handles OAuth 2.0 flow for Google Photos integration:
- Redirect to Google OAuth consent screen
- Handle OAuth callback and token exchange
- Session management for authenticated users
- Token refresh and validation
"""

import json
import secrets
import logging
from pathlib import Path
from urllib.parse import urlencode
import requests
from flask import session, request, redirect, url_for, current_app

logger = logging.getLogger(__name__)

class GooglePhotosAuth:
    """Handles Google Photos OAuth authentication"""
    
    def __init__(self, credentials_path=None):
        """
        Initialize Google Photos authentication
        
        Args:
            credentials_path: Path to Google OAuth credentials JSON file
        """
        self.credentials_path = credentials_path or Path("config/google_photos_credentials.json")
        self.credentials = None
        self.oauth_config = {
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'userinfo_uri': 'https://www.googleapis.com/oauth2/v2/userinfo',
            'revoke_uri': 'https://oauth2.googleapis.com/revoke',
        }
        self.scopes = [
            'https://www.googleapis.com/auth/photospicker.mediaitems.readonly',
            'https://www.googleapis.com/auth/photoslibrary.readonly',
            'openid',
            'email'
        ]
        self._load_credentials()
    
    def _load_credentials(self):
        """Load OAuth credentials from JSON file"""
        try:
            if self.credentials_path.exists():
                with open(self.credentials_path, 'r') as f:
                    data = json.load(f)
                    if 'web' in data:
                        self.credentials = data['web']
                    else:
                        self.credentials = data
                logger.info("Google Photos credentials loaded")
            else:
                logger.error(f"Credentials file not found: {self.credentials_path}")
                self.credentials = None
        except Exception as e:
            logger.error(f"Failed to load Google Photos credentials: {e}")
            self.credentials = None
    
    def is_configured(self):
        """Check if OAuth credentials are properly configured"""
        return (self.credentials and 
                'client_id' in self.credentials and 
                'client_secret' in self.credentials)
    
    def get_auth_url(self, redirect_uri, state=None):
        """
        Generate Google OAuth authorization URL
        
        Args:
            redirect_uri: Where to redirect after OAuth consent
            state: Optional state parameter for security
            
        Returns:
            Authorization URL string
        """
        if not self.is_configured():
            raise ValueError("Google OAuth credentials not configured")
        
        if not state:
            state = secrets.token_urlsafe(32)
            
        # Store state in session for verification
        session['oauth_state'] = state
        session['oauth_redirect_uri'] = redirect_uri
        
        params = {
            'client_id': self.credentials['client_id'],
            'redirect_uri': redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent'  # Force consent screen to get refresh token
        }
        
        auth_url = f"{self.oauth_config['auth_uri']}?{urlencode(params)}"
        logger.info(f"Generated OAuth URL for redirect_uri: {redirect_uri}")
        return auth_url
    
    def handle_callback(self, code, state, redirect_uri):
        """
        Handle OAuth callback and exchange code for tokens
        
        Args:
            code: Authorization code from OAuth callback
            state: State parameter for verification
            redirect_uri: Must match the redirect_uri used in auth request
            
        Returns:
            dict: Token response with access_token, refresh_token, etc.
        """
        if not self.is_configured():
            raise ValueError("Google OAuth credentials not configured")
        
        # Verify state parameter
        session_state = session.get('oauth_state')
        if not state or state != session_state:
            raise ValueError("Invalid state parameter")
        
        # Verify redirect URI
        session_redirect_uri = session.get('oauth_redirect_uri') 
        if redirect_uri != session_redirect_uri:
            raise ValueError("Redirect URI mismatch")
        
        # Exchange code for tokens
        token_data = {
            'client_id': self.credentials['client_id'],
            'client_secret': self.credentials['client_secret'], 
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        response = requests.post(self.oauth_config['token_uri'], data=token_data)
        response.raise_for_status()
        
        tokens = response.json()
        
        # Add timestamp for expiration tracking
        import time
        tokens['issued_at'] = time.time()
        
        # Store tokens in session
        session['google_tokens'] = tokens
        session['authenticated'] = True
        
        # Clean up OAuth session data
        session.pop('oauth_state', None)
        session.pop('oauth_redirect_uri', None)
        
        logger.info("Successfully exchanged OAuth code for tokens")
        return tokens
    
    def get_user_info(self, access_token):
        """
        Get user information from Google
        
        Args:
            access_token: Valid Google access token
            
        Returns:
            dict: User information (email, name, etc.)
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(self.oauth_config['userinfo_uri'], headers=headers)
        response.raise_for_status()
        
        user_info = response.json()
        logger.info(f"Retrieved user info for: {user_info.get('email', 'unknown')}")
        return user_info
    
    def refresh_token(self, refresh_token):
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            dict: New token response
        """
        if not self.is_configured():
            raise ValueError("Google OAuth credentials not configured")
        
        token_data = {
            'client_id': self.credentials['client_id'],
            'client_secret': self.credentials['client_secret'],
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(self.oauth_config['token_uri'], data=token_data)
        response.raise_for_status()
        
        new_tokens = response.json()
        
        # Add timestamp for expiration tracking
        import time
        new_tokens['issued_at'] = time.time()
        
        # Update session with new tokens
        current_tokens = session.get('google_tokens', {})
        current_tokens.update(new_tokens)
        session['google_tokens'] = current_tokens
        
        logger.info("Successfully refreshed access token")
        return new_tokens
    
    def is_authenticated(self):
        """Check if user is currently authenticated"""
        return session.get('authenticated', False) and 'google_tokens' in session
    
    def get_access_token(self):
        """
        Get valid access token, refreshing if necessary
        
        Returns:
            str: Valid access token or None if not authenticated
        """
        if not self.is_authenticated():
            return None
        
        tokens = session['google_tokens']
        access_token = tokens.get('access_token')
        
        # Check if token is expired and refresh if needed
        if self._is_token_expired(tokens):
            refresh_token = tokens.get('refresh_token')
            if refresh_token:
                try:
                    logger.info("Access token expired, refreshing...")
                    new_tokens = self.refresh_token(refresh_token)
                    access_token = new_tokens.get('access_token', access_token)
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    return None
            else:
                logger.error("Token expired but no refresh token available")
                return None
        
        return access_token
    
    def _is_token_expired(self, tokens):
        """
        Check if access token is expired
        
        Args:
            tokens: Token dictionary with expires_in and timestamp
            
        Returns:
            bool: True if token is expired or will expire soon
        """
        import time
        
        # Get token expiration info
        expires_in = tokens.get('expires_in', 3600)  # Default 1 hour
        issued_at = tokens.get('issued_at')
        
        # If no issued_at timestamp, assume token is fresh
        if not issued_at:
            # Add timestamp for future checks
            tokens['issued_at'] = time.time()
            session['google_tokens'] = tokens
            return False
        
        # Check if token will expire in the next 5 minutes (300 seconds buffer)
        current_time = time.time()
        expiry_time = issued_at + expires_in
        buffer_time = 300  # 5 minutes
        
        return (current_time + buffer_time) >= expiry_time
    
    def logout(self):
        """Clear authentication session"""
        session.pop('google_tokens', None)
        session.pop('authenticated', None)
        logger.info("User logged out")
    
    def clear_authentication(self):
        """Clear all authentication data (alias for logout)"""
        self.logout()
    
    def revoke_token(self, token):
        """
        Revoke access token or refresh token
        
        Args:
            token: Token to revoke
        """
        try:
            params = {'token': token}
            response = requests.post(self.oauth_config['revoke_uri'], params=params)
            response.raise_for_status()
            logger.info("Token revoked successfully")
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")