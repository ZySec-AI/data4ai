"""Session management for Data4AI with persistent state and resumable workflows."""

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from data4ai.atomic_writer import AtomicWriter

logger = logging.getLogger("data4ai")


@dataclass
class ProcessingStage:
    """Represents a single processing stage within a session."""

    name: str
    status: str  # pending, in_progress, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    items_processed: int = 0
    items_total: int = 0
    items_failed: int = 0
    checkpoint_file: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProcessingStage":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ContentItem:
    """Represents a single piece of content being tracked."""

    item_id: str
    source_path: str
    content_hash: str
    size: int
    last_modified: str
    processing_stage: str
    status: str  # pending, processing, completed, failed, skipped
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContentItem":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SessionData:
    """Main session data structure."""

    session_id: str
    name: str
    source_type: str  # youtube, document, prompt
    source_config: dict[str, Any]
    created_at: str
    last_active: str
    status: str  # active, paused, completed, failed

    # Processing stages
    stages: dict[str, ProcessingStage] = field(default_factory=dict)

    # Content tracking
    content_items: dict[str, ContentItem] = field(default_factory=dict)

    # Metrics
    total_processed: int = 0
    total_pending: int = 0
    total_failed: int = 0
    total_skipped: int = 0

    # Configuration
    output_repo: str = ""
    processing_config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            "stages": {k: v.to_dict() for k, v in self.stages.items()},
            "content_items": {k: v.to_dict() for k, v in self.content_items.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionData":
        """Create from dictionary."""
        stages = {
            k: ProcessingStage.from_dict(v) for k, v in data.pop("stages", {}).items()
        }
        content_items = {
            k: ContentItem.from_dict(v)
            for k, v in data.pop("content_items", {}).items()
        }

        session = cls(**data)
        session.stages = stages
        session.content_items = content_items
        return session


class SessionManager:
    """Manages persistent sessions with resumable workflows."""

    DEFAULT_DIR = Path(".data4ai_sessions")

    def __init__(self, session_dir: Optional[Path] = None):
        """Initialize session manager.

        Args:
            session_dir: Directory to store session files
        """
        self.session_dir = session_dir or self.DEFAULT_DIR
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoints_dir = self.session_dir / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

        self.content_registry_dir = self.session_dir / "content_registry"
        self.content_registry_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Session manager initialized: {self.session_dir}")

    def create_session(
        self,
        name: str,
        source_type: str,
        source_config: dict[str, Any],
        output_repo: str,
        processing_config: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> SessionData:
        """Create a new session.

        Args:
            name: Human-readable session name
            source_type: Type of source (youtube, document, prompt)
            source_config: Configuration for the source
            output_repo: Output repository name
            processing_config: Processing configuration
            session_id: Optional custom session ID

        Returns:
            Created session data
        """
        session_id = session_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        session_data = SessionData(
            session_id=session_id,
            name=name,
            source_type=source_type,
            source_config=source_config,
            created_at=now,
            last_active=now,
            status="active",
            output_repo=output_repo,
            processing_config=processing_config or {},
        )

        self._save_session(session_data)
        logger.info(f"Created session '{name}' ({session_id})")

        return session_data

    def load_session(self, session_id: str) -> Optional[SessionData]:
        """Load existing session.

        Args:
            session_id: Session ID to load

        Returns:
            Loaded session data or None if not found
        """
        session_file = self.session_dir / f"session_{session_id}.json"

        if not session_file.exists():
            logger.warning(f"Session not found: {session_id}")
            return None

        try:
            with open(session_file) as f:
                data = json.load(f)

            session_data = SessionData.from_dict(data)
            logger.info(f"Loaded session '{session_data.name}' ({session_id})")

            return session_data

        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def find_session_by_name(self, name: str) -> Optional[SessionData]:
        """Find session by name.

        Args:
            name: Session name to search for

        Returns:
            Session data or None if not found
        """
        for session_file in self.session_dir.glob("session_*.json"):
            try:
                with open(session_file) as f:
                    data = json.load(f)

                if data.get("name") == name:
                    return SessionData.from_dict(data)

            except Exception:
                continue

        return None

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions with summary information.

        Returns:
            List of session summaries
        """
        sessions = []

        for session_file in self.session_dir.glob("session_*.json"):
            try:
                with open(session_file) as f:
                    data = json.load(f)

                # Calculate progress
                stages = data.get("stages", {})
                total_stages = len(stages)
                completed_stages = sum(
                    1 for stage in stages.values() if stage.get("status") == "completed"
                )

                sessions.append(
                    {
                        "session_id": data.get("session_id"),
                        "name": data.get("name"),
                        "source_type": data.get("source_type"),
                        "status": data.get("status"),
                        "created_at": data.get("created_at"),
                        "last_active": data.get("last_active"),
                        "output_repo": data.get("output_repo"),
                        "total_processed": data.get("total_processed", 0),
                        "total_pending": data.get("total_pending", 0),
                        "total_failed": data.get("total_failed", 0),
                        "progress": (
                            f"{completed_stages}/{total_stages}"
                            if total_stages > 0
                            else "0/0"
                        ),
                        "file": str(session_file),
                    }
                )

            except Exception as e:
                logger.warning(f"Failed to read session {session_file}: {e}")
                continue

        # Sort by last_active descending
        sessions.sort(key=lambda x: x.get("last_active", ""), reverse=True)

        return sessions

    def update_session(self, session_data: SessionData) -> None:
        """Update session data.

        Args:
            session_data: Session data to update
        """
        session_data.last_active = datetime.now(timezone.utc).isoformat()
        self._save_session(session_data)

    def add_processing_stage(
        self, session_data: SessionData, stage_name: str, total_items: int = 0
    ) -> ProcessingStage:
        """Add a processing stage to the session.

        Args:
            session_data: Session to add stage to
            stage_name: Name of the processing stage
            total_items: Total number of items to process in this stage

        Returns:
            Created processing stage
        """
        stage = ProcessingStage(
            name=stage_name, status="pending", items_total=total_items
        )

        session_data.stages[stage_name] = stage
        self.update_session(session_data)

        logger.info(f"Added stage '{stage_name}' to session '{session_data.name}'")

        return stage

    def update_stage_progress(
        self,
        session_data: SessionData,
        stage_name: str,
        items_processed: int = 0,
        items_failed: int = 0,
        status: Optional[str] = None,
    ) -> None:
        """Update progress for a processing stage.

        Args:
            session_data: Session containing the stage
            stage_name: Name of the stage to update
            items_processed: Number of items processed (incremental)
            items_failed: Number of items failed (incremental)
            status: New status for the stage
        """
        if stage_name not in session_data.stages:
            logger.warning(f"Stage '{stage_name}' not found in session")
            return

        stage = session_data.stages[stage_name]

        if items_processed > 0:
            stage.items_processed += items_processed

        if items_failed > 0:
            stage.items_failed += items_failed

        if status:
            stage.status = status

            if status == "in_progress" and not stage.started_at:
                stage.started_at = datetime.now(timezone.utc).isoformat()
            elif status in ["completed", "failed"]:
                stage.completed_at = datetime.now(timezone.utc).isoformat()

        self.update_session(session_data)

        logger.debug(
            f"Updated stage '{stage_name}': {stage.items_processed}/{stage.items_total} processed"
        )

    def add_content_item(
        self,
        session_data: SessionData,
        item_id: str,
        source_path: str,
        content_hash: str,
        size: int,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ContentItem:
        """Add a content item to track.

        Args:
            session_data: Session to add item to
            item_id: Unique identifier for the item
            source_path: Path to the source content
            content_hash: Hash of the content for change detection
            size: Size of the content in bytes
            metadata: Additional metadata

        Returns:
            Created content item
        """
        now = datetime.now(timezone.utc).isoformat()

        item = ContentItem(
            item_id=item_id,
            source_path=source_path,
            content_hash=content_hash,
            size=size,
            last_modified=now,
            processing_stage="pending",
            status="pending",
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

        session_data.content_items[item_id] = item
        session_data.total_pending += 1

        self.update_session(session_data)

        return item

    def update_content_item_status(
        self,
        session_data: SessionData,
        item_id: str,
        status: str,
        processing_stage: Optional[str] = None,
    ) -> None:
        """Update status of a content item.

        Args:
            session_data: Session containing the item
            item_id: ID of the item to update
            status: New status
            processing_stage: New processing stage
        """
        if item_id not in session_data.content_items:
            logger.warning(f"Content item '{item_id}' not found in session")
            return

        item = session_data.content_items[item_id]
        old_status = item.status

        item.status = status
        item.updated_at = datetime.now(timezone.utc).isoformat()

        if processing_stage:
            item.processing_stage = processing_stage

        # Update session totals
        if old_status == "pending" and status != "pending":
            session_data.total_pending -= 1

        if status == "completed":
            session_data.total_processed += 1
        elif status == "failed":
            session_data.total_failed += 1
        elif status == "skipped":
            session_data.total_skipped += 1

        self.update_session(session_data)

    def should_skip_content(
        self, session_data: SessionData, item_id: str, current_hash: str
    ) -> bool:
        """Check if content should be skipped based on change detection.

        Args:
            session_data: Session containing the item
            item_id: ID of the item to check
            current_hash: Current hash of the content

        Returns:
            True if content should be skipped
        """
        if item_id not in session_data.content_items:
            return False

        item = session_data.content_items[item_id]

        # Skip if already completed and hash hasn't changed
        return item.status == "completed" and item.content_hash == current_hash

    def get_session_summary(self, session_data: SessionData) -> dict[str, Any]:
        """Get comprehensive session summary.

        Args:
            session_data: Session to summarize

        Returns:
            Session summary
        """
        stages_summary = {}
        for stage_name, stage in session_data.stages.items():
            stages_summary[stage_name] = {
                "status": stage.status,
                "progress": f"{stage.items_processed}/{stage.items_total}",
                "failed": stage.items_failed,
                "completion_percentage": (
                    (stage.items_processed / stage.items_total * 100)
                    if stage.items_total > 0
                    else 0
                ),
            }

        return {
            "session_id": session_data.session_id,
            "name": session_data.name,
            "source_type": session_data.source_type,
            "status": session_data.status,
            "created_at": session_data.created_at,
            "last_active": session_data.last_active,
            "output_repo": session_data.output_repo,
            "stages": stages_summary,
            "totals": {
                "processed": session_data.total_processed,
                "pending": session_data.total_pending,
                "failed": session_data.total_failed,
                "skipped": session_data.total_skipped,
                "total_items": len(session_data.content_items),
            },
        }

    def cleanup_session(self, session_id: str) -> bool:
        """Clean up a session and its associated files.

        Args:
            session_id: Session ID to clean up

        Returns:
            True if cleanup was successful
        """
        try:
            # Remove session file
            session_file = self.session_dir / f"session_{session_id}.json"
            if session_file.exists():
                session_file.unlink()

            # Remove checkpoints
            for checkpoint_file in self.checkpoints_dir.glob(f"{session_id}_*.json"):
                checkpoint_file.unlink()

            # Remove content registry
            content_file = self.content_registry_dir / f"{session_id}_content.json"
            if content_file.exists():
                content_file.unlink()

            logger.info(f"Cleaned up session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {e}")
            return False

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Clean up old completed sessions.

        Args:
            days: Remove sessions older than this many days

        Returns:
            Number of sessions cleaned up
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cleaned = 0

        for session_file in self.session_dir.glob("session_*.json"):
            try:
                with open(session_file) as f:
                    data = json.load(f)

                last_active = datetime.fromisoformat(data.get("last_active", ""))
                status = data.get("status", "")

                if last_active < cutoff and status in ["completed", "failed"]:
                    session_id = data.get("session_id")
                    if self.cleanup_session(session_id):
                        cleaned += 1

            except Exception as e:
                logger.warning(f"Failed to process session {session_file}: {e}")
                continue

        return cleaned

    def _save_session(self, session_data: SessionData) -> None:
        """Save session data to disk.

        Args:
            session_data: Session data to save
        """
        session_file = self.session_dir / f"session_{session_data.session_id}.json"
        AtomicWriter.write_json(session_data.to_dict(), session_file)
