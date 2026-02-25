"""
Core mod management: install, uninstall, enable, disable, and query mods.
Mods are BepInEx plugins stored in Among Us/BepInEx/plugins/.
Disabled mods are moved to Among Us/BepInEx/plugins_disabled/.
"""

import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.config import get_backups_dir


class ModInfo:
    """Represents a single installed mod."""

    def __init__(self, name: str, path: str, enabled: bool = True,
                 version: str = "unknown", author: str = "unknown",
                 description: str = "", source_url: str = "",
                 installed_date: str = ""):
        self.name = name
        self.path = path
        self.enabled = enabled
        self.version = version
        self.author = author
        self.description = description
        self.source_url = source_url
        self.installed_date = installed_date or datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "enabled": self.enabled,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "source_url": self.source_url,
            "installed_date": self.installed_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModInfo":
        return cls(**data)

    @property
    def file_size(self) -> int:
        p = Path(self.path)
        if p.is_file():
            return p.stat().st_size
        elif p.is_dir():
            return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        return 0

    @property
    def size_str(self) -> str:
        size = self.file_size
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class ModManager:
    """Manages mod installation and state."""

    def __init__(self, among_us_path: str):
        self.among_us_path = Path(among_us_path)
        self.bepinex_dir = self.among_us_path / "BepInEx"
        self.plugins_dir = self.bepinex_dir / "plugins"
        self.disabled_dir = self.bepinex_dir / "plugins_disabled"
        self.meta_file = self.bepinex_dir / "mod_metadata.json"
        self._metadata: dict[str, dict] = {}
        self._load_metadata()

    def _load_metadata(self):
        if self.meta_file.exists():
            try:
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._metadata = {}

    def _save_metadata(self):
        self.meta_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump(self._metadata, f, indent=2)
        except OSError:
            pass

    def _set_mod_meta(self, name: str, info: ModInfo):
        self._metadata[name] = info.to_dict()
        self._save_metadata()

    def _get_mod_meta(self, name: str) -> Optional[dict]:
        return self._metadata.get(name)

    def _remove_mod_meta(self, name: str):
        self._metadata.pop(name, None)
        self._save_metadata()

    @property
    def is_bepinex_installed(self) -> bool:
        core = self.bepinex_dir / "core"
        if not core.exists():
            return False
        return (core / "BepInEx.Core.dll").exists() or (core / "BepInEx.dll").exists()

    def get_installed_mods(self) -> list[ModInfo]:
        """Get all installed mods (enabled and disabled)."""
        mods = []
        # Enabled mods
        if self.plugins_dir.exists():
            for item in self.plugins_dir.iterdir():
                if item.name.startswith(".") or item.name == "mod_metadata.json":
                    continue
                if item.suffix.lower() == ".dll" or item.is_dir():
                    meta = self._get_mod_meta(item.name)
                    if meta:
                        mod = ModInfo.from_dict(meta)
                        mod.enabled = True
                        mod.path = str(item)
                    else:
                        mod = ModInfo(
                            name=item.stem if item.is_file() else item.name,
                            path=str(item),
                            enabled=True,
                        )
                    mods.append(mod)

        # Disabled mods
        if self.disabled_dir.exists():
            for item in self.disabled_dir.iterdir():
                if item.name.startswith("."):
                    continue
                if item.suffix.lower() == ".dll" or item.is_dir():
                    meta = self._get_mod_meta(item.name)
                    if meta:
                        mod = ModInfo.from_dict(meta)
                        mod.enabled = False
                        mod.path = str(item)
                    else:
                        mod = ModInfo(
                            name=item.stem if item.is_file() else item.name,
                            path=str(item),
                            enabled=False,
                        )
                    mods.append(mod)

        return mods

    def install_mod(self, source_path: str, mod_name: str = "",
                    version: str = "unknown", author: str = "unknown",
                    description: str = "", source_url: str = "") -> ModInfo:
        """Install a mod from a file or directory."""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        source = Path(source_path)

        if source.suffix.lower() == ".zip":
            return self._install_from_zip(source, mod_name, version, author, description, source_url)

        if source.suffix.lower() == ".dll":
            name = mod_name or source.stem
            dest = self.plugins_dir / source.name
            shutil.copy2(source, dest)
            info = ModInfo(name=name, path=str(dest), version=version,
                           author=author, description=description, source_url=source_url)
            self._set_mod_meta(source.name, info)
            return info

        if source.is_dir():
            name = mod_name or source.name
            dest = self.plugins_dir / source.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source, dest)
            info = ModInfo(name=name, path=str(dest), version=version,
                           author=author, description=description, source_url=source_url)
            self._set_mod_meta(source.name, info)
            return info

        raise ValueError(f"Unsupported mod format: {source.suffix}")

    def _install_from_zip(self, zip_path: Path, mod_name: str,
                          version: str, author: str, description: str,
                          source_url: str) -> ModInfo:
        """
        Install a mod from a zip file.
        Many Among Us mods (like TheOtherRoles) ship as FULL PACKAGES that
        include BepInEx, dotnet, configs, and the mod DLL all together.
        These need to be extracted directly into the game root folder.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(zip_path, "r") as zf:
                filenames = zf.namelist()
                zf.extractall(tmp)

            tmp_path = Path(tmp)

            # Detect if this is a FULL MOD PACKAGE (contains BepInEx + dotnet + doorstop)
            # Mods like TheOtherRoles, TownOfUs, etc. ship this way
            is_full_package = (
                (tmp_path / "BepInEx").exists()
                and (
                    (tmp_path / "dotnet").exists()
                    or (tmp_path / "doorstop_config.ini").exists()
                    or (tmp_path / "winhttp.dll").exists()
                )
            )

            if is_full_package:
                # This is a full mod package — extract EVERYTHING to the game root
                # This overwrites BepInEx core, configs, adds plugins, etc.
                self._copy_tree_merge(tmp_path, self.among_us_path)

                # Find the main mod DLL that was installed in plugins
                name = mod_name or zip_path.stem
                plugins = self.plugins_dir
                main_dll = None
                if plugins.exists():
                    for dll in plugins.iterdir():
                        if dll.suffix.lower() == ".dll":
                            # Skip known framework DLLs
                            if dll.stem.lower() not in (
                                "reactor", "mini.regioninstall",
                                "bepinex.core", "0harmony",
                            ):
                                main_dll = dll
                                break

                path = str(main_dll) if main_dll else str(plugins)
                info = ModInfo(name=name, path=path, version=version,
                               author=author, description=description, source_url=source_url)
                self._set_mod_meta(name, info)
                return info

            # Check if the zip just contains a BepInEx folder (plugins only)
            bepinex_in_zip = tmp_path / "BepInEx"
            if bepinex_in_zip.exists():
                self._copy_tree_merge(bepinex_in_zip, self.bepinex_dir)

                name = mod_name or zip_path.stem
                dlls = list(self.plugins_dir.rglob("*.dll")) if self.plugins_dir.exists() else []
                path = str(dlls[0]) if dlls else str(self.plugins_dir)

                info = ModInfo(name=name, path=path, version=version,
                               author=author, description=description, source_url=source_url)
                self._set_mod_meta(name, info)
                return info

            # Simple zip with just DLL(s)
            dlls = list(tmp_path.rglob("*.dll"))
            if dlls:
                if len(dlls) == 1:
                    dll = dlls[0]
                    name = mod_name or dll.stem
                    dest = self.plugins_dir / dll.name
                    self.plugins_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dll, dest)
                    info = ModInfo(name=name, path=str(dest), version=version,
                                   author=author, description=description, source_url=source_url)
                    self._set_mod_meta(dll.name, info)
                    return info
                else:
                    name = mod_name or zip_path.stem
                    dest = self.plugins_dir / name
                    dest.mkdir(parents=True, exist_ok=True)
                    for dll in dlls:
                        shutil.copy2(dll, dest / dll.name)
                    info = ModInfo(name=name, path=str(dest), version=version,
                                   author=author, description=description, source_url=source_url)
                    self._set_mod_meta(name, info)
                    return info

            raise ValueError("No mod files found in zip archive")

    @staticmethod
    def _copy_tree_merge(src: Path, dst: Path):
        """Recursively copy src into dst, merging directories and overwriting files."""
        for item in src.iterdir():
            target = dst / item.name
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                ModManager._copy_tree_merge(item, target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)

    def uninstall_mod(self, mod: ModInfo):
        """Remove a mod completely."""
        p = Path(mod.path)
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
        self._remove_mod_meta(mod.name)

    def enable_mod(self, mod: ModInfo) -> ModInfo:
        """Enable a disabled mod by moving it to the plugins folder."""
        if mod.enabled:
            return mod

        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        source = Path(mod.path)
        dest = self.plugins_dir / source.name

        if source.exists():
            shutil.move(str(source), str(dest))

        mod.enabled = True
        mod.path = str(dest)
        self._set_mod_meta(source.name, mod)
        return mod

    def disable_mod(self, mod: ModInfo) -> ModInfo:
        """Disable a mod by moving it to the disabled folder."""
        if not mod.enabled:
            return mod

        self.disabled_dir.mkdir(parents=True, exist_ok=True)
        source = Path(mod.path)
        dest = self.disabled_dir / source.name

        if source.exists():
            shutil.move(str(source), str(dest))

        mod.enabled = False
        mod.path = str(dest)
        self._set_mod_meta(source.name, mod)
        return mod

    def backup_mods(self, backup_name: str = "") -> Path:
        """Create a backup of all currently installed mods."""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_dir = get_backups_dir() / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Copy plugins
        if self.plugins_dir.exists():
            dest = backup_dir / "plugins"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(self.plugins_dir, dest)

        # Copy disabled plugins
        if self.disabled_dir.exists():
            dest = backup_dir / "plugins_disabled"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(self.disabled_dir, dest)

        # Copy metadata
        if self.meta_file.exists():
            shutil.copy2(self.meta_file, backup_dir / "mod_metadata.json")

        return backup_dir

    def restore_backup(self, backup_path: str):
        """Restore mods from a backup."""
        backup = Path(backup_path)
        if not backup.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        # Restore plugins
        plugins_backup = backup / "plugins"
        if plugins_backup.exists():
            if self.plugins_dir.exists():
                shutil.rmtree(self.plugins_dir)
            shutil.copytree(plugins_backup, self.plugins_dir)

        # Restore disabled
        disabled_backup = backup / "plugins_disabled"
        if disabled_backup.exists():
            if self.disabled_dir.exists():
                shutil.rmtree(self.disabled_dir)
            shutil.copytree(disabled_backup, self.disabled_dir)

        # Restore metadata
        meta_backup = backup / "mod_metadata.json"
        if meta_backup.exists():
            shutil.copy2(meta_backup, self.meta_file)
            self._load_metadata()

    def get_backups(self) -> list[dict]:
        """List available backups."""
        backups = []
        backup_base = get_backups_dir()
        if backup_base.exists():
            for item in sorted(backup_base.iterdir(), reverse=True):
                if item.is_dir():
                    mod_count = 0
                    plugins = item / "plugins"
                    if plugins.exists():
                        mod_count = len([f for f in plugins.iterdir()
                                         if f.suffix == ".dll" or f.is_dir()])
                    backups.append({
                        "name": item.name,
                        "path": str(item),
                        "date": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                        "mod_count": mod_count,
                    })
        return backups

    def delete_backup(self, backup_path: str):
        """Delete a backup."""
        p = Path(backup_path)
        if p.exists() and p.is_dir():
            shutil.rmtree(p)

    def check_conflicts(self) -> list[str]:
        """Check for potential mod conflicts (duplicate DLLs, known incompatibilities)."""
        conflicts = []
        if not self.plugins_dir.exists():
            return conflicts

        dll_sources: dict[str, list[str]] = {}
        for item in self.plugins_dir.rglob("*.dll"):
            name = item.name.lower()
            if name not in dll_sources:
                dll_sources[name] = []
            dll_sources[name].append(str(item))

        for dll_name, sources in dll_sources.items():
            if len(sources) > 1:
                conflicts.append(
                    f"Duplicate DLL '{dll_name}' found in: {', '.join(sources)}"
                )

        return conflicts
