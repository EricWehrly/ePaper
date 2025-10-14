"""
Google Photos media download manager.
"""

import os
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

class GooglePhotosDownloader:
    """Downloads media items from Google Photos."""
    
    def __init__(self, credentials: Credentials, download_dir: str = "pic-raw"):
        """
        Initialize downloader.
        
        Args:
            credentials: Valid OAuth 2.0 credentials
            download_dir: Directory to save downloaded files
        """
        self.credentials = credentials
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized downloader with directory: {self.download_dir}")
        
    def download_media_item(self, media_item: Dict, max_size: Optional[int] = None) -> Optional[str]:
        """
        Download a single media item.
        
        Args:
            media_item: Media item data from Picker API
            max_size: Optional maximum dimension for images
            
        Returns:
            Local file path if successful, None if failed
        """
        try:
            # Extract download information
            media_file = media_item.get("mediaFile", {})
            base_url = media_file.get("baseUrl")
            filename = media_item.get("filename", "unknown")
            
            if not base_url:
                logger.error(f"No baseUrl found for media item: {media_item.get('id', 'unknown')}")
                return None
                
            # Construct download URL
            download_url = self._build_download_url(base_url, media_item, max_size)
            
            # Generate local filename
            local_filename = self._generate_filename(filename, media_item)
            file_path = self.download_dir / local_filename
            
            # Download the file
            success = self._download_file(download_url, file_path)
            
            if success:
                logger.info(f"Downloaded: {local_filename}")
                return str(file_path)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to download media item: {e}")
            return None
            
    def download_all(self, media_items: List[Dict], max_size: Optional[int] = None) -> List[str]:
        """
        Download all media items.
        
        Args:
            media_items: List of media item data
            max_size: Optional maximum dimension for images
            
        Returns:
            List of successfully downloaded file paths
        """
        downloaded_paths = []
        
        logger.info(f"Starting download of {len(media_items)} media items")
        
        for i, item in enumerate(media_items, 1):
            logger.debug(f"Downloading item {i}/{len(media_items)}")
            
            path = self.download_media_item(item, max_size)
            if path:
                downloaded_paths.append(path)
            else:
                logger.warning(f"Failed to download item {i}")
                
        success_rate = len(downloaded_paths) / len(media_items) * 100 if media_items else 0
        logger.info(f"Download complete: {len(downloaded_paths)}/{len(media_items)} "
                   f"files ({success_rate:.1f}% success)")
                   
        return downloaded_paths
        
    def _build_download_url(self, base_url: str, media_item: Dict, max_size: Optional[int]) -> str:
        """
        Build download URL with appropriate parameters.
        
        Args:
            base_url: Base URL from media item
            media_item: Full media item data
            max_size: Optional maximum dimension
            
        Returns:
            Complete download URL
        """
        media_file = media_item.get("mediaFile", {})
        mime_type = media_file.get("mimeType", "")
        
        # For videos, use 'dv' parameter to download video file
        if mime_type.startswith("video/"):
            return f"{base_url}=dv"
            
        # For images, use size parameters or 'd' for full download
        if max_size:
            # Download with maximum dimension constraint
            return f"{base_url}=w{max_size}-h{max_size}"
        else:
            # Download full resolution with metadata (except location)
            return f"{base_url}=d"
            
    def _download_file(self, url: str, file_path: Path) -> bool:
        """
        Download file from URL to local path.
        
        Args:
            url: Download URL
            file_path: Local path to save file
            
        Returns:
            True if successful
        """
        try:
            # Ensure credentials are fresh
            if self.credentials.expired:
                self.credentials.refresh(requests.Request())
                
            headers = {
                "Authorization": f"Bearer {self.credentials.token}"
            }
            
            # Stream download for large files
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Save file in chunks
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            # Verify file was created and has content
            if file_path.exists() and file_path.stat().st_size > 0:
                return True
            else:
                logger.error(f"Downloaded file is empty or missing: {file_path}")
                return False
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error downloading file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False
            
    def _generate_filename(self, original_filename: str, media_item: Dict) -> str:
        """
        Generate safe local filename.
        
        Args:
            original_filename: Original filename from Google Photos
            media_item: Media item data for fallback info
            
        Returns:
            Safe filename for local storage
        """
        # Start with original filename
        filename = original_filename or "unknown"
        
        # Remove any path separators for security
        filename = os.path.basename(filename)
        
        # If no extension, add one based on MIME type
        if '.' not in filename:
            mime_type = media_item.get("mediaFile", {}).get("mimeType", "")
            extension = self._get_extension_from_mime(mime_type)
            filename = f"{filename}{extension}"
            
        # Handle filename conflicts
        file_path = self.download_dir / filename
        if file_path.exists():
            base, ext = os.path.splitext(filename)
            counter = 1
            
            while file_path.exists():
                filename = f"{base}_{counter}{ext}"
                file_path = self.download_dir / filename
                counter += 1
                
        return filename
        
    def _get_extension_from_mime(self, mime_type: str) -> str:
        """
        Get file extension from MIME type.
        
        Args:
            mime_type: MIME type string
            
        Returns:
            File extension including dot
        """
        mime_to_ext = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg", 
            "image/png": ".png",
            "image/gif": ".gif",
            "image/bmp": ".bmp",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
            "video/avi": ".avi",
            "video/mov": ".mov",
            "video/quicktime": ".mov"
        }
        
        return mime_to_ext.get(mime_type.lower(), ".jpg")  # Default to .jpg
        
    def get_download_stats(self) -> Dict:
        """
        Get statistics about downloads in the download directory.
        
        Returns:
            Dictionary with download statistics
        """
        if not self.download_dir.exists():
            return {"total_files": 0, "total_size": 0}
            
        files = list(self.download_dir.iterdir())
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        
        return {
            "total_files": len(files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }