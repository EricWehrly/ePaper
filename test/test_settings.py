"""
Simple unit tests for Settings class.
Tests that settings load with defaults and save on change.
"""
import unittest
import json
import tempfile
from pathlib import Path

from src.settings import Settings, DEFAULT_SETTINGS


class TestSettings(unittest.TestCase):
    """Test settings management."""
    
    def setUp(self):
        """Create temp directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.settings_file = Path(self.temp_dir) / 'settings.json'
        
    def tearDown(self):
        """Clean up temp directory."""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_load_with_defaults_when_file_missing(self):
        """Settings should use defaults when file doesn't exist."""
        settings = Settings(self.settings_file)
        
        # Should have all default values
        self.assertEqual(settings.get('app_name'), 'ePaper')
        self.assertEqual(settings.get('mode'), 'image')
        self.assertEqual(settings.get('orientation'), 'portrait')
        
        # File should not be created yet (only save on change)
        self.assertFalse(self.settings_file.exists())
    
    def test_load_from_file_preserves_custom_values(self):
        """Settings should load custom values from file."""
        # Create file with custom values
        custom_data = {
            'app_name': 'MyDisplay',
            'mode': 'carousel',
            'orientation': 'landscape'
        }
        with open(self.settings_file, 'w') as f:
            json.dump(custom_data, f)
        
        # Load settings
        settings = Settings(self.settings_file)
        
        # Should have custom values
        self.assertEqual(settings.get('app_name'), 'MyDisplay')
        self.assertEqual(settings.get('mode'), 'carousel')
        self.assertEqual(settings.get('orientation'), 'landscape')
        
        # Should still have defaults for missing keys
        self.assertEqual(settings.get('autoplay'), False)
        self.assertEqual(settings.get('interval_sec'), 30)
    
    def test_set_saves_to_file(self):
        """Setting a value should save to file."""
        settings = Settings(self.settings_file)
        
        # Change a value
        settings.set('app_name', 'TestDisplay')
        
        # File should now exist
        self.assertTrue(self.settings_file.exists())
        
        # File should contain the new value
        with open(self.settings_file, 'r') as f:
            data = json.load(f)
        self.assertEqual(data['app_name'], 'TestDisplay')
    
    def test_update_multiple_saves_once(self):
        """Update should save multiple changes at once."""
        settings = Settings(self.settings_file)
        
        # Update multiple values
        settings.update({
            'app_name': 'MultiTest',
            'mode': 'playlist',
            'orientation': 'landscape'
        })
        
        # File should contain all changes
        with open(self.settings_file, 'r') as f:
            data = json.load(f)
        self.assertEqual(data['app_name'], 'MultiTest')
        self.assertEqual(data['mode'], 'playlist')
        self.assertEqual(data['orientation'], 'landscape')
    
    def test_nested_settings_merge_correctly(self):
        """Nested dict settings should merge with defaults."""
        # File with partial playlist settings
        partial_data = {
            'playlist': {
                'current_id': 'test_playlist'
                # Missing current_index and loop
            }
        }
        with open(self.settings_file, 'w') as f:
            json.dump(partial_data, f)
        
        settings = Settings(self.settings_file)
        
        # Should have custom value
        playlist = settings.get('playlist')
        self.assertEqual(playlist['current_id'], 'test_playlist')
        
        # Should have defaults for missing nested keys
        self.assertEqual(playlist['current_index'], 0)
        self.assertEqual(playlist['loop'], True)
    
    def test_load_preserves_unknown_keys(self):
        """Loading should preserve unknown keys from file."""
        # File with unknown key
        data = {
            'app_name': 'TestApp',
            'custom_key': 'custom_value',
            'another_key': 123
        }
        with open(self.settings_file, 'w') as f:
            json.dump(data, f)
        
        settings = Settings(self.settings_file)
        
        # Unknown keys should be preserved
        self.assertEqual(settings.get('custom_key'), 'custom_value')
        self.assertEqual(settings.get('another_key'), 123)
        
        # Change something and save
        settings.set('mode', 'carousel')
        
        # Unknown keys should still be in file
        with open(self.settings_file, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data['custom_key'], 'custom_value')
        self.assertEqual(saved_data['another_key'], 123)


if __name__ == '__main__':
    unittest.main()
