"""
Settings management for ePaper display.

Settings are loaded from JSON with defaults applied for missing values.
Settings are only saved when explicitly changed, not on load.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Default settings - single source of truth
DEFAULT_SETTINGS = {
    'app_name': 'ePaper',
    'mode': 'image',           # 'image', 'carousel', or 'playlist'
    'autoplay': False,         # server-driven carousel active
    'interval_sec': 30,        # seconds between images in carousel
    'orientation': 'portrait', # 'portrait' | 'landscape'
    'playlist': {              # playlist-specific settings
        'current_id': None,    # ID of currently playing playlist
        'current_index': 0,    # Current image index in playlist
        'loop': True           # Whether to loop playlist
    },
    'ngrok_redirect': {        # ngrok redirect banner configuration
        'enabled': True,
        'countdown_seconds': 7
    }
}


class Settings:
    """Manages application settings with file persistence."""
    
    def __init__(self, settings_path: Path):
        self.settings_path = settings_path
        self._settings = {}
        self.load()
    
    def load(self):
        """Load settings from file, applying defaults for missing values."""
        # Start with defaults
        self._settings = self._deep_copy(DEFAULT_SETTINGS)
        
        # Load from file if it exists
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r') as f:
                    file_data = json.load(f)
                
                if isinstance(file_data, dict):
                    # Merge file data into defaults
                    self._deep_merge(self._settings, file_data)
                    logger.info(f"Loaded settings from {self.settings_path}")
            except Exception as e:
                logger.warning(f"Failed to load settings: {e}")
    
    def save(self):
        """Save current settings to file."""
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_path, 'w') as f:
                json.dump(self._settings, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save settings: {e}")
    
    def get(self, key: str, default=None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a setting value and save to file."""
        self._settings[key] = value
        self.save()
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple settings and save once."""
        self._settings.update(updates)
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self._settings.copy()
    
    @staticmethod
    def _deep_copy(obj):
        """Deep copy a dict/list structure."""
        if isinstance(obj, dict):
            return {k: Settings._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [Settings._deep_copy(item) for item in obj]
        else:
            return obj
    
    @staticmethod
    def _deep_merge(target: dict, source: dict):
        """Deep merge source into target dict."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                Settings._deep_merge(target[key], value)
            else:
                target[key] = value
