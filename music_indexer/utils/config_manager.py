"""
Configuration manager for the music indexer application.
Handles reading/writing settings to config file.
"""
import os
import configparser
import json

DEFAULT_CONFIG = {
    "app": {
        "name": "Music Indexer",
        "version": "0.1.0",
        "log_level": "INFO",
    },
    "paths": {
        "music_directories": [],
        "default_export_directory": "./",
    },
    "indexing": {
        "supported_formats": ["mp3", "flac", "m4a", "aac", "wav"],
        "cache_file": "cache/music_cache.db",
    },
    "search": {
        "similarity_threshold": 75,  # Default threshold for fuzzy matching (0-100)
        # NEW: Configurable suffix removal
        "ignore_suffixes": ["justify", "sob", "nrg", "dps", "trt", "pms"],
    },
}


class ConfigManager:
    """Manages application configuration settings."""

    def __init__(self, config_file="config.ini"):
        """Initialize configuration manager with specified config file."""
        # Make sure config_file is not empty
        self.config_file = config_file or "config.ini"
        self.config = configparser.ConfigParser()
        
        # Load configuration or create default if not exists
        if os.path.exists(self.config_file):
            self.load_config()
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration file."""
        for section, options in DEFAULT_CONFIG.items():
            self.config[section] = {}
            for key, value in options.items():
                # Handle lists by converting to JSON string
                if isinstance(value, list):
                    self.config[section][key] = json.dumps(value)
                else:
                    self.config[section][key] = str(value)
        
        self.save_config()
        
    def load_config(self):
        """Load configuration from file."""
        self.config.read(self.config_file)
        
    def save_config(self):
        """Save current configuration to file."""
    # Ensure the directory exists only if there's a directory specified
        dirname = os.path.dirname(self.config_file)
        if dirname:  # Only try to create directories if there's a directory path
            os.makedirs(dirname, exist_ok=True)
    
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
    
    def get(self, section, key, fallback=None):
        """Get configuration value."""
        value = self.config.get(section, key, fallback=fallback)
        
        # Try to parse JSON for list/dict values
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
            
    def set(self, section, key, value):
        """Set configuration value."""
        if section not in self.config:
            self.config[section] = {}
            
        # Convert lists/dicts to JSON strings
        if isinstance(value, (list, dict)):
            value = json.dumps(value)
        else:
            value = str(value)
            
        self.config[section][key] = value
        self.save_config()
        
    def add_music_directory(self, directory_path):
        """Add a music directory to the configuration."""
        if os.path.exists(directory_path):
            music_dirs = self.get("paths", "music_directories", fallback=[])
            if directory_path not in music_dirs:
                music_dirs.append(directory_path)
                self.set("paths", "music_directories", music_dirs)
                return True
        return False
    
    def remove_music_directory(self, directory_path):
        """Remove a music directory from the configuration."""
        music_dirs = self.get("paths", "music_directories", fallback=[])
        if directory_path in music_dirs:
            music_dirs.remove(directory_path)
            self.set("paths", "music_directories", music_dirs)
            return True
        return False
    
    def get_supported_formats(self):
        """Get list of supported audio formats."""
        return self.get("indexing", "supported_formats")
    
    def get_similarity_threshold(self):
        """Get similarity threshold for fuzzy matching."""
        return int(self.get("search", "similarity_threshold", fallback=75))
    
    def set_similarity_threshold(self, threshold):
        """Set similarity threshold for fuzzy matching."""
        # Ensure threshold is between 0 and 100
        threshold = max(0, min(100, int(threshold)))
        self.set("search", "similarity_threshold", threshold)
