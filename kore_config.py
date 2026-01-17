import json
import os

class KoreConfig:
    """Configuration manager for Kore"""
    
    def __init__(self):
        self.config_file = "kore_config.json"
        self.defaults = {
            "behavior": {
                "animation_speed": 0.1,
                "search_timeout": 10,
                "max_file_size_mb": 50,
                "confirm_destructive_actions": True
            },
            "shortcuts": {
                "create_file": "ctrl+shift+f",
                "create_folder": "ctrl+shift+d",
                "quick_search": "ctrl+space"
            },
            "file_types": {
                "text": [".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".xml"],
                "document": [".doc", ".docx", ".pdf", ".ppt", ".pptx", ".xls", ".xlsx"],
                "media": [".jpg", ".png", ".gif", ".mp4", ".mp3", ".avi", ".mov"]
            },
            "smart_folders": {
                "work": ["*.doc", "*.pdf", "*.xls"],
                "code": ["*.py", "*.js", "*.html", "*.css"],
                "media": ["*.jpg", "*.png", "*.mp4"]
            }
        }
        self.load_config()
    
    def load_config(self):
        """Load or create configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            # Merge with defaults for missing keys
            for category, values in self.defaults.items():
                if category not in self.config:
                    self.config[category] = values
                else:
                    for key, value in values.items():
                        if key not in self.config[category]:
                            self.config[category][key] = value
        else:
            self.config = self.defaults
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, category, key=None):
        """Get configuration value"""
        if key:
            return self.config.get(category, {}).get(key)
        return self.config.get(category, {})
    
    def set(self, category, key, value):
        """Set configuration value"""
        if category not in self.config:
            self.config[category] = {}
        self.config[category][key] = value
        self.save_config()

config = KoreConfig()