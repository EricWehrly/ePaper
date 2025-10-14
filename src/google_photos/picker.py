"""
Google Photos Picker API interface.
"""

import json
import time
import logging
import requests
from typing import Dict, List, Optional
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

class GooglePhotosPicker:
    """Interface for Google Photos Picker API."""
    
    BASE_URL = "https://photospicker.googleapis.com/v1"
    
    def __init__(self, credentials: Credentials):
        """
        Initialize picker API client.
        
        Args:
            credentials: Valid OAuth 2.0 credentials
        """
        self.credentials = credentials
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make authenticated request to Picker API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests
            
        Returns:
            JSON response as dictionary
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        # Ensure credentials are fresh
        if self.credentials.expired:
            self.credentials.refresh(requests.Request())
            
        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json"
        }
        
        # Merge any additional headers
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
            
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error in Picker API request: {e}")
            logger.error(f"Response content: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error in Picker API request: {e}")
            raise
            
    def create_session(self) -> Dict:
        """
        Create a new photo picking session.
        
        Returns:
            Session data including session ID and picker URI
        """
        try:
            logger.info("Creating new picker session")
            result = self._make_request("POST", "sessions")
            
            session_id = result.get('id')
            picker_uri = result.get('pickerUri')
            
            logger.info(f"Created picker session: {session_id}")
            logger.debug(f"Picker URI: {picker_uri}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create picker session: {e}")
            raise
            
    def get_session(self, session_id: str) -> Dict:
        """
        Get current session status.
        
        Args:
            session_id: Session ID to check
            
        Returns:
            Session status data
        """
        try:
            result = self._make_request("GET", f"sessions/{session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise
            
    def is_session_complete(self, session_id: str) -> bool:
        """
        Check if user has completed photo selection.
        
        Args:
            session_id: Session ID to check
            
        Returns:
            True if selection is complete
        """
        try:
            session = self.get_session(session_id)
            return session.get("mediaItemsSet", False)
            
        except Exception as e:
            logger.error(f"Failed to check session completion: {e}")
            return False
            
    def list_media_items(self, session_id: str, page_size: int = 100) -> List[Dict]:
        """
        List media items selected in session.
        
        Args:
            session_id: Session ID
            page_size: Maximum items per page
            
        Returns:
            List of media item data
        """
        try:
            media_items = []
            page_token = None
            
            while True:
                params = {
                    "sessionId": session_id,
                    "pageSize": page_size
                }
                
                if page_token:
                    params["pageToken"] = page_token
                    
                result = self._make_request("GET", "mediaItems", params=params)
                
                items = result.get("mediaItems", [])
                media_items.extend(items)
                
                page_token = result.get("nextPageToken")
                if not page_token:
                    break
                    
            logger.info(f"Retrieved {len(media_items)} media items from session {session_id}")
            return media_items
            
        except Exception as e:
            logger.error(f"Failed to list media items for session {session_id}: {e}")
            raise
            
    def poll_until_complete(self, session_id: str, timeout: int = 300, 
                          callback: Optional[callable] = None) -> bool:
        """
        Poll session until user completes selection or timeout.
        
        Args:
            session_id: Session ID to poll
            timeout: Maximum time to wait in seconds
            callback: Optional callback function called on each poll
            
        Returns:
            True if session completed successfully, False if timeout
        """
        start_time = time.time()
        poll_count = 0
        
        logger.info(f"Starting to poll session {session_id} (timeout: {timeout}s)")
        
        while time.time() - start_time < timeout:
            try:
                session = self.get_session(session_id)
                poll_count += 1
                
                if callback:
                    callback(session, poll_count)
                    
                if session.get("mediaItemsSet", False):
                    elapsed = time.time() - start_time
                    logger.info(f"Session {session_id} completed after {elapsed:.1f}s ({poll_count} polls)")
                    return True
                    
                # Use recommended polling interval from response
                polling_config = session.get("pollingConfig", {})
                interval_str = polling_config.get("pollInterval", "10s")
                
                # Parse interval (format: "10s", "30s", etc.)
                interval = self._parse_interval(interval_str)
                
                logger.debug(f"Polling session {session_id} (attempt {poll_count}), "
                           f"waiting {interval}s for next poll")
                           
                time.sleep(interval)
                
            except Exception as e:
                logger.warning(f"Error during polling (attempt {poll_count}): {e}")
                # Continue polling despite errors
                time.sleep(10)  # Default fallback interval
                
        elapsed = time.time() - start_time
        logger.warning(f"Session {session_id} timed out after {elapsed:.1f}s ({poll_count} polls)")
        return False
        
    def _parse_interval(self, interval_str: str) -> int:
        """
        Parse polling interval string to seconds.
        
        Args:
            interval_str: Interval string like "10s", "30s"
            
        Returns:
            Interval in seconds
        """
        try:
            if interval_str.endswith('s'):
                return int(interval_str[:-1])
            else:
                return int(interval_str)
        except (ValueError, TypeError):
            logger.warning(f"Could not parse interval '{interval_str}', using default 10s")
            return 10