"""Tests for resumable YouTube extraction orchestration."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from data4ai.integrations.youtube_handler import YouTubeHandler


def bare_handler() -> YouTubeHandler:
    handler = object.__new__(YouTubeHandler)
    handler.api_key = "test-key"
    handler.model = "test/model"
    handler.client = Mock()
    handler.session_manager = Mock()
    handler.content_tracker = Mock()
    handler.content_tracker.create_youtube_content_hash.return_value = "hash"
    return handler


def make_video(video_id: str) -> dict:
    return {
        "id": video_id,
        "title": video_id,
        "url": f"https://youtu.be/{video_id}",
        "duration": "10",
        "upload_date": "20260910",
    }


def test_process_videos_with_session_handles_skip_success_and_failure(tmp_path):
    handler = bare_handler()
    checkpoint = Mock()
    checkpoint.get_stage_resume_info.return_value = {"completed_items": ["completed"]}
    session = SimpleNamespace(
        session_id="session-1", content_items={"existing": object()}
    )
    (tmp_path / "existing.md").write_text("already present", encoding="utf-8")

    def transcript(video_id):
        if video_id == "failed":
            raise RuntimeError("transcript failure")
        return "transcript", {"title": "Updated", "channel": "Channel"}

    handler._get_video_transcript = Mock(side_effect=transcript)
    handler._create_markdown = Mock(return_value="# notes")
    videos = [
        make_video("completed"),
        make_video("existing"),
        make_video("processed"),
        make_video("failed"),
    ]
    with patch("data4ai.integrations.youtube_handler.time.sleep"):
        files, stats = handler._process_videos_with_session(
            videos, tmp_path, session, checkpoint, incremental=True
        )

    assert stats == {"total_videos": 4, "processed": 1, "skipped": 2, "failed": 1}
    assert len(files) == 4
    assert (tmp_path / "processed.md").read_text(encoding="utf-8") == "# notes"
    assert "transcript failure" in (tmp_path / "failed.md").read_text(encoding="utf-8")
    handler.session_manager.add_content_item.assert_called_once()
    handler.session_manager.update_session.assert_called_once_with(session)


def test_session_channel_and_search_entry_points(tmp_path):
    handler = bare_handler()
    session = SimpleNamespace(session_id="session-1")
    checkpoint = Mock()
    checkpoint.load_stage_checkpoint.return_value = None
    videos = [make_video("abcdefghijk")]
    expected = ([tmp_path / "abcdefghijk.md"], {"processed": 1})
    handler._process_videos_with_session = Mock(return_value=expected)

    with patch(
        "data4ai.integrations.youtube_handler.SessionCheckpointManager",
        return_value=checkpoint,
    ):
        handler._get_channel_videos = Mock(return_value=videos)
        assert (
            handler.extract_from_channel_with_session(
                session, "@channel", tmp_path, max_videos=1
            )
            == expected
        )
        handler._search_youtube_videos = Mock(return_value=videos)
        assert (
            handler.extract_from_search_with_session(
                session, "topic", tmp_path, max_results=5
            )
            == expected
        )

    assert checkpoint.create_stage_checkpoint.call_count == 2
    assert checkpoint.add_pending_items.call_count == 2


def test_session_entry_points_return_empty_when_no_videos(tmp_path):
    handler = bare_handler()
    session = SimpleNamespace(session_id="session-1")
    checkpoint = Mock()
    checkpoint.load_stage_checkpoint.return_value = object()
    with patch(
        "data4ai.integrations.youtube_handler.SessionCheckpointManager",
        return_value=checkpoint,
    ):
        handler._get_channel_videos = Mock(return_value=[])
        channel = handler.extract_from_channel_with_session(session, "@empty", tmp_path)
        handler._search_youtube_videos = Mock(return_value=[])
        search = handler.extract_from_search_with_session(session, "empty", tmp_path)
    empty = ([], {"total_videos": 0, "processed": 0, "skipped": 0, "failed": 0})
    assert channel == empty
    assert search == empty


def test_resume_extraction_routes_and_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    handler = bare_handler()
    session = SimpleNamespace(
        session_id="session-1",
        source_type="youtube_channel",
        source_config={"channel_handle": "@channel", "max_videos": 2},
        output_repo="demo",
    )
    handler.session_manager.load_session.return_value = session
    handler.extract_from_channel_with_session = Mock(
        return_value=([], {"processed": 0})
    )
    checkpoint = Mock()
    checkpoint.get_stage_resume_info.return_value = {
        "can_resume": True,
        "pending_count": 2,
    }
    checkpoint.get_session_summary.return_value = {
        "stages": {"extract": {"pending": 1}}
    }
    handler.session_manager.get_session_summary.return_value = {"name": "Demo"}

    with patch(
        "data4ai.integrations.youtube_handler.SessionCheckpointManager",
        return_value=checkpoint,
    ):
        assert handler.resume_extraction("session-1") == ([], {"processed": 0})
        summary = handler.get_session_summary("session-1")
    assert summary["name"] == "Demo"
    assert summary["can_resume"] is True

    session.source_type = "youtube_search"
    session.source_config = {"keywords": "topic", "max_results": 3}
    handler.extract_from_search_with_session = Mock(return_value=([], {"processed": 0}))
    with patch(
        "data4ai.integrations.youtube_handler.SessionCheckpointManager",
        return_value=checkpoint,
    ):
        assert handler.resume_extraction("session-1") == ([], {"processed": 0})


def test_resume_and_summary_missing_states():
    handler = bare_handler()
    handler.session_manager = None
    assert handler.resume_extraction("missing") is None
    assert handler.get_session_summary("missing") is None

    handler.session_manager = Mock()
    handler.session_manager.load_session.return_value = None
    assert handler.resume_extraction("missing") is None
    assert handler.get_session_summary("missing") is None

    session = SimpleNamespace(
        session_id="session-1",
        source_type="unsupported",
        source_config={},
        output_repo="demo",
    )
    handler.session_manager.load_session.return_value = session
    checkpoint = Mock()
    checkpoint.get_stage_resume_info.return_value = {"can_resume": False}
    with patch(
        "data4ai.integrations.youtube_handler.SessionCheckpointManager",
        return_value=checkpoint,
    ):
        assert handler.resume_extraction("session-1")[1]["total_videos"] == 0
        checkpoint.get_stage_resume_info.return_value = {
            "can_resume": True,
            "pending_count": 1,
        }
        assert handler.resume_extraction("session-1") is None
