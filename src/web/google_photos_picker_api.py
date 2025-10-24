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
    
    def create_session(self, access_token: str) -> Dict[str, Any]:
        """
        Create a new picking session
        
        Args:
            access_token: Valid access token
            
        Returns:
            Dict with session information including pickerUri
        """
        try:
            result = self._make_request('/sessions', access_token, method='POST')
            
            session_data = {
                'id': result.get('id'),
                'pickerUri': result.get('pickerUri'),
                'pollingConfig': result.get('pollingConfig', {}),
                'created_at': time.time()
            }
            
            logger.info(f"Created Picker session: {session_data['id']}")
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
            
            if session_info['mediaItemsSet']:
                logger.info(f"Session {session_id} has selected media items")
            
            return session_info
            
        except requests.RequestException as e:
            logger.error(f"Failed to get session status: {e}")
            raise
    
    def list_media_items(self, access_token: str, session_id: str, 
                        page_size: int = 25, page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        List media items selected in the session
        
        Args:
            access_token: Valid access token
            session_id: Picker session ID
            page_size: Number of items per page
            page_token: Token for pagination
            
        Returns:
            Dict with selected media items
        """
        params = {
            'pageSize': min(page_size, 100)
        }
        
        if page_token:
            params['pageToken'] = page_token
            
        try:
            result = self._make_request(f'/sessions/{session_id}/mediaItems', 
                                     access_token, params=params)
            
            media_items = result.get('pickedMediaItems', [])
            next_page_token = result.get('nextPageToken')
            
            # Process media items to match expected format
            photos = []
            for item in media_items:
                media_file = item.get('mediaFile', {})
                photo = {
                    'id': media_file.get('id'),
                    'filename': item.get('filename'),
                    'mimeType': media_file.get('mimeType'),
                    'baseUrl': media_file.get('baseUrl'),
                    'thumbnailUrl': f"{media_file.get('baseUrl')}=w300-h300-c",
                    'downloadUrl': f"{media_file.get('baseUrl')}=d"
                }
                photos.append(photo)
            
            logger.info(f"Retrieved {len(photos)} selected media items from session {session_id}")
            return {
                'photos': photos,
                'nextPageToken': next_page_token,
                'totalItems': len(media_items)
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to list media items: {e}")
            raise
    
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