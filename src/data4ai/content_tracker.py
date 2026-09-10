"""Content change detection and tracking for Data4AI sessions."""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("data4ai")


class ContentTracker:
    """Handles content change detection and tracking for resumable workflows."""

    def __init__(self):
        """Initialize content tracker."""
        pass

    @staticmethod
    def calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate MD5 hash of a file.

        Args:
            file_path: Path to the file
            chunk_size: Size of chunks to read at a time

        Returns:
            MD5 hash of the file
        """
        hash_md5 = hashlib.md5()

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
        except Exception as e:
            logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return ""

        return hash_md5.hexdigest()

    @staticmethod
    def calculate_content_hash(content: str) -> str:
        """Calculate MD5 hash of string content.

        Args:
            content: String content to hash

        Returns:
            MD5 hash of the content
        """
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    @staticmethod
    def get_file_info(file_path: Path) -> dict[str, Any]:
        """Get comprehensive file information for tracking.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file information
        """
        try:
            stat = file_path.stat()

            return {
                "path": str(file_path),
                "size": stat.st_size,
                "modified_time": datetime.fromtimestamp(
                    stat.st_mtime, timezone.utc
                ).isoformat(),
                "hash": ContentTracker.calculate_file_hash(file_path),
                "exists": True,
            }
        except Exception as e:
            logger.warning(f"Failed to get file info for {file_path}: {e}")
            return {
                "path": str(file_path),
                "size": 0,
                "modified_time": "",
                "hash": "",
                "exists": False,
            }

    @staticmethod
    def has_file_changed(file_path: Path, cached_info: dict[str, Any]) -> bool:
        """Check if a file has changed since last tracking.

        Args:
            file_path: Path to the file
            cached_info: Previously cached file information

        Returns:
            True if file has changed
        """
        if not file_path.exists():
            return cached_info.get("exists", False)  # Changed if it used to exist

        current_info = ContentTracker.get_file_info(file_path)

        # Quick check: size or modification time
        if current_info["size"] != cached_info.get("size", 0) or current_info[
            "modified_time"
        ] != cached_info.get("modified_time", ""):
            return True

        # Deep check: content hash (only if quick checks pass)
        return current_info["hash"] != cached_info.get("hash", "")

    @staticmethod
    def scan_directory(
        directory: Path,
        patterns: Optional[list[str]] = None,
        recursive: bool = True,
        exclude_patterns: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Scan directory for files and return their information.

        Args:
            directory: Directory to scan
            patterns: File patterns to include (e.g., ["*.pdf", "*.txt"])
            recursive: Whether to scan recursively
            exclude_patterns: Patterns to exclude

        Returns:
            List of file information dictionaries
        """
        if not directory.exists() or not directory.is_dir():
            logger.warning(f"Directory not found or not a directory: {directory}")
            return []

        files_info = []
        patterns = patterns or ["*"]
        exclude_patterns = exclude_patterns or []

        def should_exclude(file_path: Path) -> bool:
            """Check if file should be excluded."""
            return any(file_path.match(pattern) for pattern in exclude_patterns)

        def scan_path(path: Path, depth: int = 0) -> None:
            """Recursively scan path."""
            try:
                for item in path.iterdir():
                    if item.is_file():
                        # Check if file matches any include pattern
                        if any(
                            item.match(pattern) for pattern in patterns
                        ) and not should_exclude(item):
                            files_info.append(ContentTracker.get_file_info(item))

                    elif item.is_dir() and recursive and not should_exclude(item):
                        scan_path(item, depth + 1)

            except PermissionError:
                logger.warning(f"Permission denied accessing: {path}")
            except Exception as e:
                logger.warning(f"Error scanning {path}: {e}")

        scan_path(directory)

        return files_info

    @staticmethod
    def create_youtube_content_id(video_info: dict[str, Any]) -> str:
        """Create a unique content ID for YouTube videos.

        Args:
            video_info: Video information dictionary

        Returns:
            Unique content ID
        """
        video_id = video_info.get("id", "")
        channel = video_info.get("channel", "")
        title = video_info.get("title", "")

        # Create a composite ID that includes video ID and basic metadata
        content_str = f"{video_id}:{channel}:{title}"
        return hashlib.md5(content_str.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def create_youtube_content_hash(
        video_info: dict[str, Any], transcript: Optional[str] = None
    ) -> str:
        """Create a content hash for YouTube videos to detect changes.

        Args:
            video_info: Video information dictionary
            transcript: Video transcript content

        Returns:
            Content hash
        """
        # Include key metadata that might change
        hash_content = {
            "id": video_info.get("id", ""),
            "title": video_info.get("title", ""),
            "duration": video_info.get("duration", ""),
            "upload_date": video_info.get("upload_date", ""),
            "channel": video_info.get("channel", ""),
            "transcript_length": len(transcript) if transcript else 0,
            "transcript_hash": (
                ContentTracker.calculate_content_hash(transcript) if transcript else ""
            ),
        }

        content_str = json.dumps(hash_content, sort_keys=True)
        return hashlib.md5(content_str.encode("utf-8")).hexdigest()

    @staticmethod
    def detect_content_changes(
        current_items: list[dict[str, Any]],
        cached_items: dict[str, dict[str, Any]],
        content_type: str = "file",
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Detect changes in content items.

        Args:
            current_items: Current content items
            cached_items: Previously cached content items
            content_type: Type of content (file, youtube, etc.)

        Returns:
            Tuple of (new_items, changed_items, unchanged_items)
        """
        new_items = []
        changed_items = []
        unchanged_items = []

        for item in current_items:
            if content_type == "file":
                item_id = item["path"]
                hash_key = "hash"
            elif content_type == "youtube":
                item_id = ContentTracker.create_youtube_content_id(item)
                hash_key = "content_hash"
            else:
                # Generic fallback
                item_id = item.get("id", str(item))
                hash_key = "hash"

            if item_id not in cached_items:
                new_items.append(item)
            else:
                cached_item = cached_items[item_id]
                current_hash = item.get(hash_key, "")
                cached_hash = cached_item.get(hash_key, "")

                if current_hash != cached_hash:
                    changed_items.append(item)
                else:
                    unchanged_items.append(item)

        return new_items, changed_items, unchanged_items

    @staticmethod
    def create_content_registry_entry(
        item_id: str,
        source_path: str,
        content_hash: str,
        size: int,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Create a standardized content registry entry.

        Args:
            item_id: Unique identifier for the content
            source_path: Path or identifier of the source
            content_hash: Hash of the content
            size: Size of the content
            metadata: Additional metadata

        Returns:
            Content registry entry
        """
        now = datetime.now(timezone.utc).isoformat()

        return {
            "item_id": item_id,
            "source_path": source_path,
            "content_hash": content_hash,
            "size": size,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {},
        }

    @staticmethod
    def find_moved_files(
        current_files: list[dict[str, Any]], cached_files: dict[str, dict[str, Any]]
    ) -> list[tuple[str, str, dict[str, Any]]]:
        """Find files that may have been moved or renamed.

        Args:
            current_files: Current file information
            cached_files: Previously cached file information

        Returns:
            List of (old_path, new_path, file_info) tuples for moved files
        """
        moved_files = []

        # Create hash to path mappings
        current_hash_to_path = {
            item["hash"]: item["path"] for item in current_files if item["hash"]
        }
        cached_hash_to_path = {
            item["hash"]: item["path"]
            for item in cached_files.values()
            if item.get("hash")
        }

        # Find files with same hash but different paths
        for file_hash, cached_path in cached_hash_to_path.items():
            if file_hash in current_hash_to_path:
                current_path = current_hash_to_path[file_hash]
                if current_path != cached_path:
                    # Found a moved file
                    file_info = next(
                        item for item in current_files if item["path"] == current_path
                    )
                    moved_files.append((cached_path, current_path, file_info))

        return moved_files

    @staticmethod
    def get_folder_structure_fingerprint(directory: Path) -> str:
        """Create a fingerprint of folder structure to detect organizational changes.

        Args:
            directory: Directory to fingerprint

        Returns:
            Fingerprint string representing folder structure
        """
        if not directory.exists():
            return ""

        try:
            structure = []

            for root, _dirs, files in os.walk(directory):
                root_path = Path(root)
                relative_root = root_path.relative_to(directory)

                # Add directory structure
                structure.append(f"DIR:{relative_root}")

                # Add files (just names, not content)
                for file in sorted(files):
                    structure.append(f"FILE:{relative_root / file}")

            structure_str = "\n".join(sorted(structure))
            return hashlib.md5(structure_str.encode("utf-8")).hexdigest()

        except Exception as e:
            logger.warning(f"Failed to create folder fingerprint for {directory}: {e}")
            return ""

    @staticmethod
    def should_rescan_folder(
        directory: Path, cached_fingerprint: str, force_rescan: bool = False
    ) -> bool:
        """Determine if a folder should be rescanned for changes.

        Args:
            directory: Directory to check
            cached_fingerprint: Previously cached folder fingerprint
            force_rescan: Force rescan regardless of fingerprint

        Returns:
            True if folder should be rescanned
        """
        if force_rescan:
            return True

        if not cached_fingerprint:
            return True  # No previous scan

        current_fingerprint = ContentTracker.get_folder_structure_fingerprint(directory)
        return current_fingerprint != cached_fingerprint
