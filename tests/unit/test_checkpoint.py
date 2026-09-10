"""Tests for checkpoint persistence and recovery."""

import json
from datetime import datetime, timedelta, timezone

from data4ai.checkpoint import (
    CheckpointData,
    CheckpointManager,
    SessionCheckpointManager,
    StageCheckpointData,
)


def test_checkpoint_data_round_trip():
    data = CheckpointData(
        session_id="session-1",
        created_at="now",
        updated_at="later",
        input_file="input.csv",
        output_dir="out",
        schema="alpaca",
        model="model",
        temperature=0.7,
        batch_size=10,
        completed_rows=[1],
        pending_rows=[2],
        failed_rows=[3],
        partial_data={1: {"output": "ok"}},
        metrics={"rows": 1},
        total_tokens=10,
        total_cost=0.1,
    )

    assert CheckpointData.from_dict(data.to_dict()) == data


def test_checkpoint_manager_lifecycle(tmp_path):
    manager = CheckpointManager(tmp_path, session_id="session-1")
    checkpoint = manager.create_checkpoint(
        input_file=tmp_path / "input.csv",
        output_dir=tmp_path / "output",
        schema="alpaca",
        model="model",
        temperature=0.7,
        batch_size=2,
        total_rows=[1, 2, 3],
    )

    assert manager.checkpoint_file.exists()
    assert checkpoint.pending_rows == [1, 2, 3]

    manager.update_progress(
        completed=[1],
        failed=[2],
        partial_data={1: {"answer": "done"}},
        metrics={"batches": 1},
        tokens=42,
    )
    assert checkpoint.completed_rows == [1]
    assert checkpoint.failed_rows == [2]
    assert checkpoint.pending_rows == [3]
    assert checkpoint.total_tokens == 42
    assert manager.get_resume_info()["can_resume"] is True

    loaded = CheckpointManager(tmp_path, session_id="session-1").load_checkpoint()
    assert loaded is not None
    assert loaded.partial_data == {"1": {"answer": "done"}}

    latest = manager.find_latest_checkpoint(tmp_path / "input.csv")
    assert latest == manager.checkpoint_file
    listed = CheckpointManager.list_checkpoints(tmp_path)
    assert listed[0]["completed"] == 1
    assert listed[0]["failed"] == 1

    manager.cleanup(keep_failed=True)
    assert manager.checkpoint_file.exists()
    manager.cleanup()
    assert not manager.checkpoint_file.exists()


def test_checkpoint_manager_handles_missing_and_invalid_files(tmp_path):
    manager = CheckpointManager(tmp_path, session_id="session-1")
    assert manager.load_checkpoint() is None
    assert manager.find_latest_checkpoint(tmp_path / "input.csv") is None
    assert CheckpointManager.list_checkpoints(tmp_path / "missing") == []

    manager.checkpoint_file.write_text("not json")
    assert manager.load_checkpoint() is None

    bad_file = tmp_path / "checkpoint_bad.json"
    bad_file.write_text("not json")
    assert CheckpointManager.list_checkpoints(tmp_path) == []


def test_clean_old_checkpoints(tmp_path):
    old = tmp_path / "checkpoint_old.json"
    recent = tmp_path / "checkpoint_recent.json"
    old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    recent_time = datetime.now(timezone.utc).isoformat()
    old.write_text(json.dumps({"updated_at": old_time}))
    recent.write_text(json.dumps({"updated_at": recent_time}))

    assert CheckpointManager.clean_old_checkpoints(days=7, checkpoint_dir=tmp_path) == 1
    assert not old.exists()
    assert recent.exists()


def test_stage_checkpoint_data_round_trip():
    data = StageCheckpointData(
        stage_name="extract",
        session_id="session-1",
        checkpoint_id="checkpoint-1",
        created_at="now",
        updated_at="later",
        stage_config={"batch": 2},
        input_source="in",
        output_target="out",
        total_items=2,
        completed_items=["one"],
        pending_items=["two"],
        failed_items=[],
        skipped_items=[],
        stage_data={},
        error_log=[],
        processing_times={},
        api_usage={},
    )

    assert StageCheckpointData.from_dict(data.to_dict()) == data


def test_session_checkpoint_manager_lifecycle(tmp_path):
    manager = SessionCheckpointManager("session-1", tmp_path)
    checkpoint = manager.create_stage_checkpoint(
        "extract", {"batch": 2}, "input", "output", total_items=0
    )
    manager.add_pending_items("extract", ["one", "two", "three"])
    manager.update_stage_progress(
        "extract",
        completed_items=["one"],
        failed_items=["two"],
        skipped_items=["three"],
        stage_data={"cursor": 3},
        processing_time=1.5,
        api_usage={"tokens": 12},
        error_info={"message": "failed item"},
    )

    resume = manager.get_stage_resume_info("extract")
    assert resume is not None
    assert resume["completed_count"] == 1
    assert resume["failed_count"] == 1
    assert resume["skipped_count"] == 1
    assert manager.is_stage_complete("extract") is True
    assert checkpoint.error_log[0]["message"] == "failed item"

    summary = manager.get_session_summary()
    assert summary["completed_stages"] == 1
    assert summary["stages"]["extract"]["api_usage"] == {"tokens": 12}

    loaded = SessionCheckpointManager("session-1", tmp_path).load_stage_checkpoint(
        "extract"
    )
    assert loaded is not None
    assert loaded.completed_items == ["one"]

    assert manager.cleanup_stage("extract") is True
    assert manager.cleanup_all_stages() == 0
    assert manager.get_stage_resume_info("missing") is None
    assert manager.is_stage_complete("missing") is False
