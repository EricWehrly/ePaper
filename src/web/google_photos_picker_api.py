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
    
    def list_media_items(self, access_token: str, session_id: str, 
                        page_size: int = 25, page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        List media items and albums selected in the session
        
        NOTE: The Google Photos Picker API doesn't provide a direct endpoint to list
        selected media items. This method is a placeholder that should be updated
        when Google provides the actual implementation.
        
        Args:
            access_token: Valid access token
            session_id: Picker session ID
            page_size: Number of items per page
            page_token: Token for pagination
            
        Returns:
            Dict with selected media items and albums
        """
        # For now, return a placeholder response indicating that media items
        # cannot be listed directly from the Picker API
        logger.warning(f"list_media_items called for session {session_id} - this functionality may not be available in Picker API")
        
        try:
            # First check if the session exists and has media items
            session_info = self.get_session(access_token, session_id)
            
            if not session_info.get('mediaItemsSet', False):
                return {
                    'pickedMediaItems': [],
                    'pickedAlbums': [],
                    'nextPageToken': None
                }
            
            # The Picker API doesn't currently provide a way to list the actual media items
            # that were selected. This is a limitation of the API design.
            # For now, we return a placeholder response.
            logger.error(f"Cannot list media items for session {session_id} - Picker API limitation")
            
            return {
                'error': 'Media items listing not available',
                'message': 'The Google Photos Picker API does not provide endpoints to list selected media items directly',
                'pickedMediaItems': [],
                'pickedAlbums': [],
                'nextPageToken': None
            }
            
        except Exception as e:
            logger.error(f"Failed to list media items: {e}")
            raise
            photos = []
            for item in media_items:
                media_file = item.get('mediaFile', {})
                photo = {
                    'id': media_file.get('id'),
                    'filename': item.get('filename'),
                    'mimeType': media_file.get('mimeType'),
                    'baseUrl': media_file.get('baseUrl'),
                    'thumbnailUrl': f"{media_file.get('baseUrl')}=w300-h300-c",
                    'downloadUrl': f"{media_file.get('baseUrl')}=d",
                    'type': 'photo'
                }
                photos.append(photo)
                
            # Process selected albums 
            selected_albums = []
            for album in albums:
                album_info = {
                    'id': album.get('id'),
                    'title': album.get('title'),
                    'mediaItemsCount': album.get('mediaItemsCount', 0),
                    'coverPhotoBaseUrl': album.get('coverPhotoBaseUrl'),
                    'type': 'album'
                }
                selected_albums.append(album_info)
            
            logger.info(f"Retrieved {len(photos)} photos and {len(selected_albums)} albums from session {session_id}")
            return {
                'photos': photos,
                'albums': selected_albums,
                'nextPageToken': next_page_token,
                'totalItems': len(media_items) + len(albums)
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