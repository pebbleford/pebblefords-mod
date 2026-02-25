"""
Mod catalog - curated list of Among Us mods with metadata.
Mirrors the original Mod Manager's approach of having a known mod list
that users can check/uncheck and batch install.
"""

import json
import os
from pathlib import Path
from urllib import request

from core.config import get_app_data_dir

CATALOG_CACHE_FILE = get_app_data_dir() / "mod_catalog.json"

# Curated mod catalog - similar to what the original Mod Manager offered
# Each entry has: name, author, description, github (owner/repo), category, tags
DEFAULT_CATALOG = [
    # ── Compatible with Among Us v17.2.1 (Feb 2026) ──
    # ── Roles Mods ──
    {
        "id": "town-of-host-enhanced",
        "name": "Town of Host Enhanced",
        "author": "0xDrMoe",
        "description": "Host-only mod with 200+ roles. No installation needed for other players. Actively maintained!",
        "github": "0xDrMoe/TownofHost-Enhanced",
        "category": "Roles",
        "tags": ["roles", "host-only", "popular", "compatible"],
        "dependencies": [],
    },
    {
        "id": "extreme-roles",
        "name": "Extreme Roles",
        "author": "yukieiji",
        "description": "Adds many unique roles and abilities. Actively maintained and updated for latest Among Us.",
        "github": "yukieiji/ExtremeRoles",
        "category": "Roles",
        "tags": ["roles", "compatible"],
        "dependencies": [],
    },
    {
        "id": "theother-roles",
        "name": "The Other Roles",
        "author": "TheOtherRolesAU",
        "description": "Adds many custom roles like Sheriff, Engineer, Jester, and more. WARNING: Not updated for latest Among Us - may not work!",
        "github": "TheOtherRolesAU/TheOtherRoles",
        "category": "Roles",
        "tags": ["roles", "popular", "full-package", "outdated"],
        "dependencies": ["reactor"],
    },
    {
        "id": "town-of-us-r",
        "name": "Town Of Us Reactivated",
        "author": "eDonnes",
        "description": "Adds new roles, modifiers, and game settings. WARNING: Not updated since April 2025 - may not work!",
        "github": "eDonnes124/Town-Of-Us-R",
        "category": "Roles",
        "tags": ["roles", "outdated"],
        "dependencies": ["reactor"],
    },
    # ── Maps ──
    {
        "id": "submerged",
        "name": "Submerged",
        "author": "SubmergedAmongUs",
        "description": "Adds the Submerged map - an underwater submarine map. Updated for v17.1, may work with v17.2.",
        "github": "SubmergedAmongUs/Submerged",
        "category": "Maps",
        "tags": ["map", "popular"],
        "dependencies": ["reactor"],
    },
    # ── Frameworks ──
    {
        "id": "reactor",
        "name": "Reactor",
        "author": "NuclearPowered",
        "description": "Modding API framework for Among Us. Required by some mods. Officially supports up to v17.0.1.",
        "github": "NuclearPowered/Reactor",
        "category": "Frameworks",
        "tags": ["framework", "api"],
        "dependencies": [],
    },
    {
        "id": "bepinex",
        "name": "BepInEx (IL2CPP)",
        "author": "BepInEx",
        "description": "Unity mod loader. Required for all mods to work.",
        "github": "BepInEx/BepInEx",
        "category": "Frameworks",
        "tags": ["framework", "required"],
        "dependencies": [],
    },
    # ── Custom / Built-in ──
    {
        "id": "pebblefords-mod",
        "name": "Pebbleford's Mod",
        "author": "Pebbleford",
        "description": "Custom mod with Sheriff, Jester, Mayor, Seer roles + hack menu (ESP, No Clip, Speed Hack, Kill Aura, Teleport, Sabotage, and more). Press INSERT in-game to open hack menu.",
        "github": "",
        "category": "Custom",
        "tags": ["roles", "hacks", "custom", "compatible", "built-in"],
        "dependencies": [],
        "local_dll": "custom_mod/bin/Release/net6.0/CustomMod.dll",
    },
]


class CatalogMod:
    """A mod entry from the catalog."""

    def __init__(self, data: dict):
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.author = data.get("author", "")
        self.description = data.get("description", "")
        self.github = data.get("github", "")
        self.category = data.get("category", "Other")
        self.tags = data.get("tags", [])
        self.dependencies = data.get("dependencies", [])
        self.local_dll = data.get("local_dll", "")
        # Filled after fetching release info
        self.version = data.get("version", "")
        self.download_url = data.get("download_url", "")
        self.file_size = data.get("file_size", 0)
        self.download_count = data.get("download_count", 0)
        self.stars = data.get("stars", 0)
        self.updated = data.get("updated", "")
        # State
        self.installed = data.get("installed", False)
        self.selected = data.get("selected", False)
        self.installed_version = data.get("installed_version", "")
        self.has_update = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "author": self.author,
            "description": self.description,
            "github": self.github,
            "category": self.category,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "local_dll": self.local_dll,
            "version": self.version,
            "download_url": self.download_url,
            "file_size": self.file_size,
            "download_count": self.download_count,
            "stars": self.stars,
            "updated": self.updated,
            "installed": self.installed,
            "selected": self.selected,
            "installed_version": self.installed_version,
        }

    @property
    def size_str(self) -> str:
        size = self.file_size
        if size == 0:
            return ""
        for unit in ("B", "KB", "MB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} GB"

    @property
    def repo_url(self) -> str:
        if self.github:
            return f"https://github.com/{self.github}"
        return ""


class ModCatalog:
    """Manages the curated mod catalog with GitHub release fetching."""

    def __init__(self):
        self._mods: list[CatalogMod] = []
        self._load_catalog()

    def _load_catalog(self):
        """Load catalog from cache, merging in any new fields from defaults."""
        # Build a lookup of default entries by id
        defaults_by_id = {d["id"]: d for d in DEFAULT_CATALOG}

        if CATALOG_CACHE_FILE.exists():
            try:
                with open(CATALOG_CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Merge default fields into cached entries (picks up new fields like dependencies)
                cached_ids = set()
                for entry in data:
                    cached_ids.add(entry.get("id", ""))
                    default = defaults_by_id.get(entry.get("id", ""), {})
                    for key, value in default.items():
                        if key not in entry:
                            entry[key] = value
                # Add any new default entries not in cache
                for default_entry in DEFAULT_CATALOG:
                    if default_entry["id"] not in cached_ids:
                        data.append(default_entry)
                self._mods = [CatalogMod(m) for m in data]
                return
            except (json.JSONDecodeError, OSError):
                pass

        self._mods = [CatalogMod(m) for m in DEFAULT_CATALOG]

    def _save_catalog(self):
        try:
            with open(CATALOG_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump([m.to_dict() for m in self._mods], f, indent=2)
        except OSError:
            pass

    def get_mods(self) -> list[CatalogMod]:
        return self._mods

    def get_categories(self) -> list[str]:
        cats = []
        seen = set()
        for mod in self._mods:
            if mod.category not in seen:
                cats.append(mod.category)
                seen.add(mod.category)
        return cats

    def get_mods_by_category(self, category: str) -> list[CatalogMod]:
        return [m for m in self._mods if m.category == category]

    def get_selected_mods(self) -> list[CatalogMod]:
        return [m for m in self._mods if m.selected]

    def get_installed_mods(self) -> list[CatalogMod]:
        return [m for m in self._mods if m.installed]

    def get_mod_by_id(self, mod_id: str) -> CatalogMod | None:
        for m in self._mods:
            if m.id == mod_id:
                return m
        return None

    def get_dependencies(self, mod: CatalogMod) -> list[CatalogMod]:
        """Get all dependencies for a mod that aren't already installed.
        Returns them in install order (deepest deps first)."""
        needed = []
        seen = set()

        def _resolve(m: CatalogMod):
            for dep_id in m.dependencies:
                if dep_id in seen:
                    continue
                seen.add(dep_id)
                dep = self.get_mod_by_id(dep_id)
                if dep and not dep.installed:
                    _resolve(dep)  # resolve transitive deps first
                    needed.append(dep)

        _resolve(mod)
        return needed

    def fetch_release_info(self, mod: CatalogMod) -> bool:
        """Fetch latest release info from GitHub for a single mod."""
        if not mod.github:
            return False
        try:
            owner, repo = mod.github.split("/")
            url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            req = request.Request(url, headers={
                "User-Agent": "AmongUsModManager/1.0",
                "Accept": "application/vnd.github.v3+json",
            })
            with request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            mod.version = data.get("tag_name", "")
            mod.updated = data.get("published_at", "")[:10]

            # Find the best asset (prefer zip, then dll)
            for asset in data.get("assets", []):
                name = asset["name"].lower()
                if name.endswith(".zip") or name.endswith(".dll"):
                    mod.download_url = asset["browser_download_url"]
                    mod.file_size = asset.get("size", 0)
                    mod.download_count = asset.get("download_count", 0)
                    break

            # Get star count
            repo_url = f"https://api.github.com/repos/{owner}/{repo}"
            req2 = request.Request(repo_url, headers={
                "User-Agent": "AmongUsModManager/1.0",
                "Accept": "application/vnd.github.v3+json",
            })
            with request.urlopen(req2, timeout=10) as resp2:
                repo_data = json.loads(resp2.read().decode())
            mod.stars = repo_data.get("stargazers_count", 0)

            return True
        except Exception:
            return False

    def fetch_all_releases(self, progress_callback=None) -> int:
        """Fetch release info for all mods. Returns count of successfully fetched."""
        success = 0
        total = len(self._mods)
        for i, mod in enumerate(self._mods):
            if progress_callback:
                progress_callback(f"Fetching {mod.name}...", (i + 1) / total)
            if self.fetch_release_info(mod):
                success += 1
        self._save_catalog()
        return success

    def generate_share_code(self) -> str:
        """Generate a shareable config code (list of selected mod IDs)."""
        selected = [m.id for m in self._mods if m.selected or m.installed]
        return ",".join(selected)

    def apply_share_code(self, code: str) -> int:
        """Apply a share code - select the mods listed in the code. Returns count matched."""
        ids = set(code.strip().split(","))
        count = 0
        for mod in self._mods:
            if mod.id in ids:
                mod.selected = True
                count += 1
            else:
                mod.selected = False
        return count

    def sort_mods(self, key: str = "name"):
        """Sort the catalog by a given key."""
        if key == "name":
            self._mods.sort(key=lambda m: m.name.lower())
        elif key == "author":
            self._mods.sort(key=lambda m: m.author.lower())
        elif key == "version":
            self._mods.sort(key=lambda m: m.version, reverse=True)
        elif key == "installed":
            self._mods.sort(key=lambda m: (not m.installed, m.name.lower()))
        elif key == "category":
            self._mods.sort(key=lambda m: (m.category, m.name.lower()))
        elif key == "stars":
            self._mods.sort(key=lambda m: m.stars, reverse=True)

    def mark_installed(self, mod_id: str, version: str = ""):
        for mod in self._mods:
            if mod.id == mod_id:
                mod.installed = True
                mod.installed_version = version or mod.version
                break
        self._save_catalog()

    def mark_uninstalled(self, mod_id: str):
        for mod in self._mods:
            if mod.id == mod_id:
                mod.installed = False
                mod.installed_version = ""
                mod.selected = False
                break
        self._save_catalog()

    def detect_installed_from_files(self, among_us_path: str):
        """Scan the game's plugins folder and BepInEx to detect which catalog mods are installed."""
        from pathlib import Path

        game = Path(among_us_path)
        plugins_dir = game / "BepInEx" / "plugins"
        bepinex_core = game / "BepInEx" / "core"

        # Collect all DLL names and folder names in plugins
        found_files: set[str] = set()  # lowercase stems/names
        if plugins_dir.exists():
            for item in plugins_dir.iterdir():
                if item.suffix.lower() == ".dll":
                    found_files.add(item.stem.lower())
                elif item.is_dir() and not item.name.startswith("."):
                    found_files.add(item.name.lower())
                    # Also check DLLs inside subfolders
                    for sub in item.rglob("*.dll"):
                        found_files.add(sub.stem.lower())

        # Build matching patterns for each catalog mod
        # We try: repo name, mod name (normalized), known DLL names
        for mod in self._mods:
            matched = False

            # Special case: BepInEx - check core folder
            if mod.id == "bepinex":
                if bepinex_core.exists() and (
                    (bepinex_core / "BepInEx.Core.dll").exists()
                    or (bepinex_core / "BepInEx.dll").exists()
                ):
                    matched = True
            else:
                # Build list of possible names to match
                candidates: set[str] = set()

                # From mod name: "The Other Roles" → "theotherroles"
                normalized_name = mod.name.lower().replace(" ", "").replace("-", "").replace("_", "")
                candidates.add(normalized_name)

                # From GitHub repo: "TheOtherRolesAU/TheOtherRoles" → "theotherroles"
                if mod.github and "/" in mod.github:
                    repo_name = mod.github.split("/")[1]
                    candidates.add(repo_name.lower())
                    candidates.add(repo_name.lower().replace("-", "").replace("_", ""))

                # From mod id: "theother-roles" → "theotherroles"
                candidates.add(mod.id.lower().replace("-", "").replace("_", ""))

                # From author: sometimes the DLL has the author name
                # (skip this, too many false positives)

                # Check if any found file matches any candidate
                for found in found_files:
                    found_norm = found.replace("-", "").replace("_", "").replace(".", "")
                    for candidate in candidates:
                        if candidate == found_norm or candidate in found_norm or found_norm in candidate:
                            matched = True
                            break
                    if matched:
                        break

            if matched and not mod.installed:
                mod.installed = True
                mod.selected = True
                if not mod.installed_version:
                    mod.installed_version = mod.version or "unknown"
            elif not matched and mod.installed:
                # File is gone - mark as uninstalled
                mod.installed = False
                mod.installed_version = ""

        self._save_catalog()

    def check_updates(self) -> list[CatalogMod]:
        """Check which installed mods have newer versions."""
        updates = []
        for mod in self._mods:
            if mod.installed and mod.version and mod.installed_version:
                if mod.version != mod.installed_version:
                    mod.has_update = True
                    updates.append(mod)
        return updates
