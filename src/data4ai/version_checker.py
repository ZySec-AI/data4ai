"""Version checking utilities for Data4AI."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

import httpx
from packaging import version

logger = logging.getLogger(__name__)


class VersionChecker:
    """Check for Data4AI updates and notify users."""

    def __init__(self, package_name: str = "data4ai"):
        self.package_name = package_name
        self.pypi_url = f"https://pypi.org/pypi/{package_name}/json"
        self.cache_file = Path.home() / ".data4ai" / "version_cache.json"
        self.cache_duration = 86400  # 24 hours in seconds

    def get_current_version(self) -> str:
        """Get current installed version."""
        try:
            from data4ai import __version__

            return __version__
        except ImportError:
            # Fallback version for development
            return "0.3.0"

    def _load_cache(self) -> Optional[dict]:
        """Load cached version information."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    cache_data = json.load(f)

                import time

                if time.time() - cache_data.get("timestamp", 0) < self.cache_duration:
                    return cache_data
        except Exception as e:
            logger.debug(f"Failed to load version cache: {e}")
        return None

    def _save_cache(self, latest_version: str) -> None:
        """Save version information to cache."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            import time

            cache_data = {"latest_version": latest_version, "timestamp": time.time()}
            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.debug(f"Failed to save version cache: {e}")

    async def get_latest_version(self) -> Optional[str]:
        """Get latest version from PyPI."""
        # Check cache first
        cache_data = self._load_cache()
        if cache_data:
            return cache_data.get("latest_version")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.pypi_url)
                response.raise_for_status()
                data = response.json()
                latest_version = data["info"]["version"]

                # Save to cache
                self._save_cache(latest_version)
                return latest_version

        except Exception as e:
            logger.debug(f"Failed to check latest version: {e}")
            return None

    def get_latest_version_sync(self) -> Optional[str]:
        """Get latest version synchronously."""
        try:
            return asyncio.run(self.get_latest_version())
        except Exception as e:
            logger.debug(f"Failed to check version sync: {e}")
            return None

    def check_for_updates(self) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Check if updates are available.

        Returns:
            (has_update, current_version, latest_version)
        """
        current_version = self.get_current_version()
        latest_version = self.get_latest_version_sync()

        if not latest_version or current_version == "unknown":
            return False, current_version, latest_version

        try:
            has_update = version.parse(latest_version) > version.parse(current_version)
            return has_update, current_version, latest_version
        except Exception as e:
            logger.debug(f"Failed to compare versions: {e}")
            return False, current_version, latest_version

    def format_update_message(self, current_ver: str, latest_ver: str) -> str:
        """Format update notification message."""
        return f"""
🚀 A newer version of Data4AI is available!

   Current version: {current_ver}
   Latest version:  {latest_ver}

💡 To update, run:
   pip install --upgrade data4ai

📋 Release notes: https://github.com/zysec-ai/data4ai/releases
"""
