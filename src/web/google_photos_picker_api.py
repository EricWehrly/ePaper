"""
Google Photos Picker API Integration

Provides functionality to interact with Google Photos Picker API:
- Create picking sessions
- Poll session status
- List selected media items
- Handle photo selection flow
"""

import logging
import requests
import time
from typing import Dict, List, Optional, Any
from flask import session

logger = logging.getLogger(__name__)

class GooglePhotosPickerAPI:
    """Interface to Google Photos Picker API"""
    
    def __init__(self):
        """Initialize Google Photos Picker API client"""
        self.base_url = "https://photospicker.googleapis.com/v1"
        
    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """Get HTTP headers with authorization"""
        return {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, access_token: str, method: str = 'GET', 
                     params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict:
        """
        Make authenticated request to Google Photos Picker API
        
        Args:
            endpoint: API endpoint (e.g., '/sessions')
            access_token: Valid access token
            method: HTTP method
            params: Query parameters
            json_data: JSON payload for POST requests
            
        Returns:
            JSON response data
            
        Raises:
            requests.RequestException: For API errors
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(access_token)
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=30
        )
        
        try:
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # Log the full error response for debugging
            error_details = f"Status: {response.status_code}"
            try:
                error_body = response.json()
                error_details += f", Body: {error_body}"
            except:
                error_details += f", Body: {response.text}"
            logger.error(f"Google Photos Picker API error - {error_details}")
            raise
    
    def create_session(self, access_token: str, include_albums: bool = True) -> Dict[str, Any]:
        """
        Create a new picking session
        
        Args:
            access_token: Valid access token
            include_albums: Whether to include album selection capability
            
        Returns:
            Dict with session information including pickerUri
        """
        try:
            # For Google Photos Picker API, sessions are created with minimal configuration
            # The picker interface itself handles media item and album selection
            json_data = {}
            
            logger.info(f"Creating Picker session with config: {json_data}")
            
            result = self._make_request('/sessions', access_token, method='POST', json_data=json_data)
            
            session_data = {
                'id': result.get('id'),
                'pickerUri': result.get('pickerUri'),
                'pollingConfig': result.get('pollingConfig', {}),
                'created_at': time.time(),
                'supportsAlbums': include_albums
            }
            
            logger.info(f"Created Picker session: {session_data['id']} (albums: {include_albums})")
            return session_data
            
        except requests.RequestException as e:
            logger.error(f"Failed to create Picker session: {e}")
            raise
    
    def get_session(self, access_token: str, session_id: str) -> Dict[str, Any]:
        """
        Get session status and check if media items are set
        
        Args:
            access_token: Valid access token
            session_id: Picker session ID
            
        Returns:
            Dict with session status and media items info
        """
        try:
            result = self._make_request(f'/sessions/{session_id}', access_token)
            
            session_info = {
                'id': result.get('id'),
                'mediaItemsSet': result.get('mediaItemsSet', False),
                'pollingConfig': result.get('pollingConfig', {}),
                'pickerUri': result.get('pickerUri')
            }
            
            logger.info(f"Session {session_id} API response: {result}")
            
            if session_info['mediaItemsSet']:
                logger.info(f"Session {session_id} has selected media items")
            else:
                logger.debug(f"Session {session_id} has no media items yet")
            
            return session_info
            
        except requests.RequestException as e:
            logger.error(f"Failed to get session status: {e}")
            raise
    
    def list_media_items(self, access_token, session_id, page_size=25, page_token=None):
        """
        List media items selected in a picker session
        
        Uses the correct Google Photos Picker API endpoint:
        GET https://photospicker.googleapis.com/v1/mediaItems?sessionId={sessionId}
        """
        logger.info(f"Getting media items for session {session_id} using correct endpoint")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Use the correct endpoint format from the documentation
        params = {
            'sessionId': session_id,
            'pageSize': page_size
        }
        
        if page_token:
            params['pageToken'] = page_token
        
        try:
            # Log the full request for debugging
            logger.info(f"Making request to photospicker API:")
            logger.info(f"  URL: https://photospicker.googleapis.com/v1/mediaItems")
            logger.info(f"  Params: {params}")
            logger.info(f"  Headers: Authorization=Bearer {access_token[:20]}...")
            
            response = requests.get(
                'https://photospicker.googleapis.com/v1/mediaItems',  # Correct endpoint
                headers=headers,
                params=params
            )
            
            logger.info(f"API Response: Status={response.status_code}")
            
            if response.ok:
                data = response.json()
                logger.info(f"API Response body: {data}")
                
                # Google returns 'mediaItems', not 'pickedMediaItems'
                media_items = data.get('mediaItems', [])
                logger.info(f"Parsed media items: {len(media_items)} items")
                
                if len(media_items) == 0:
                    logger.warning(f"⚠️ API returned empty mediaItems array for session {session_id}")
                    logger.warning(f"Full response data: {data}")
                else:
                    logger.info(f"✅ Retrieved {len(media_items)} media items for session {session_id}")
                
                return {
                    'success': True,
                    'mediaItems': media_items,
                    'nextPageToken': data.get('nextPageToken')
                }
            else:
                logger.error(f"❌ API error for session {session_id}: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return {
                    'success': False,
                    'error': f'API returned {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            logger.error(f"Exception listing media items for session {session_id}: {e}")
            return {
                'success': False,
                'error': 'Request failed',
                'details': str(e)
            }
    
    def poll_session_until_complete(self, access_token: str, session_id: str, 
                                  max_wait_time: int = 300, check_interval: int = 5) -> bool:
        """
        Poll session until user completes selection or timeout
        
        Args:
            access_token: Valid access token
            session_id: Picker session ID
            max_wait_time: Maximum time to wait in seconds
            check_interval: How often to check in seconds
            
        Returns:
            True if media items were selected, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                session_info = self.get_session(access_token, session_id)
                
                if session_info['mediaItemsSet']:
                    return True
                
                # Use polling config from API if available
                polling_config = session_info.get('pollingConfig', {})
                interval = polling_config.get('pollInterval', check_interval)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error polling session: {e}")
                time.sleep(check_interval)
        
        logger.warning(f"Session {session_id} polling timed out after {max_wait_time}s")
        return False
    
    def delete_session(self, access_token: str, session_id: str) -> bool:
        """
        Delete a picking session
        
        Args:
            access_token: Valid access token
            session_id: Picker session ID
            
        Returns:
            True if successful
        """
        try:
            self._make_request(f'/sessions/{session_id}', access_token, method='DELETE')
            logger.info(f"Deleted Picker session: {session_id}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to delete session: {e}")
            return False