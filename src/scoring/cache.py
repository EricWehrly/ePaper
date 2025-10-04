"""
Cache management for scoring results.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ScoringCache:
    """Manages on-disk caching of scoring results with mtime validation."""
    
    def __init__(self, cache_filename: str = '.score_cache.json'):
        self._cache_filename = cache_filename
        self._cache_lock = threading.Lock()
    
    def get_cached_score(self, image_path: Path, original_path: Path) -> Optional[Dict]:
        """
        Retrieve cached score if mtimes match.
        
        Returns:
            Dict with cached scores or None if cache miss/invalid
        """
        try:
            cache_path = image_path.parent / self._cache_filename
            if not cache_path.exists():
                return None
                
            cache = self._load_cache(cache_path)
            if not cache:
                return None
                
            cache_key = str(image_path.name)
            cached_entry = cache.get(cache_key)
            
            if not cached_entry:
                return None
                
            # Validate mtimes
            image_mtime = image_path.stat().st_mtime
            original_mtime = original_path.stat().st_mtime
            
            if (cached_entry.get('image_mtime') == image_mtime and
                    cached_entry.get('original_mtime') == original_mtime):
                return cached_entry.get('scores')
                
            return None
            
        except Exception as e:
            logger.debug(f"Cache read error for {image_path.name}: {e}")
            return None
    
    def store_score(self, image_path: Path, original_path: Path, scores: Dict) -> None:
        """
        Store scores in cache with current mtimes.
        
        Args:
            image_path: Path to converted image
            original_path: Path to original image  
            scores: Scoring results to cache
        """
        try:
            cache_path = image_path.parent / self._cache_filename
            image_mtime = image_path.stat().st_mtime
            original_mtime = original_path.stat().st_mtime
            
            with self._cache_lock:
                cache = self._load_cache(cache_path)
                
                cache_key = str(image_path.name)
                cache[cache_key] = {
                    'image_mtime': image_mtime,
                    'original_mtime': original_mtime,
                    'scores': scores
                }
                
                self._save_cache(cache_path, cache)
                
        except Exception as e:
            logger.debug(f"Cache write error for {image_path.name}: {e}")
            # Don't let cache errors break scoring
            pass
    
    def _load_cache(self, cache_path: Path) -> Dict:
        """Load cache from disk, returning empty dict on error."""
        try:
            if cache_path.exists():
                with open(cache_path, 'r', encoding='utf-8') as fh:
                    return json.load(fh)
        except Exception:
            pass
        return {}
    
    def _save_cache(self, cache_path: Path, cache: Dict) -> None:
        """Save cache to disk atomically."""
        # Write to temporary file first, then rename for atomicity
        tmp_path = cache_path.with_suffix('.tmp')
        with open(tmp_path, 'w', encoding='utf-8') as fh:
            json.dump(cache, fh, ensure_ascii=False, indent=2)
            fh.flush()
        tmp_path.replace(cache_path)
    
    def clear_cache(self, directory: Path) -> bool:
        """
        Clear cache file in the given directory.
        
        Returns:
            True if cache was cleared or didn't exist, False on error
        """
        try:
            cache_path = directory / self._cache_filename
            if cache_path.exists():
                cache_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache in {directory}: {e}")
            return False