"""
Online mod browsing and downloading.
Fetches mod listings from GitHub repositories and provides search/download functionality.
"""

import json
import tempfile
from pathlib import Path
from urllib import request, parse
from typing import Optional

from core.config import get_mods_cache_dir


# Well-known Among Us mod repositories on GitHub
KNOWN_REPOS = [
    {"owner": "Eisbison", "repo": "TheOtherRoles", "description": "The Other Roles - Adds many new roles"},
    {"owner": "SubmergedAmongUs", "repo": "Submerged", "description": "Submerged - New map mod"},
    {"owner": "Alexejhero", "repo": "Submerged", "description": "Submerged map mod (alt)"},
    {"owner": "NuclearPowered", "repo": "Reactor", "description": "Reactor - Modding API framework"},
    {"owner": "polusgg", "repo": "mod-bepinex-client", "description": "Polus.gg client mod"},
    {"owner": "Loonie-Toons", "repo": "TOHE", "description": "Town of Host Enhanced"},
    {"owner": "EnhancedNetwork", "repo": "TownofHost-Enhanced", "description": "Town of Host Enhanced"},
    {"owner": "0xDrMoe", "repo": "TownofHost-Enhanced", "description": "Town of Host Enhanced"},
    {"owner": "scp222thj", "repo": "MalumMenu", "description": "MalumMenu - Utility mod"},
    {"owner": "Kara-Zor-El", "repo": "FreeplayToolbox", "description": "Freeplay Toolbox"},
]


class OnlineMod:
    """Represents a mod available for download."""

    def __init__(self, name: str, author: str, description: str,
                 version: str, download_url: str, repo_url: str,
                 download_count: int = 0, file_size: int = 0,
                 updated: str = "", stars: int = 0):
        self.name = name
        self.author = author
        self.description = description
        self.version = version
        self.download_url = download_url
        self.repo_url = repo_url
        self.download_count = download_count
        self.file_size = file_size
        self.updated = updated
        self.stars = stars

    @property
    def size_str(self) -> str:
        size = self.file_size
        if size == 0:
            return "Unknown"
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "author": self.author,
            "description": self.description,
            "version": self.version,
            "download_url": self.download_url,
            "repo_url": self.repo_url,
            "download_count": self.download_count,
            "file_size": self.file_size,
            "updated": self.updated,
            "stars": self.stars,
        }


class ModBrowser:
    """Browse and download mods from GitHub."""

    def __init__(self):
        self.cache_dir = get_mods_cache_dir()
        self._cache: dict[str, list[OnlineMod]] = {}

    def _github_api(self, endpoint: str) -> dict | list:
        """Make a GitHub API request."""
        url = f"https://api.github.com{endpoint}"
        req = request.Request(url, headers={
            "User-Agent": "AmongUsModManager/1.0",
            "Accept": "application/vnd.github.v3+json",
        })
        with request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())

    def get_repo_releases(self, owner: str, repo: str) -> list[OnlineMod]:
        """Get releases from a GitHub repository."""
        cache_key = f"{owner}/{repo}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        mods = []
        try:
            releases = self._github_api(f"/repos/{owner}/{repo}/releases")
            repo_info = self._github_api(f"/repos/{owner}/{repo}")

            for release in releases[:5]:  # Latest 5 releases
                for asset in release.get("assets", []):
                    if asset["name"].lower().endswith((".zip", ".dll")):
                        mod = OnlineMod(
                            name=repo_info.get("name", repo),
                            author=owner,
                            description=repo_info.get("description", "") or release.get("body", "")[:200],
                            version=release.get("tag_name", "unknown"),
                            download_url=asset["browser_download_url"],
                            repo_url=f"https://github.com/{owner}/{repo}",
                            download_count=asset.get("download_count", 0),
                            file_size=asset.get("size", 0),
                            updated=release.get("published_at", "")[:10],
                            stars=repo_info.get("stargazers_count", 0),
                        )
                        mods.append(mod)
                        break  # One asset per release

        except Exception:
            pass

        self._cache[cache_key] = mods
        return mods

    def get_known_mods(self, progress_callback=None) -> list[OnlineMod]:
        """Get mods from all known repositories."""
        all_mods = []
        total = len(KNOWN_REPOS)

        for i, repo_info in enumerate(KNOWN_REPOS):
            if progress_callback:
                progress_callback(
                    f"Fetching {repo_info['owner']}/{repo_info['repo']}...",
                    (i + 1) / total
                )
            mods = self.get_repo_releases(repo_info["owner"], repo_info["repo"])
            if mods:
                all_mods.extend(mods[:1])  # Just the latest release from each

        return all_mods

    def search_github(self, query: str) -> list[OnlineMod]:
        """Search GitHub for Among Us mods."""
        mods = []
        try:
            encoded = parse.quote(f"{query} among us mod")
            data = self._github_api(
                f"/search/repositories?q={encoded}&sort=stars&per_page=15"
            )

            for item in data.get("items", []):
                owner = item["owner"]["login"]
                repo = item["name"]
                releases = self.get_repo_releases(owner, repo)
                if releases:
                    mods.extend(releases[:1])
                else:
                    # No releases - still show the repo
                    mod = OnlineMod(
                        name=item["name"],
                        author=owner,
                        description=item.get("description", "") or "No description",
                        version="No release",
                        download_url="",
                        repo_url=item["html_url"],
                        stars=item.get("stargazers_count", 0),
                        updated=item.get("updated_at", "")[:10],
                    )
                    mods.append(mod)

        except Exception:
            pass

        return mods

    def download_mod(self, mod: OnlineMod, progress_callback=None) -> str:
        """Download a mod and return the local file path."""
        if not mod.download_url:
            raise ValueError("No download URL available for this mod")

        filename = mod.download_url.split("/")[-1]
        dest = self.cache_dir / filename

        if progress_callback:
            progress_callback(f"Downloading {mod.name}...", 0.1)

        req = request.Request(mod.download_url, headers={
            "User-Agent": "AmongUsModManager/1.0",
        })
        with request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            data = bytearray()
            downloaded = 0
            block_size = 8192

            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                data.extend(chunk)
                downloaded += len(chunk)
                if progress_callback and total > 0:
                    progress_callback(
                        f"Downloading {mod.name}... {downloaded // 1024}KB",
                        0.1 + 0.8 * (downloaded / total)
                    )

        dest.write_bytes(bytes(data))

        if progress_callback:
            progress_callback("Download complete!", 1.0)

        return str(dest)

    def check_for_updates(self, installed_mods: list) -> list[dict]:
        """Check if any installed mods have newer versions available."""
        updates = []
        for mod in installed_mods:
            if not hasattr(mod, "source_url") or not mod.source_url:
                continue
            # Extract owner/repo from GitHub URL
            try:
                parts = mod.source_url.rstrip("/").split("/")
                if "github.com" in mod.source_url and len(parts) >= 5:
                    owner = parts[-2]
                    repo = parts[-1]
                    releases = self.get_repo_releases(owner, repo)
                    if releases and releases[0].version != mod.version:
                        updates.append({
                            "mod": mod,
                            "current_version": mod.version,
                            "latest_version": releases[0].version,
                            "download_url": releases[0].download_url,
                            "online_mod": releases[0],
                        })
            except (IndexError, AttributeError):
                continue

        return updates

    def clear_cache(self):
        """Clear the download cache."""
        self._cache.clear()
        if self.cache_dir.exists():
            for f in self.cache_dir.iterdir():
                if f.is_file():
                    f.unlink()
