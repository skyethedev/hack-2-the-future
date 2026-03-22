import json
import os
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "work_duration": 25,
            "break_duration": 5,
            "strict_mode": False,
            "skin": "classic",
            "work_apps": ["Visual Studio", "Code", "Docs", "Word", "Cursor", "Notepad", "Stack Overflow", "GitHub", "ChatGPT", "Google",],
            "distracting_apps": ["YouTube", "Twitter", "X", "Reddit", "Netflix", "TikTok", "Instagram"]
        }
        self.config = self.load_config()

    def load_config(self):
        """Loads configuration from config.json. Creates it with defaults if not found."""
        if not os.path.exists(self.config_file):
            self.save_config(self.default_config)
            return self.default_config.copy()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Fill missing keys with defaults
                for key, value in self.default_config.items():
                    if key not in loaded:
                        loaded[key] = value
                return loaded
        except (json.JSONDecodeError, IOError):
            # If file is corrupted, return defaults but don't overwrite user file immediately
            return self.default_config.copy()

    def save_config(self, config_data=None):
        """Saves current configuration to config.json."""
        if config_data is None:
            config_data = self.config

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
        
        self.config = config_data

    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set a configuration value and save."""
        self.config[key] = value
        self.save_config()
