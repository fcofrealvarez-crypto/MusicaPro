import json
import os
from datetime import datetime

HISTORY_FILE = "history.json"

class HistoryManager:
    def __init__(self):
        self.history = []
        self.load()

    def load(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    self.history = json.load(f)
            except Exception as e:
                print(f"Error loading history: {e}")
                self.history = []

    def save(self):
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_entry(self, title, artist, file_path, format_ext):
        entry = {
            "title": title,
            "artist": artist,
            "file_path": file_path,
            "format": format_ext,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        # Insert at beginning
        self.history.insert(0, entry)
        # Optional: Limit history size (e.g., 100 entries)
        if len(self.history) > 100:
            self.history.pop()
        self.save()

    def get_all(self):
        return self.history

    def clear(self):
        self.history = []
        self.save()
