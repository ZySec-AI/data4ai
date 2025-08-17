"""Checkpoint and resume functionality for Data4AI."""

import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from data4ai.atomic_writer import AtomicWriter

logger = logging.getLogger("data4ai")


@dataclass
class CheckpointData:
    """Data structure for checkpoint information."""

    session_id: str
    created_at: str
    updated_at: str
    input_file: str
    output_dir: str
    schema: str
    model: str
    temperature: float
    batch_size: int
    completed_rows: list[int]
    pending_rows: list[int]
    failed_rows: list[int]
    partial_data: dict[int, dict[str, Any]]
    metrics: dict[str, Any]
    total_tokens: int
    total_cost: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CheckpointData":
        """Create from dictionary."""
        return cls(**data)


class CheckpointManager:
    """Manage checkpoint creation and recovery."""

    DEFAULT_DIR = Path(".data4ai_checkpoint")

    def __init__(
        self, checkpoint_dir: Optional[Path] = None, session_id: Optional[str] = None
    ):
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoints
            session_id: Session ID for checkpoint (generates new if None)
        """
        self.checkpoint_dir = checkpoint_dir or self.DEFAULT_DIR
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.session_id = session_id or str(uuid.uuid4())
        self.checkpoint_file = (
            self.checkpoint_dir / f"checkpoint_{self.session_id}.json"
        )
        self.checkpoint_data: Optional[CheckpointData] = None

        logger.info(f"Checkpoint manager initialized: {self.checkpoint_file}")

    def create_checkpoint(
        self,
        input_file: Path,
        output_dir: Path,
        schema: str,
        model: str,
        temperature: float,
        batch_size: int,
        total_rows: list[int],
    ) -> CheckpointData:
        """Create a new checkpoint.

        Args:
            input_file: Input file path
            output_dir: Output directory
            schema: Dataset schema
            model: Model name
            temperature: Generation temperature
            batch_size: Batch size
            total_rows: List of all row indices to process

        Returns:
            Created checkpoint data
        """
        now = datetime.now(timezone.utc).isoformat()

        self.checkpoint_data = CheckpointData(
            session_id=self.session_id,
            created_at=now,
            updated_at=now,
            input_file=str(input_file),
            output_dir=str(output_dir),
            schema=schema,
            model=model,
            temperature=temperature,
            batch_size=batch_size,
            completed_rows=[],
            pending_rows=total_rows,
            failed_rows=[],
            partial_data={},
            metrics={},
            total_tokens=0,
            total_cost=0.0,
        )

        self._save_checkpoint()
        logger.info(f"Created checkpoint for {len(total_rows)} rows")

        return self.checkpoint_data

    def load_checkpoint(
        self, checkpoint_file: Optional[Path] = None
    ) -> Optional[CheckpointData]:
        """Load existing checkpoint.

        Args:
            checkpoint_file: Specific checkpoint file to load

        Returns:
            Loaded checkpoint data or None if not found
        """
        file_to_load = checkpoint_file or self.checkpoint_file

        if not file_to_load.exists():
            logger.info(f"No checkpoint found at {file_to_load}")
            return None

        try:
            with open(file_to_load) as f:
                data = json.load(f)

            self.checkpoint_data = CheckpointData.from_dict(data)
            logger.info(
                f"Loaded checkpoint: {len(self.checkpoint_data.completed_rows)} completed, "
                f"{len(self.checkpoint_data.pending_rows)} pending"
            )

            return self.checkpoint_data

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    def find_latest_checkpoint(self, input_file: Path) -> Optional[Path]:
        """Find the latest checkpoint for a given input file.

        Args:
            input_file: Input file to find checkpoint for

        Returns:
            Path to latest checkpoint or None
        """
        checkpoints = []

        for checkpoint_file in self.checkpoint_dir.glob("checkpoint_*.json"):
            try:
                with open(checkpoint_file) as f:
                    data = json.load(f)

                if data.get("input_file") == str(input_file):
                    checkpoints.append((checkpoint_file, data.get("updated_at", "")))
            except Exception:
                continue

        if not checkpoints:
            return None

        # Sort by update time and return latest
        checkpoints.sort(key=lambda x: x[1], reverse=True)
        return checkpoints[0][0]

    def update_progress(
        self,
        completed: Optional[list[int]] = None,
        failed: Optional[list[int]] = None,
        partial_data: Optional[dict[int, dict[str, Any]]] = None,
        metrics: Optional[dict[str, Any]] = None,
        tokens: int = 0,
    ) -> None:
        """Update checkpoint progress.

        Args:
            completed: Newly completed row indices
            failed: Newly failed row indices
            partial_data: Partial completion data
            metrics: Updated metrics
            tokens: Tokens used in this update
        """
        if not self.checkpoint_data:
            logger.warning("No checkpoint to update")
            return

        # Update completed rows
        if completed:
            self.checkpoint_data.completed_rows.extend(completed)
            # Remove from pending
            pending_set = set(self.checkpoint_data.pending_rows)
            pending_set -= set(completed)
            self.checkpoint_data.pending_rows = list(pending_set)

        # Update failed rows
        if failed:
            self.checkpoint_data.failed_rows.extend(failed)
            # Remove from pending
            pending_set = set(self.checkpoint_data.pending_rows)
            pending_set -= set(failed)
            self.checkpoint_data.pending_rows = list(pending_set)

        # Update partial data
        if partial_data:
            self.checkpoint_data.partial_data.update(partial_data)

        # Update metrics
        if metrics:
            self.checkpoint_data.metrics.update(metrics)

        # Update token count
        self.checkpoint_data.total_tokens += tokens

        # Update timestamp
        self.checkpoint_data.updated_at = datetime.now(timezone.utc).isoformat()

        self._save_checkpoint()

        logger.debug(
            f"Updated checkpoint: {len(self.checkpoint_data.completed_rows)} completed, "
            f"{len(self.checkpoint_data.pending_rows)} pending, "
            f"{len(self.checkpoint_data.failed_rows)} failed"
        )

    def mark_batch_complete(self, batch_indices: list[int]) -> None:
        """Mark a batch of rows as complete.

        Args:
            batch_indices: Row indices that were completed
        """
        self.update_progress(completed=batch_indices)

    def mark_batch_failed(self, batch_indices: list[int]) -> None:
        """Mark a batch of rows as failed.

        Args:
            batch_indices: Row indices that failed
        """
        self.update_progress(failed=batch_indices)

    def get_resume_info(self) -> dict[str, Any]:
        """Get information for resuming from checkpoint.

        Returns:
            Dictionary with resume information
        """
        if not self.checkpoint_data:
            return {}

        return {
            "session_id": self.checkpoint_data.session_id,
            "completed_count": len(self.checkpoint_data.completed_rows),
            "pending_count": len(self.checkpoint_data.pending_rows),
            "failed_count": len(self.checkpoint_data.failed_rows),
            "total_tokens": self.checkpoint_data.total_tokens,
            "can_resume": len(self.checkpoint_data.pending_rows) > 0,
            "partial_data": self.checkpoint_data.partial_data,
        }

    def cleanup(self, keep_failed: bool = False) -> None:
        """Clean up checkpoint after successful completion.

        Args:
            keep_failed: Whether to keep checkpoint if there were failures
        """
        if not self.checkpoint_data:
            return

        if self.checkpoint_data.failed_rows and keep_failed:
            logger.info(
                f"Keeping checkpoint due to {len(self.checkpoint_data.failed_rows)} failures"
            )
            return

        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            logger.info(f"Removed checkpoint: {self.checkpoint_file}")

    def _save_checkpoint(self) -> None:
        """Save checkpoint to disk."""
        if not self.checkpoint_data:
            return

        AtomicWriter.write_json(self.checkpoint_data.to_dict(), self.checkpoint_file)

    @staticmethod
    def list_checkpoints(checkpoint_dir: Optional[Path] = None) -> list[dict[str, Any]]:
        """List all available checkpoints.

        Args:
            checkpoint_dir: Directory to search for checkpoints

        Returns:
            List of checkpoint summaries
        """
        dir_to_search = checkpoint_dir or CheckpointManager.DEFAULT_DIR

        if not dir_to_search.exists():
            return []

        checkpoints = []

        for checkpoint_file in dir_to_search.glob("checkpoint_*.json"):
            try:
                with open(checkpoint_file) as f:
                    data = json.load(f)

                checkpoints.append(
                    {
                        "file": str(checkpoint_file),
                        "session_id": data.get("session_id"),
                        "input_file": data.get("input_file"),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                        "completed": len(data.get("completed_rows", [])),
                        "pending": len(data.get("pending_rows", [])),
                        "failed": len(data.get("failed_rows", [])),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to read checkpoint {checkpoint_file}: {e}")
                continue

        # Sort by update time
        checkpoints.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        return checkpoints

    @staticmethod
    def clean_old_checkpoints(
        days: int = 7, checkpoint_dir: Optional[Path] = None
    ) -> int:
        """Clean up old checkpoints.

        Args:
            days: Remove checkpoints older than this many days
            checkpoint_dir: Directory to clean

        Returns:
            Number of checkpoints removed
        """
        from datetime import timedelta

        dir_to_clean = checkpoint_dir or CheckpointManager.DEFAULT_DIR

        if not dir_to_clean.exists():
            return 0

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        removed = 0

        for checkpoint_file in dir_to_clean.glob("checkpoint_*.json"):
            try:
                with open(checkpoint_file) as f:
                    data = json.load(f)

                updated = datetime.fromisoformat(data.get("updated_at", ""))

                if updated < cutoff:
                    checkpoint_file.unlink()
                    removed += 1
                    logger.info(f"Removed old checkpoint: {checkpoint_file}")

            except Exception as e:
                logger.warning(f"Failed to process checkpoint {checkpoint_file}: {e}")
                continue

        return removed
