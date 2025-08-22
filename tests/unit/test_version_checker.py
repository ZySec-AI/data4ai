"""Tests for version checker functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from data4ai.version_checker import VersionChecker


class TestVersionChecker:
    """Test version checking functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = VersionChecker()

    def test_get_current_version(self):
        """Test getting current version."""
        version = self.checker.get_current_version()
        assert isinstance(version, str)
        assert version != ""

    def test_load_cache_missing_file(self):
        """Test loading cache when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.checker.cache_file = Path(temp_dir) / "nonexistent.json"
            cache_data = self.checker._load_cache()
            assert cache_data is None

    def test_load_cache_expired(self):
        """Test loading expired cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "cache.json"

            # Create expired cache (timestamp = 0)
            cache_data = {"latest_version": "1.0.0", "timestamp": 0}
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)

            self.checker.cache_file = cache_file
            result = self.checker._load_cache()
            assert result is None

    def test_load_cache_valid(self):
        """Test loading valid cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "cache.json"

            import time

            # Create valid cache (current timestamp)
            cache_data = {"latest_version": "1.0.0", "timestamp": time.time()}
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)

            self.checker.cache_file = cache_file
            result = self.checker._load_cache()
            assert result is not None
            assert result["latest_version"] == "1.0.0"

    def test_save_cache(self):
        """Test saving cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "cache.json"
            self.checker.cache_file = cache_file

            self.checker._save_cache("1.2.3")

            assert cache_file.exists()
            with open(cache_file) as f:
                data = json.load(f)
            assert data["latest_version"] == "1.2.3"
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_get_latest_version_success(self):
        """Test successful version fetch from PyPI."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"info": {"version": "1.2.3"}}

        with (
            patch("httpx.AsyncClient") as mock_client_class,
            tempfile.TemporaryDirectory() as temp_dir,
        ):
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            self.checker.cache_file = Path(temp_dir) / "cache.json"
            version = await self.checker.get_latest_version()

            assert version == "1.2.3"
            mock_client.get.assert_called_once_with(self.checker.pypi_url)

    @pytest.mark.asyncio
    async def test_get_latest_version_failure(self):
        """Test handling of network failure."""
        with (
            patch("httpx.AsyncClient") as mock_client_class,
            tempfile.TemporaryDirectory() as temp_dir,
        ):
            # Ensure no cache interferes
            self.checker.cache_file = Path(temp_dir) / "cache.json"

            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            version = await self.checker.get_latest_version()
            assert version is None

    def test_get_latest_version_sync(self):
        """Test synchronous version check."""
        with patch.object(self.checker, "get_latest_version") as mock_async:
            mock_async.return_value = "1.2.3"

            with patch("asyncio.run", return_value="1.2.3"):
                version = self.checker.get_latest_version_sync()
                assert version == "1.2.3"

    def test_check_for_updates_newer_available(self):
        """Test update check when newer version is available."""
        with (
            patch.object(self.checker, "get_current_version", return_value="1.0.0"),
            patch.object(self.checker, "get_latest_version_sync", return_value="1.2.3"),
        ):
            has_update, current, latest = self.checker.check_for_updates()
            assert has_update is True
            assert current == "1.0.0"
            assert latest == "1.2.3"

    def test_check_for_updates_up_to_date(self):
        """Test update check when up to date."""
        with (
            patch.object(self.checker, "get_current_version", return_value="1.2.3"),
            patch.object(self.checker, "get_latest_version_sync", return_value="1.2.3"),
        ):
            has_update, current, latest = self.checker.check_for_updates()
            assert has_update is False
            assert current == "1.2.3"
            assert latest == "1.2.3"

    def test_check_for_updates_no_network(self):
        """Test update check when network is unavailable."""
        with (
            patch.object(self.checker, "get_current_version", return_value="1.0.0"),
            patch.object(self.checker, "get_latest_version_sync", return_value=None),
        ):
            has_update, current, latest = self.checker.check_for_updates()
            assert has_update is False
            assert current == "1.0.0"
            assert latest is None

    def test_format_update_message(self):
        """Test update message formatting."""
        message = self.checker.format_update_message("1.0.0", "1.2.3")
        assert "1.0.0" in message
        assert "1.2.3" in message
        assert "pip install --upgrade" in message
        assert "data4ai" in message
