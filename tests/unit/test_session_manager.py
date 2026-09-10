"""Tests for persistent Data4AI sessions."""

import json
from datetime import datetime, timedelta, timezone

from data4ai.session_manager import (
    ContentItem,
    ProcessingStage,
    SessionData,
    SessionManager,
)


def test_session_models_round_trip():
    stage = ProcessingStage("extract", "pending", items_total=2)
    item = ContentItem(
        "item-1", "source", "hash", 10, "now", "extract", "pending", "now", "now"
    )
    session = SessionData(
        "session-1",
        "Session",
        "document",
        {"path": "input.pdf"},
        "now",
        "now",
        "active",
        stages={"extract": stage},
        content_items={"item-1": item},
    )

    restored = SessionData.from_dict(session.to_dict())
    assert restored == session
    assert ProcessingStage.from_dict(stage.to_dict()) == stage
    assert ContentItem.from_dict(item.to_dict()) == item


def test_session_lifecycle_and_listing(tmp_path):
    manager = SessionManager(tmp_path)
    session = manager.create_session(
        "My session",
        "document",
        {"path": "input.pdf"},
        "dataset",
        {"batch_size": 2},
        session_id="session-1",
    )
    stage = manager.add_processing_stage(session, "extract", total_items=3)
    manager.update_stage_progress(
        session, "extract", items_processed=2, items_failed=1, status="in_progress"
    )
    assert stage.started_at is not None
    manager.update_stage_progress(
        session, "extract", items_processed=1, status="completed"
    )
    assert stage.completed_at is not None

    loaded = manager.load_session("session-1")
    assert loaded is not None
    assert loaded.stages["extract"].items_processed == 3
    assert manager.find_session_by_name("My session") is not None
    assert manager.find_session_by_name("missing") is None

    listed = manager.list_sessions()
    assert listed[0]["progress"] == "1/1"
    assert listed[0]["output_repo"] == "dataset"
    assert (
        manager.get_session_summary(session)["stages"]["extract"][
            "completion_percentage"
        ]
        == 100
    )


def test_missing_and_invalid_sessions(tmp_path):
    manager = SessionManager(tmp_path)
    assert manager.load_session("missing") is None

    invalid = tmp_path / "session_invalid.json"
    invalid.write_text("not-json")
    assert manager.load_session("invalid") is None
    assert manager.list_sessions() == []


def test_content_status_and_skip_logic(tmp_path):
    manager = SessionManager(tmp_path)
    session = manager.create_session(
        "Content", "document", {}, "output", session_id="session-1"
    )
    item = manager.add_content_item(
        session, "item-1", "source", "hash-1", 10, {"type": "text"}
    )
    assert session.total_pending == 1
    assert manager.should_skip_content(session, "missing", "hash") is False
    assert manager.should_skip_content(session, "item-1", "hash-1") is False

    manager.update_content_item_status(session, "item-1", "completed", "publish")
    assert item.processing_stage == "publish"
    assert session.total_pending == 0
    assert session.total_processed == 1
    assert manager.should_skip_content(session, "item-1", "hash-1") is True
    assert manager.should_skip_content(session, "item-1", "changed") is False

    failed = manager.add_content_item(session, "failed", "source", "hash", 1)
    skipped = manager.add_content_item(session, "skipped", "source", "hash", 1)
    manager.update_content_item_status(session, failed.item_id, "failed")
    manager.update_content_item_status(session, skipped.item_id, "skipped")
    manager.update_content_item_status(session, "missing", "completed")
    assert session.total_failed == 1
    assert session.total_skipped == 1


def test_cleanup_session_and_old_sessions(tmp_path):
    manager = SessionManager(tmp_path)
    old = manager.create_session(
        "Old", "prompt", {}, "output", session_id="old-session"
    )
    old.status = "completed"
    old.last_active = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    manager._save_session(old)
    active = manager.create_session(
        "Active", "prompt", {}, "output", session_id="active-session"
    )
    active.last_active = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    manager._save_session(active)

    (manager.checkpoints_dir / "old-session_extract.json").write_text("{}")
    (manager.content_registry_dir / "old-session_content.json").write_text("{}")
    assert manager.cleanup_old_sessions(days=30) == 1
    assert manager.load_session("old-session") is None
    assert manager.load_session("active-session") is not None
    assert manager.cleanup_session("active-session") is True


def test_missing_stage_and_empty_summary(tmp_path):
    manager = SessionManager(tmp_path)
    session = manager.create_session(
        "Empty", "prompt", {}, "output", session_id="session-1"
    )
    manager.update_stage_progress(session, "missing", status="completed")
    summary = manager.get_session_summary(session)
    assert summary["stages"] == {}
    assert summary["totals"]["total_items"] == 0

    bad = tmp_path / "session_bad.json"
    bad.write_text(
        json.dumps(
            {
                "session_id": "bad",
                "last_active": "not-a-date",
                "status": "completed",
            }
        )
    )
    assert manager.cleanup_old_sessions(days=30) == 0
