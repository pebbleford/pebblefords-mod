"""
Configuration and settings management for Among Us Mod Manager.
Stores settings in %APPDATA%/AmongUsModManager/
"""

import json
import os
from pathlib import Path

APP_NAME = "AmongUsModManager"
APP_VERSION = "1.0.0"

def get_app_data_dir() -> Path:
    """Get the application data directory."""
    appdata = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
    path = Path(appdata) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_mods_cache_dir() -> Path:
    """Get the directory for cached mod downloads."""
    path = get_app_data_dir() / "cache"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_profiles_dir() -> Path:
    """Get the directory for mod profiles."""
    path = get_app_data_dir() / "profiles"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_backups_dir() -> Path:
    """Get the directory for mod backups."""
    path = get_app_data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path

SETTINGS_FILE = get_app_data_dir() / "settings.json"

DEFAULT_SETTINGS = {
    "among_us_path": "",
    "theme": "dark",
    "auto_update_check": True,
    "last_profile": "default",
    "window_width": 1000,
    "window_height": 650,
    "favorite_mods": [],
}


class Settings:
    """Manages application settings."""

    def __init__(self):
        self._data = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except OSError:
            pass

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        self.save()
