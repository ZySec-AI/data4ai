"""Success-path coverage for the public command-line interface."""

from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from data4ai.cli import app

runner = CliRunner()


def test_prompt_dry_run_and_version():
    result = runner.invoke(
        app,
        [
            "prompt",
            "--repo",
            "demo",
            "--description",
            "examples",
            "--count",
            "2",
            "--dataset",
            "alpaca",
            "--dspy-model",
            "test/model",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "Dry run completed" in result.output
    assert runner.invoke(app, ["version"]).exit_code == 0


def test_document_file_and_folder_dry_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    document = tmp_path / "source.md"
    document.write_text("# Source", encoding="utf-8")
    with patch(
        "data4ai.cli.DocumentHandler.detect_document_type", return_value="markdown"
    ):
        result = runner.invoke(
            app,
            ["doc", str(document), "--repo", "demo", "--count", "2", "--dry-run"],
        )
    assert result.exit_code == 0
    assert "Dry run completed" in result.output

    folder = tmp_path / "docs"
    folder.mkdir()
    files = [folder / f"{index}.md" for index in range(12)]
    with patch("data4ai.cli.DocumentHandler.scan_folder", return_value=files):
        result = runner.invoke(
            app,
            [
                "doc",
                str(folder),
                "--repo",
                "demo",
                "--file-types",
                "md,txt",
                "--dry-run",
            ],
        )
    assert result.exit_code == 0
    assert "and 2 more" in result.output


def test_document_generation_with_quality_and_upload(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    document = tmp_path / "source.md"
    document.write_text("# Source", encoding="utf-8")
    generator = Mock()
    generator.generate_from_document_sync.return_value = {
        "row_count": 4,
        "output_path": "outputs/datasets/demo/data.jsonl",
        "chunks_processed": 3,
        "total_documents": 2,
    }
    publisher = Mock()
    publisher.push_dataset.return_value = "https://example.test/dataset"
    with (
        patch(
            "data4ai.cli.DocumentHandler.detect_document_type", return_value="markdown"
        ),
        patch("data4ai.generator.DatasetGenerator", return_value=generator),
        patch("data4ai.cli.HuggingFacePublisher", return_value=publisher),
        patch("data4ai.cli.console.status", return_value=nullcontext()),
        patch("data4ai.cli.settings") as settings,
    ):
        settings.hf_token = "hf-token"
        settings.hf_organization = "org"
        result = runner.invoke(
            app,
            [
                "doc",
                str(document),
                "--repo",
                "demo",
                "--count",
                "4",
                "--taxonomy",
                "advanced",
                "--provenance",
                "--verify",
                "--long-context",
                "--huggingface",
            ],
        )
    assert result.exit_code == 0
    assert "Generated 4 examples" in result.output
    assert "Processed 3 chunks from 2 documents" in result.output
    assert "Published to" in result.output
    generator.generate_from_document_sync.assert_called_once()
    publisher.push_dataset.assert_called_once()


def test_prompt_generation_success():
    generator = Mock()
    generator.generate_from_prompt_sync.return_value = {
        "row_count": 3,
        "output_path": "output/data.jsonl",
        "prompt_generation_method": "static",
        "metrics": {"completion_rate": 1.0},
    }
    with patch("data4ai.cli.DatasetGenerator", return_value=generator):
        result = runner.invoke(
            app,
            ["prompt", "--repo", "demo", "--description", "examples", "--count", "3"],
        )
    assert result.exit_code == 0
    assert "Generated 3 examples" in result.output


def test_push_dataset_success():
    publisher = Mock()
    publisher.push_dataset.return_value = "https://example.test/dataset"
    with patch("data4ai.cli.HuggingFacePublisher", return_value=publisher):
        result = runner.invoke(
            app,
            ["push", "--repo", "demo", "--token", "hf-token", "--description", "Demo"],
        )
    assert result.exit_code == 0
    assert "uploaded successfully" in result.output


def test_file_validate_and_stats_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source.csv"
    source.write_text("instruction,output\na,b\n", encoding="utf-8")
    with patch(
        "data4ai.schemas.SchemaRegistry.get_schema", return_value=object(), create=True
    ):
        result = runner.invoke(
            app,
            ["file-to-dataset", str(source), "--repo", "demo", "--dataset", "alpaca"],
        )
    assert result.exit_code == 0

    dataset = tmp_path / "outputs" / "datasets" / "demo"
    dataset.mkdir(parents=True)
    (dataset / "data.jsonl").write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")
    validation = runner.invoke(app, ["validate", "--repo", "demo"])
    assert validation.exit_code == 0
    assert "2 examples" in validation.output
    statistics = runner.invoke(app, ["stats", "--repo", "demo"])
    assert statistics.exit_code == 0
    assert "Total: 2 examples" in statistics.output


def test_deprecated_excel_command():
    result = runner.invoke(app, ["excel-to-dataset", "source.xlsx", "--repo", "demo"])
    assert result.exit_code == 1
    assert "deprecated" in result.output


def test_session_list_status_cleanup_and_errors():
    session = {
        "name": "Demo",
        "session_id": "1234567890",
        "source_type": "youtube_channel",
        "status": "running",
        "progress": "1/2",
        "last_active": "2026-09-10T00:00:00+00:00",
        "total_processed": 1,
        "total_failed": 0,
        "output_repo": "demo",
    }
    manager = Mock()
    manager.list_sessions.return_value = [session]
    loaded = SimpleNamespace(name="Demo", source_type="youtube_channel")
    manager.load_session.return_value = loaded
    manager.get_session_summary.return_value = {
        "name": "Demo",
        "session_id": "1234567890",
        "source_type": "youtube_channel",
        "status": "running",
        "created_at": "today",
        "last_active": "today",
        "output_repo": "demo",
        "totals": {
            "processed": 1,
            "pending": 1,
            "failed": 0,
            "skipped": 0,
            "total_items": 2,
        },
        "stages": {
            "extract": {"status": "completed", "items_processed": 1, "items_total": 1}
        },
        "source_config": {"channel": "demo"},
    }
    manager.cleanup_old_sessions.return_value = 2
    with patch("data4ai.session_manager.SessionManager", return_value=manager):
        listing = runner.invoke(app, ["session", "list", "--verbose"])
        status = runner.invoke(app, ["session", "status", "1234567890", "--verbose"])
        cleanup = runner.invoke(app, ["session", "cleanup", "--older-than", "24h"])
        invalid = runner.invoke(app, ["session", "invalid"])
    assert listing.exit_code == 0 and "Demo" in listing.output
    assert status.exit_code == 0 and "Processed: 1" in status.output
    assert cleanup.exit_code == 0 and "Cleaned up 2" in cleanup.output
    assert invalid.exit_code == 1


def test_youtube_generation_and_upload(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    handler = Mock()
    handler.extract_from_channel.return_value = ["one.md", "two.md"]
    generator = Mock()
    generator.generate_from_document_sync.return_value = {
        "row_count": 2,
        "output_path": "outputs/datasets/demo/data.jsonl",
    }
    publisher = Mock()
    publisher.push_to_hub.return_value = "https://example.test/dataset"
    with (
        patch("data4ai.cli.check_environment_variables"),
        patch(
            "data4ai.integrations.youtube_handler.YouTubeHandler", return_value=handler
        ),
        patch("data4ai.generator.DatasetGenerator", return_value=generator),
        patch("data4ai.cli.HuggingFacePublisher", return_value=publisher),
    ):
        result = runner.invoke(
            app,
            ["youtube", "@channel", "--repo", "demo", "--count", "2", "--huggingface"],
        )
    assert result.exit_code == 0
    assert "Generated 2 examples" in result.output
    handler.extract_from_channel.assert_called_once()
    generator.generate_from_document_sync.assert_called_once()
    publisher.push_to_hub.assert_called_once()


def test_youtube_search_dry_run_and_invalid_source(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    handler = Mock()
    handler.extract_from_search.return_value = ["one.md"]
    with (
        patch("data4ai.cli.check_environment_variables"),
        patch(
            "data4ai.integrations.youtube_handler.YouTubeHandler", return_value=handler
        ),
    ):
        result = runner.invoke(
            app,
            ["youtube", "tutorials", "--search", "--repo", "demo", "--dry-run"],
        )
        invalid = runner.invoke(app, ["youtube", "invalid", "--repo", "demo"])
    assert result.exit_code == 0
    assert "transcripts extracted only" in result.output
    assert invalid.exit_code == 1


def test_session_resume_youtube(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    manager = Mock()
    session = SimpleNamespace(
        session_id="1234567890", name="Demo", source_type="youtube_channel"
    )
    manager.find_session_by_name.return_value = session
    manager.load_session.return_value = session
    handler = Mock()
    handler.resume_extraction.return_value = (
        ["one.md"],
        {"processed": 1, "skipped": 0, "failed": 0},
    )
    with (
        patch("data4ai.session_manager.SessionManager", return_value=manager),
        patch(
            "data4ai.integrations.youtube_handler.YouTubeHandler", return_value=handler
        ),
    ):
        result = runner.invoke(app, ["session", "resume", "--name", "Demo"])
    assert result.exit_code == 0
    assert "Resume completed" in result.output


def test_youtube_session_channel_and_search(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    manager = Mock()
    manager.find_session_by_name.return_value = None
    manager.create_session.return_value = SimpleNamespace(session_id="session")
    handler = Mock()
    handler.extract_from_channel_with_session.return_value = (
        ["one.md"],
        {"processed": 1, "skipped": 0, "failed": 0},
    )
    handler.extract_from_search_with_session.return_value = (
        ["search.md"],
        {"processed": 1, "skipped": 0, "failed": 0},
    )
    with (
        patch("data4ai.cli.check_environment_variables"),
        patch("data4ai.session_manager.SessionManager", return_value=manager),
        patch(
            "data4ai.integrations.youtube_handler.YouTubeHandler", return_value=handler
        ),
    ):
        channel = runner.invoke(
            app,
            ["youtube-session", "@channel", "--repo", "demo", "--max-videos", "2"],
        )
        search = runner.invoke(
            app,
            ["youtube-session", "tutorial", "--search", "--repo", "search-demo"],
        )
    assert channel.exit_code == 0 and "Session completed" in channel.output
    assert search.exit_code == 0 and "Session completed" in search.output
    handler.extract_from_channel_with_session.assert_called_once()
    handler.extract_from_search_with_session.assert_called_once()
