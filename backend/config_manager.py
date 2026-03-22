import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "download_path": "downloads",
    "default_format": "mp3",
    "bass_reduction": False,
    "theme_mode": "dark",
    "check_updates": True
}

class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    # Update defaults with loaded data (preserves new keys if defaults change)
                    self.config.update(data)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key):
        return self.config.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()
