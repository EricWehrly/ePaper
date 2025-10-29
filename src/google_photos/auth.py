"""
Google Photos OAuth 2.0 authentication handling.
"""

import json
import logging
from typing import Optional, Tuple, Dict
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

class GooglePhotosAuth:
    """Handles OAuth 2.0 authentication for Google Photos API."""
    
    # Required scopes for Google Photos Library API
    LIBRARY_SCOPE = 'https://www.googleapis.com/auth/photoslibrary.readonly'
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize auth handler.
        
        Args:
            client_id: OAuth 2.0 client ID
            client_secret: OAuth 2.0 client secret
            redirect_uri: Authorized redirect URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = [self.LIBRARY_SCOPE]
        
    @classmethod
    def from_config(cls, config: Dict) -> 'GooglePhotosAuth':
        """Create auth handler from configuration dictionary."""
        return cls(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
    def get_authorization_url(self) -> Tuple[str, str]:
        """
        Get authorization URL for OAuth consent flow.
        
        Returns:
            Tuple of (authorization_url, state)
        """
        try:
            flow = self._create_flow()
            
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'  # Force consent screen to ensure refresh token
            )
            
            logger.info("Generated authorization URL")
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {e}")
            raise
    
    def exchange_code_for_tokens(self, authorization_code: str, state: str) -> Credentials:
        """
        Exchange authorization code for access tokens.
        
        Args:
            authorization_code: Authorization code from OAuth callback
            state: State parameter to verify request
            
        Returns:
            Google OAuth 2.0 credentials
        """
        try:
            flow = self._create_flow()
            flow.fetch_token(authorization_response=authorization_code)
            
            credentials = flow.credentials
            logger.info("Successfully exchanged authorization code for tokens")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to exchange authorization code: {e}")
            raise
            
    def refresh_credentials(self, credentials: Credentials) -> Credentials:
        """
        Refresh expired credentials.
        
        Args:
            credentials: Existing credentials with refresh token
            
        Returns:
            Refreshed credentials
        """
        try:
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                logger.info("Successfully refreshed credentials")
                
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to refresh credentials: {e}")
            raise
            
    def _create_flow(self) -> Flow:
        """Create OAuth 2.0 flow object."""
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        
        return flow
        
    @staticmethod
    def credentials_to_dict(credentials: Credentials) -> Dict:
        """Convert credentials object to dictionary for storage."""
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
    @staticmethod 
    def credentials_from_dict(credentials_dict: Dict) -> Optional[Credentials]:
        """Create credentials object from dictionary."""
        if not credentials_dict:
            return None
            
        try:
            from datetime import datetime
            
            expiry = None
            if credentials_dict.get('expiry'):
                expiry = datetime.fromisoformat(credentials_dict['expiry'])
                
            credentials = Credentials(
                token=credentials_dict['token'],
                refresh_token=credentials_dict.get('refresh_token'),
                token_uri=credentials_dict['token_uri'],
                client_id=credentials_dict['client_id'],
                client_secret=credentials_dict['client_secret'],
                scopes=credentials_dict['scopes'],
                expiry=expiry
            )
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to create credentials from dict: {e}")
            return None