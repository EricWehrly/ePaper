"""
Google Photos API Integration

Provides functionality to interact with Google Photos Library API:
- List user's photo albums
- Search for photos 
- Get photo metadata and download URLs
- Handle pagination and filtering
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from flask import session

logger = logging.getLogger(__name__)

class GooglePhotosAPI:
    """Interface to Google Photos Library API"""
    
    def __init__(self):
        """Initialize Google Photos API client"""
        self.base_url = "https://photoslibrary.googleapis.com/v1"
        
    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """Get HTTP headers with authorization"""
        return {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, access_token: str, method: str = 'GET', 
                     params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict:
        """
        Make authenticated request to Google Photos API
        
        Args:
            endpoint: API endpoint (e.g., '/albums')
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
            logger.error(f"Google Photos API error - {error_details}")
            raise
    
    def get_albums(self, access_token: str, page_size: int = 20, 
                   page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user's photo albums
        
        Args:
            access_token: Valid access token
            page_size: Number of albums per page (max 50)
            page_token: Token for pagination
            
        Returns:
            Dict with albums list and pagination info
        """
        params = {
            'pageSize': min(page_size, 50)
        }
        if page_token:
            params['pageToken'] = page_token
            
        try:
            result = self._make_request('/albums', access_token, params=params)
            
            albums = result.get('albums', [])
            # Add additional info for each album
            for album in albums:
                album['itemCount'] = album.get('mediaItemsCount', 0)
                album['coverPhotoUrl'] = album.get('coverPhotoBaseUrl')
                
            logger.info(f"Retrieved {len(albums)} albums")
            return {
                'albums': albums,
                'nextPageToken': result.get('nextPageToken'),
                'totalCount': len(albums)
            }
            
        except requests.RequestException as e:
            # Log the full error response for debugging
            if hasattr(e, 'response') and e.response is not None:
                error_details = f"Albums API - Status: {e.response.status_code}"
                try:
                    error_body = e.response.json()
                    error_details += f", Body: {error_body}"
                except:
                    error_details += f", Body: {e.response.text}"
                logger.error(error_details)
            logger.error(f"Failed to get albums: {e}")
            raise
    
    def search_photos(self, access_token: str, album_id: Optional[str] = None,
                     page_size: int = 25, page_token: Optional[str] = None,
                     filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Search for photos with optional filters
        
        Args:
            access_token: Valid access token
            album_id: Optional album ID to search within
            page_size: Number of photos per page (max 100)
            page_token: Token for pagination
            filters: Optional search filters
            
        Returns:
            Dict with photos list and pagination info
        """
        json_data = {
            'pageSize': min(page_size, 100)
        }
        
        if page_token:
            json_data['pageToken'] = page_token
            
        if album_id:
            json_data['albumId'] = album_id
            
        if filters:
            json_data['filters'] = filters
        
        try:
            result = self._make_request('/mediaItems:search', access_token, 
                                      method='POST', json_data=json_data)
            
            media_items = result.get('mediaItems', [])
            
            # Process media items to include useful info
            photos = []
            for item in media_items:
                # Only include photos (not videos) for now
                if item.get('mimeType', '').startswith('image/'):
                    photo = {
                        'id': item.get('id'),
                        'filename': item.get('filename'),
                        'description': item.get('description', ''),
                        'mimeType': item.get('mimeType'),
                        'creationTime': item.get('mediaMetadata', {}).get('creationTime'),
                        'width': int(item.get('mediaMetadata', {}).get('width', 0)),
                        'height': int(item.get('mediaMetadata', {}).get('height', 0)),
                        'baseUrl': item.get('baseUrl'),
                        'thumbnailUrl': f"{item.get('baseUrl')}=w300-h300-c",
                        'downloadUrl': f"{item.get('baseUrl')}=d"  # Download URL
                    }
                    photos.append(photo)
            
            logger.info(f"Found {len(photos)} photos in search")
            return {
                'photos': photos,
                'nextPageToken': result.get('nextPageToken'),
                'totalCount': len(photos)
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to search photos: {e}")
            raise
    
    def get_recent_photos(self, access_token: str, page_size: int = 25,
                         page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get recent photos from user's library
        
        Args:
            access_token: Valid access token
            page_size: Number of photos per page
            page_token: Token for pagination
            
        Returns:
            Dict with recent photos
        """
        # Use mediaItems endpoint instead of search for recent photos
        # The search endpoint requires filters, but for recent photos we can use the list endpoint
        params = {
            'pageSize': min(page_size, 100)
        }
        
        if page_token:
            params['pageToken'] = page_token
            
        try:
            result = self._make_request('/mediaItems', access_token, 
                                     method='GET', params=params)
            
            media_items = result.get('mediaItems', [])
            next_page_token = result.get('nextPageToken')
            
            # Process media items to match expected format
            photos = []
            for item in media_items:
                # Only include photos (not videos) for now
                if item.get('mimeType', '').startswith('image/'):
                    photo = {
                        'id': item.get('id'),
                        'filename': item.get('filename'),
                        'description': item.get('description', ''),
                        'mimeType': item.get('mimeType'),
                        'baseUrl': item.get('baseUrl'),
                        'thumbnailUrl': f"{item.get('baseUrl')}=w300-h300-c",
                        'downloadUrl': f"{item.get('baseUrl')}=d"  # Download URL
                    }
                    photos.append(photo)
            
            logger.info(f"Retrieved {len(photos)} recent photos")
            return {
                'photos': photos,
                'nextPageToken': next_page_token,
                'totalCount': len(photos)
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to get recent photos: {e}")
            raise
    
    def download_photo(self, access_token: str, photo_id: str, base_url: str) -> bytes:
        """
        Download photo data
        
        Args:
            access_token: Valid access token  
            photo_id: Photo ID
            base_url: Photo's base URL
            
        Returns:
            Photo data as bytes
        """
        # Use download URL to get full resolution image
        download_url = f"{base_url}=d"
        
        headers = self._get_headers(access_token)
        
        try:
            response = requests.get(download_url, headers=headers, timeout=60)
            response.raise_for_status()
            
            logger.info(f"Downloaded photo {photo_id}, size: {len(response.content)} bytes")
            return response.content
            
        except requests.RequestException as e:
            logger.error(f"Failed to download photo {photo_id}: {e}")
            raise