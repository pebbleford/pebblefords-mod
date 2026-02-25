"""
BepInEx mod loader management for Among Us.
Downloads the pre-configured BepInExPack from Thunderstore (made specifically for Among Us)
and also supports the bleeding edge builds from builds.bepinex.dev.
"""

import io
import json
import os
import shutil
import zipfile
from pathlib import Path
from urllib import request

# Primary: BepInEx bleeding edge IL2CPP x86 build (latest, supports newest metadata versions)
BLEEDING_EDGE_URL = "https://builds.bepinex.dev/projects/bepinex_be/754/BepInEx-Unity.IL2CPP-win-x86-6.0.0-be.754%2Bc038613.zip"

# Backup: Thunderstore BepInExPack preconfigured for Among Us (may lag behind game updates)
THUNDERSTORE_URL = "https://thunderstore.io/package/download/BepInEx/BepInExPack_AmongUs/6.0.700/"


class BepInExManager:
    """Manages BepInEx installation for Among Us."""

    def __init__(self, among_us_path: str):
        self.game_path = Path(among_us_path)
        self.bepinex_dir = self.game_path / "BepInEx"

    @property
    def is_installed(self) -> bool:
        # Check for core DLLs - BepInEx 6 uses BepInEx.Core.dll or BepInEx.dll
        core = self.bepinex_dir / "core"
        if not core.exists():
            return False
        return (
            (core / "BepInEx.Core.dll").exists()
            or (core / "BepInEx.dll").exists()
        )

    @property
    def version(self) -> str:
        if not self.is_installed:
            return "Not installed"
        # Try to read version from changelog or config
        for name in ["CHANGELOG.md", "changelog.txt"]:
            f = self.bepinex_dir / "core" / name
            if f.exists():
                try:
                    line = f.read_text(encoding="utf-8").strip().split("\n")[0]
                    return line.strip("#- ").strip()
                except OSError:
                    pass
        # Check if BepInEx.Core.dll exists (v6)
        if (self.bepinex_dir / "core" / "BepInEx.Core.dll").exists():
            return "6.x (Bleeding Edge)"
        return "Installed"

    def _get_working_url(self) -> str:
        """Find a working download URL."""
        for url in [BLEEDING_EDGE_URL, THUNDERSTORE_URL]:
            try:
                req = request.Request(url, headers={"User-Agent": "AmongUsModManager/1.0"})
                with request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        return url
            except Exception:
                continue
        return THUNDERSTORE_URL  # Last resort

    def download_and_install(self, progress_callback=None) -> bool:
        """Download and install BepInEx for Among Us."""
        try:
            if progress_callback:
                progress_callback("Finding best BepInEx build...", 0.05)

            url = self._get_working_url()

            if progress_callback:
                progress_callback("Downloading BepInEx...", 0.1)

            # Download with progress
            req = request.Request(url, headers={"User-Agent": "AmongUsModManager/1.0"})
            with request.urlopen(req, timeout=180) as resp:
                total_size = int(resp.headers.get("Content-Length", 0))
                data = bytearray()
                downloaded = 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    data.extend(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        pct = 0.1 + 0.5 * (downloaded / total_size)
                        progress_callback(
                            f"Downloading BepInEx... {mb_done:.1f} / {mb_total:.1f} MB",
                            pct,
                        )
                data = bytes(data)

            if progress_callback:
                progress_callback("Extracting BepInEx...", 0.65)

            self._install_from_bytes(data)

            if progress_callback:
                progress_callback("Setting up directories...", 0.80)

            # Ensure required directories exist
            for dirname in ["plugins", "plugins_disabled", "config", "patchers"]:
                (self.bepinex_dir / dirname).mkdir(parents=True, exist_ok=True)

            if progress_callback:
                progress_callback("Fixing Steam authentication...", 0.90)

            # Create steam_appid.txt to fix SteamworksAuthFail error
            # Among Us App ID is 945360
            steam_appid = self.game_path / "steam_appid.txt"
            steam_appid.write_text("945360", encoding="utf-8")

            if progress_callback:
                progress_callback("BepInEx installed successfully!", 1.0)

            return True

        except Exception as e:
            if progress_callback:
                progress_callback(f"Error: {e}", -1)
            return False

    def _install_from_bytes(self, data: bytes):
        """
        Extract BepInEx zip into the game directory.
        Handles both flat zips and nested zips (like Thunderstore packs
        that put everything inside a subfolder).
        """
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()

            # Detect if files are inside a subfolder (e.g. "BepInExPack_AmongUs/")
            # by checking if there's a common prefix that contains BepInEx/ or doorstop
            prefix = ""
            for name in names:
                parts = name.split("/")
                if len(parts) >= 2 and parts[1] in ("BepInEx", "dotnet", "doorstop_config.ini"):
                    prefix = parts[0] + "/"
                    break

            if prefix:
                # Extract with prefix stripped — put contents directly in game dir
                for member in zf.infolist():
                    if not member.filename.startswith(prefix):
                        continue
                    # Strip the prefix
                    rel_path = member.filename[len(prefix):]
                    if not rel_path:
                        continue

                    target = self.game_path / rel_path

                    if member.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(target, "wb") as dst:
                            dst.write(src.read())
            else:
                # Flat zip — extract directly
                zf.extractall(self.game_path)

    def install_from_zip(self, zip_path: str, progress_callback=None) -> bool:
        """Install BepInEx from a local zip file."""
        try:
            if progress_callback:
                progress_callback("Reading zip file...", 0.2)

            data = Path(zip_path).read_bytes()

            if progress_callback:
                progress_callback("Extracting BepInEx...", 0.5)

            self._install_from_bytes(data)

            for dirname in ["plugins", "plugins_disabled", "config", "patchers"]:
                (self.bepinex_dir / dirname).mkdir(parents=True, exist_ok=True)

            if progress_callback:
                progress_callback("BepInEx installed!", 1.0)

            return True

        except Exception as e:
            if progress_callback:
                progress_callback(f"Error: {e}", -1)
            return False

    def uninstall(self) -> bool:
        """Remove BepInEx from the game directory."""
        try:
            if self.bepinex_dir.exists():
                shutil.rmtree(self.bepinex_dir)

            # Remove all BepInEx boot files
            for filename in [
                "winhttp.dll", "doorstop_config.ini", ".doorstop_version",
                "changelog.txt",
            ]:
                f = self.game_path / filename
                if f.exists():
                    f.unlink()

            # Remove dotnet runtime folder if it was installed by BepInEx
            dotnet = self.game_path / "dotnet"
            if dotnet.exists():
                shutil.rmtree(dotnet)

            return True
        except OSError:
            return False

    def get_status(self) -> dict:
        """Get detailed BepInEx status information."""
        status = {
            "installed": self.is_installed,
            "version": self.version,
            "plugins_count": 0,
            "disabled_count": 0,
            "config_count": 0,
            "has_dotnet": (self.game_path / "dotnet").exists(),
            "has_doorstop": (self.game_path / "doorstop_config.ini").exists(),
            "has_winhttp": (self.game_path / "winhttp.dll").exists(),
        }

        plugins = self.bepinex_dir / "plugins"
        if plugins.exists():
            status["plugins_count"] = len([
                f for f in plugins.iterdir()
                if f.suffix == ".dll" or f.is_dir()
            ])

        disabled = self.bepinex_dir / "plugins_disabled"
        if disabled.exists():
            status["disabled_count"] = len([
                f for f in disabled.iterdir()
                if f.suffix == ".dll" or f.is_dir()
            ])

        config = self.bepinex_dir / "config"
        if config.exists():
            status["config_count"] = len(list(config.glob("*.cfg")))

        return status

    def verify_installation(self) -> list[str]:
        """Check that all required BepInEx files are present. Returns list of issues."""
        issues = []

        if not (self.game_path / "doorstop_config.ini").exists():
            issues.append("Missing doorstop_config.ini in game folder")

        if not (self.game_path / "winhttp.dll").exists():
            issues.append("Missing winhttp.dll in game folder (DLL proxy)")

        core = self.bepinex_dir / "core"
        if not core.exists():
            issues.append("Missing BepInEx/core directory")
        elif not (core / "BepInEx.Core.dll").exists() and not (core / "BepInEx.dll").exists():
            issues.append("Missing BepInEx core DLL")

        if not (self.game_path / "dotnet").exists():
            issues.append("Missing dotnet runtime folder (needed for IL2CPP)")

        return issues
