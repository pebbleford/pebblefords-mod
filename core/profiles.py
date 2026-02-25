"""
Mod profile management.
Profiles save which mods are enabled/disabled so you can quickly switch configurations.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

from core.config import get_profiles_dir


class Profile:
    """A saved mod configuration."""

    def __init__(self, name: str, mods: list[dict] | None = None,
                 description: str = "", created: str = ""):
        self.name = name
        self.mods = mods or []
        self.description = description
        self.created = created or datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "mods": self.mods,
            "description": self.description,
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        return cls(
            name=data["name"],
            mods=data.get("mods", []),
            description=data.get("description", ""),
            created=data.get("created", ""),
        )


class ProfileManager:
    """Manages mod profiles."""

    def __init__(self):
        self.profiles_dir = get_profiles_dir()

    def _profile_path(self, name: str) -> Path:
        safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
        return self.profiles_dir / f"{safe_name}.json"

    def save_profile(self, name: str, mods: list, description: str = "") -> Profile:
        """Save the current mod state as a profile."""
        mod_data = []
        for mod in mods:
            if hasattr(mod, "to_dict"):
                mod_data.append(mod.to_dict())
            elif isinstance(mod, dict):
                mod_data.append(mod)

        profile = Profile(name=name, mods=mod_data, description=description)
        path = self._profile_path(name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2)
        return profile

    def load_profile(self, name: str) -> Profile:
        """Load a profile by name."""
        path = self._profile_path(name)
        if not path.exists():
            raise FileNotFoundError(f"Profile '{name}' not found")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Profile.from_dict(data)

    def delete_profile(self, name: str):
        """Delete a profile."""
        path = self._profile_path(name)
        if path.exists():
            path.unlink()

    def list_profiles(self) -> list[Profile]:
        """List all saved profiles."""
        profiles = []
        for f in sorted(self.profiles_dir.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                profiles.append(Profile.from_dict(data))
            except (json.JSONDecodeError, OSError, KeyError):
                continue
        return profiles

    def apply_profile(self, profile: Profile, mod_manager) -> dict:
        """
        Apply a profile to the current mod setup.
        Returns a summary of changes made.
        """
        changes = {"enabled": [], "disabled": [], "missing": []}
        current_mods = mod_manager.get_installed_mods()
        current_by_name = {m.name: m for m in current_mods}

        # Build set of mod names that should be enabled
        profile_enabled = set()
        profile_disabled = set()
        for mod_data in profile.mods:
            name = mod_data.get("name", "")
            if mod_data.get("enabled", True):
                profile_enabled.add(name)
            else:
                profile_disabled.add(name)

        # Apply state changes
        for mod in current_mods:
            if mod.name in profile_enabled and not mod.enabled:
                mod_manager.enable_mod(mod)
                changes["enabled"].append(mod.name)
            elif mod.name in profile_disabled and mod.enabled:
                mod_manager.disable_mod(mod)
                changes["disabled"].append(mod.name)

        # Check for mods in profile but not installed
        installed_names = set(current_by_name.keys())
        for mod_data in profile.mods:
            name = mod_data.get("name", "")
            if name and name not in installed_names:
                changes["missing"].append(name)

        return changes

    def rename_profile(self, old_name: str, new_name: str):
        """Rename a profile."""
        old_path = self._profile_path(old_name)
        if not old_path.exists():
            raise FileNotFoundError(f"Profile '{old_name}' not found")

        with open(old_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["name"] = new_name
        new_path = self._profile_path(new_name)

        with open(new_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        old_path.unlink()

    def duplicate_profile(self, name: str, new_name: str) -> Profile:
        """Duplicate a profile with a new name."""
        profile = self.load_profile(name)
        profile.name = new_name
        profile.created = datetime.now().isoformat()
        return self.save_profile(new_name, profile.mods, profile.description)
