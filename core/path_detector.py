"""
Auto-detect Among Us installation path on Windows.
Supports Steam and Epic Games installations.
"""

import os
import re
import winreg
from pathlib import Path


def detect_steam_path() -> str | None:
    """Find Among Us installed via Steam."""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
        steam_path = Path(winreg.QueryValueEx(key, "InstallPath")[0])
        winreg.CloseKey(key)
    except (OSError, FileNotFoundError):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
            steam_path = Path(winreg.QueryValueEx(key, "InstallPath")[0])
            winreg.CloseKey(key)
        except (OSError, FileNotFoundError):
            return None

    # Check default steamapps
    candidates = [steam_path / "steamapps" / "common" / "Among Us"]

    # Check additional library folders from libraryfolders.vdf
    vdf_path = steam_path / "steamapps" / "libraryfolders.vdf"
    if vdf_path.exists():
        try:
            content = vdf_path.read_text(encoding="utf-8")
            paths = re.findall(r'"path"\s+"([^"]+)"', content)
            for p in paths:
                candidates.append(Path(p) / "steamapps" / "common" / "Among Us")
        except OSError:
            pass

    for candidate in candidates:
        if (candidate / "Among Us.exe").exists():
            return str(candidate)

    return None


def detect_epic_path() -> str | None:
    """Find Among Us installed via Epic Games."""
    programdata = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
    manifests_dir = Path(programdata) / "Epic" / "EpicGamesLauncher" / "Data" / "Manifests"

    if not manifests_dir.exists():
        return None

    try:
        for manifest_file in manifests_dir.glob("*.item"):
            try:
                import json
                content = json.loads(manifest_file.read_text(encoding="utf-8"))
                if "among" in content.get("DisplayName", "").lower():
                    install_loc = content.get("InstallLocation", "")
                    if install_loc and (Path(install_loc) / "Among Us.exe").exists():
                        return install_loc
            except (json.JSONDecodeError, OSError):
                continue
    except OSError:
        pass

    return None


def detect_among_us_path() -> str | None:
    """Try all detection methods and return the first valid path."""
    path = detect_steam_path()
    if path:
        return path

    path = detect_epic_path()
    if path:
        return path

    # Check common manual install locations
    common_paths = [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Among Us",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Among Us",
        Path("C:/Games/Among Us"),
        Path("D:/Games/Among Us"),
        Path("D:/SteamLibrary/steamapps/common/Among Us"),
    ]

    for p in common_paths:
        if (p / "Among Us.exe").exists():
            return str(p)

    return None


def validate_among_us_path(path: str) -> bool:
    """Check if a given path is a valid Among Us installation."""
    if not path:
        return False
    p = Path(path)
    return (p / "Among Us.exe").exists()
