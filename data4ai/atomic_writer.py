"""Atomic file writing operations for data safety."""

import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger("data4ai")


class AtomicWriter:
    """Provides atomic write operations to prevent data corruption."""

    @staticmethod
    def write_jsonl(
        data: list[dict[str, Any]],
        file_path: Path,
        append: bool = False,
        compress: bool = False,
    ) -> int:
        """Write JSONL file atomically.

        Args:
            data: List of dictionaries to write
            file_path: Target file path
            append: If True, append to existing file
            compress: If True, gzip the output

        Returns:
            Number of records written
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if append and file_path.exists():
            # For append, we need to be more careful
            return AtomicWriter._append_jsonl(data, file_path, compress)

        # For new file, use atomic write
        temp_fd, temp_path = tempfile.mkstemp(
            suffix=".tmp", prefix=f".{file_path.name}.", dir=file_path.parent
        )

        try:
            count = 0

            if compress:
                import gzip

                with gzip.open(temp_path, "wt", encoding="utf-8") as f:
                    for entry in data:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        count += 1
            else:
                with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                    for entry in data:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        count += 1
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data is written to disk

            # Atomic rename (on same filesystem)
            shutil.move(temp_path, str(file_path))
            logger.debug(f"Atomically wrote {count} records to {file_path}")

            return count

        except Exception as e:
            # Clean up temp file on error
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            logger.error(f"Failed to write {file_path}: {e}")
            raise

    @staticmethod
    def _append_jsonl(
        data: list[dict[str, Any]], file_path: Path, compress: bool = False
    ) -> int:
        """Append to JSONL file with safety measures."""
        # Create backup for safety
        backup_path = file_path.with_suffix(file_path.suffix + ".backup")

        try:
            if file_path.exists():
                shutil.copy2(file_path, backup_path)

            count = 0
            mode = "at" if not compress else "ab"

            if compress:
                import gzip

                with gzip.open(file_path, mode) as f:
                    for entry in data:
                        line = json.dumps(entry, ensure_ascii=False) + "\n"
                        f.write(line.encode("utf-8"))
                        count += 1
            else:
                with open(file_path, mode, encoding="utf-8") as f:
                    for entry in data:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        count += 1
                    f.flush()
                    os.fsync(f.fileno())

            # Remove backup on success
            if backup_path.exists():
                backup_path.unlink()

            return count

        except Exception as e:
            # Restore from backup on error
            if backup_path.exists():
                shutil.move(str(backup_path), str(file_path))
            logger.error(f"Failed to append to {file_path}, restored backup: {e}")
            raise

    @staticmethod
    def write_json(data: dict[str, Any], file_path: Path, indent: int = 2) -> None:
        """Write JSON file atomically."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(
            suffix=".tmp", prefix=f".{file_path.name}.", dir=file_path.parent
        )

        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            shutil.move(temp_path, str(file_path))
            logger.debug(f"Atomically wrote JSON to {file_path}")

        except Exception as e:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            logger.error(f"Failed to write {file_path}: {e}")
            raise

    @staticmethod
    def write_text(content: str, file_path: Path) -> None:
        """Write text file atomically."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(
            suffix=".tmp", prefix=f".{file_path.name}.", dir=file_path.parent
        )

        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            shutil.move(temp_path, str(file_path))
            logger.debug(f"Atomically wrote text to {file_path}")

        except Exception as e:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            logger.error(f"Failed to write {file_path}: {e}")
            raise


class ShardedWriter:
    """Write large datasets in shards to avoid memory issues."""

    def __init__(
        self, output_dir: Path, shard_size: int = 10000, compress: bool = False
    ):
        """Initialize sharded writer.

        Args:
            output_dir: Directory for output files
            shard_size: Maximum records per shard
            compress: Whether to gzip output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.shard_size = shard_size
        self.compress = compress
        self.current_shard = 0
        self.current_count = 0
        self.buffer: list[dict[str, Any]] = []

    def write(self, record: dict[str, Any]) -> None:
        """Write a single record, handling sharding."""
        self.buffer.append(record)

        if len(self.buffer) >= self.shard_size:
            self.flush()

    def flush(self) -> None:
        """Flush current buffer to disk."""
        if not self.buffer:
            return

        # Determine filename
        extension = ".jsonl" if not self.compress else ".jsonl.gz"
        shard_file = self.output_dir / f"data-{self.current_shard:05d}{extension}"

        # Write atomically
        count = AtomicWriter.write_jsonl(
            self.buffer, shard_file, compress=self.compress
        )

        logger.info(f"Wrote shard {self.current_shard} with {count} records")

        self.current_count += count
        self.current_shard += 1
        self.buffer = []

    def finalize(self) -> dict[str, Any]:
        """Flush remaining data and return statistics."""
        self.flush()

        return {
            "total_records": self.current_count,
            "shards": self.current_shard,
            "shard_size": self.shard_size,
            "compressed": self.compress,
        }
