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


@dataclass
class StageCheckpointData:
    """Enhanced checkpoint data for specific processing stages."""

    stage_name: str
    session_id: str
    checkpoint_id: str
    created_at: str
    updated_at: str

    # Stage-specific configuration
    stage_config: dict[str, Any]
    input_source: str
    output_target: str

    # Processing progress
    total_items: int
    completed_items: list[str]  # Item IDs instead of row indices
    pending_items: list[str]
    failed_items: list[str]
    skipped_items: list[str]

    # Stage-specific data
    stage_data: dict[str, Any]
    error_log: list[dict[str, Any]]

    # Performance metrics
    processing_times: dict[str, float]
    api_usage: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StageCheckpointData":
        """Create from dictionary."""
        return cls(**data)


class SessionCheckpointManager:
    """Enhanced checkpoint manager for session-based multi-stage workflows."""

    def __init__(self, session_id: str, checkpoint_dir: Optional[Path] = None):
        """Initialize session checkpoint manager.

        Args:
            session_id: Session ID for this checkpoint manager
            checkpoint_dir: Directory to store checkpoints
        """
        self.session_id = session_id
        self.checkpoint_dir = (
            checkpoint_dir or CheckpointManager.DEFAULT_DIR / "sessions"
        )
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.stage_checkpoints: dict[str, StageCheckpointData] = {}

        logger.info(f"Session checkpoint manager initialized for session: {session_id}")

    def create_stage_checkpoint(
        self,
        stage_name: str,
        stage_config: dict[str, Any],
        input_source: str,
        output_target: str,
        total_items: int,
        stage_data: Optional[dict[str, Any]] = None,
    ) -> StageCheckpointData:
        """Create a checkpoint for a specific processing stage.

        Args:
            stage_name: Name of the processing stage
            stage_config: Configuration for this stage
            input_source: Source of input for this stage
            output_target: Target output for this stage
            total_items: Total number of items to process
            stage_data: Stage-specific data

        Returns:
            Created stage checkpoint data
        """
        checkpoint_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        checkpoint_data = StageCheckpointData(
            stage_name=stage_name,
            session_id=self.session_id,
            checkpoint_id=checkpoint_id,
            created_at=now,
            updated_at=now,
            stage_config=stage_config,
            input_source=input_source,
            output_target=output_target,
            total_items=total_items,
            completed_items=[],
            pending_items=[],
            failed_items=[],
            skipped_items=[],
            stage_data=stage_data or {},
            error_log=[],
            processing_times={},
            api_usage={},
        )

        self.stage_checkpoints[stage_name] = checkpoint_data
        self._save_stage_checkpoint(checkpoint_data)

        logger.info(
            f"Created stage checkpoint '{stage_name}' for session {self.session_id}"
        )

        return checkpoint_data

    def load_stage_checkpoint(self, stage_name: str) -> Optional[StageCheckpointData]:
        """Load checkpoint for a specific stage.

        Args:
            stage_name: Name of the stage to load

        Returns:
            Loaded checkpoint data or None if not found
        """
        checkpoint_file = self._get_stage_checkpoint_file(stage_name)

        if not checkpoint_file.exists():
            logger.debug(f"No checkpoint found for stage '{stage_name}'")
            return None

        try:
            with open(checkpoint_file) as f:
                data = json.load(f)

            checkpoint_data = StageCheckpointData.from_dict(data)
            self.stage_checkpoints[stage_name] = checkpoint_data

            logger.info(
                f"Loaded stage checkpoint '{stage_name}': "
                f"{len(checkpoint_data.completed_items)} completed, "
                f"{len(checkpoint_data.pending_items)} pending"
            )

            return checkpoint_data

        except Exception as e:
            logger.error(f"Failed to load stage checkpoint '{stage_name}': {e}")
            return None

    def update_stage_progress(
        self,
        stage_name: str,
        completed_items: Optional[list[str]] = None,
        failed_items: Optional[list[str]] = None,
        skipped_items: Optional[list[str]] = None,
        stage_data: Optional[dict[str, Any]] = None,
        processing_time: Optional[float] = None,
        api_usage: Optional[dict[str, int]] = None,
        error_info: Optional[dict[str, Any]] = None,
    ) -> None:
        """Update progress for a stage checkpoint.

        Args:
            stage_name: Name of the stage to update
            completed_items: List of completed item IDs
            failed_items: List of failed item IDs
            skipped_items: List of skipped item IDs
            stage_data: Updated stage-specific data
            processing_time: Time spent processing (seconds)
            api_usage: API usage statistics
            error_info: Error information to log
        """
        if stage_name not in self.stage_checkpoints:
            logger.warning(f"Stage checkpoint '{stage_name}' not found")
            return

        checkpoint = self.stage_checkpoints[stage_name]

        # Update item lists
        if completed_items:
            checkpoint.completed_items.extend(completed_items)
            # Remove from pending
            pending_set = set(checkpoint.pending_items)
            pending_set -= set(completed_items)
            checkpoint.pending_items = list(pending_set)

        if failed_items:
            checkpoint.failed_items.extend(failed_items)
            # Remove from pending
            pending_set = set(checkpoint.pending_items)
            pending_set -= set(failed_items)
            checkpoint.pending_items = list(pending_set)

        if skipped_items:
            checkpoint.skipped_items.extend(skipped_items)
            # Remove from pending
            pending_set = set(checkpoint.pending_items)
            pending_set -= set(skipped_items)
            checkpoint.pending_items = list(pending_set)

        # Update stage data
        if stage_data:
            checkpoint.stage_data.update(stage_data)

        # Update performance metrics
        if processing_time:
            total_time = checkpoint.processing_times.get("total", 0.0)
            checkpoint.processing_times["total"] = total_time + processing_time
            checkpoint.processing_times["last_update"] = processing_time

        if api_usage:
            for key, value in api_usage.items():
                current = checkpoint.api_usage.get(key, 0)
                checkpoint.api_usage[key] = current + value

        # Log errors
        if error_info:
            checkpoint.error_log.append(
                {"timestamp": datetime.now(timezone.utc).isoformat(), **error_info}
            )

        # Update timestamp
        checkpoint.updated_at = datetime.now(timezone.utc).isoformat()

        self._save_stage_checkpoint(checkpoint)

        logger.debug(
            f"Updated stage '{stage_name}': "
            f"{len(checkpoint.completed_items)} completed, "
            f"{len(checkpoint.pending_items)} pending, "
            f"{len(checkpoint.failed_items)} failed, "
            f"{len(checkpoint.skipped_items)} skipped"
        )

    def add_pending_items(self, stage_name: str, item_ids: list[str]) -> None:
        """Add items to the pending list for a stage.

        Args:
            stage_name: Name of the stage
            item_ids: List of item IDs to add as pending
        """
        if stage_name not in self.stage_checkpoints:
            logger.warning(f"Stage checkpoint '{stage_name}' not found")
            return

        checkpoint = self.stage_checkpoints[stage_name]
        checkpoint.pending_items.extend(item_ids)
        checkpoint.total_items = (
            len(checkpoint.pending_items)
            + len(checkpoint.completed_items)
            + len(checkpoint.failed_items)
            + len(checkpoint.skipped_items)
        )

        self._save_stage_checkpoint(checkpoint)

    def get_stage_resume_info(self, stage_name: str) -> Optional[dict[str, Any]]:
        """Get resume information for a specific stage.

        Args:
            stage_name: Name of the stage

        Returns:
            Resume information or None if stage not found
        """
        if stage_name not in self.stage_checkpoints:
            return None

        checkpoint = self.stage_checkpoints[stage_name]

        return {
            "stage_name": stage_name,
            "session_id": self.session_id,
            "checkpoint_id": checkpoint.checkpoint_id,
            "total_items": checkpoint.total_items,
            "completed_count": len(checkpoint.completed_items),
            "pending_count": len(checkpoint.pending_items),
            "failed_count": len(checkpoint.failed_items),
            "skipped_count": len(checkpoint.skipped_items),
            "can_resume": len(checkpoint.pending_items) > 0,
            "pending_items": checkpoint.pending_items.copy(),
            "stage_data": checkpoint.stage_data.copy(),
            "processing_times": checkpoint.processing_times.copy(),
            "api_usage": checkpoint.api_usage.copy(),
            "last_updated": checkpoint.updated_at,
        }

    def is_stage_complete(self, stage_name: str) -> bool:
        """Check if a stage is complete.

        Args:
            stage_name: Name of the stage

        Returns:
            True if stage is complete
        """
        if stage_name not in self.stage_checkpoints:
            return False

        checkpoint = self.stage_checkpoints[stage_name]
        return len(checkpoint.pending_items) == 0

    def get_session_summary(self) -> dict[str, Any]:
        """Get summary of all stages in this session.

        Returns:
            Session summary with stage information
        """
        stages_info = {}

        for stage_name, checkpoint in self.stage_checkpoints.items():
            stages_info[stage_name] = {
                "total_items": checkpoint.total_items,
                "completed": len(checkpoint.completed_items),
                "pending": len(checkpoint.pending_items),
                "failed": len(checkpoint.failed_items),
                "skipped": len(checkpoint.skipped_items),
                "progress_percentage": (
                    len(checkpoint.completed_items)
                    / max(checkpoint.total_items, 1)
                    * 100
                ),
                "is_complete": len(checkpoint.pending_items) == 0,
                "last_updated": checkpoint.updated_at,
                "processing_time": checkpoint.processing_times.get("total", 0.0),
                "api_usage": checkpoint.api_usage.copy(),
            }

        return {
            "session_id": self.session_id,
            "stages": stages_info,
            "total_stages": len(self.stage_checkpoints),
            "completed_stages": sum(
                1 for info in stages_info.values() if info["is_complete"]
            ),
        }

    def cleanup_stage(self, stage_name: str) -> bool:
        """Clean up checkpoint for a specific stage.

        Args:
            stage_name: Name of the stage to clean up

        Returns:
            True if cleanup was successful
        """
        try:
            checkpoint_file = self._get_stage_checkpoint_file(stage_name)
            if checkpoint_file.exists():
                checkpoint_file.unlink()

            if stage_name in self.stage_checkpoints:
                del self.stage_checkpoints[stage_name]

            logger.info(f"Cleaned up stage checkpoint: {stage_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup stage checkpoint {stage_name}: {e}")
            return False

    def cleanup_all_stages(self) -> int:
        """Clean up all stage checkpoints for this session.

        Returns:
            Number of stages cleaned up
        """
        cleaned = 0

        for stage_name in list(self.stage_checkpoints.keys()):
            if self.cleanup_stage(stage_name):
                cleaned += 1

        return cleaned

    def _get_stage_checkpoint_file(self, stage_name: str) -> Path:
        """Get checkpoint file path for a stage.

        Args:
            stage_name: Name of the stage

        Returns:
            Path to checkpoint file
        """
        return self.checkpoint_dir / f"{self.session_id}_{stage_name}.json"

    def _save_stage_checkpoint(self, checkpoint: StageCheckpointData) -> None:
        """Save stage checkpoint to disk.

        Args:
            checkpoint: Checkpoint data to save
        """
        checkpoint_file = self._get_stage_checkpoint_file(checkpoint.stage_name)
        AtomicWriter.write_json(checkpoint.to_dict(), checkpoint_file)
