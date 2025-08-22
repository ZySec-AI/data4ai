"""Integration tests for YouTube functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from data4ai.cli import app
from data4ai.integrations.youtube_handler import YouTubeHandler


@pytest.fixture
def cli_runner():
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_youtube_data():
    """Mock YouTube video data for integration testing."""
    return [
        {
            "url": "https://www.youtube.com/watch?v=test1",
            "title": "Python Tutorial Part 1",
            "id": "test1",
            "duration": "600",
            "upload_date": "20240101",
            "channel": "Python Channel",
        },
        {
            "url": "https://www.youtube.com/watch?v=test2",
            "title": "Python Tutorial Part 2",
            "id": "test2",
            "duration": "800",
            "upload_date": "20240102",
            "channel": "Python Channel",
        },
    ]


@pytest.fixture
def mock_transcript():
    """Mock video transcript content."""
    return """
    In this tutorial, we'll learn about Python functions.
    Functions are reusable blocks of code that perform specific tasks.
    You can define a function using the def keyword.
    Functions can accept parameters and return values.
    This is fundamental to writing clean, maintainable code.
    """


class TestYouTubeIntegration:
    """Integration tests for YouTube functionality."""

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    @patch("data4ai.integrations.youtube_handler.YouTubeHandler")
    @patch("data4ai.generator.DatasetGenerator")
    def test_youtube_channel_command_success(
        self, mock_generator, mock_handler_class, cli_runner, mock_youtube_data
    ):
        """Test successful YouTube channel processing via CLI."""
        # Mock YouTube handler
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler
        mock_handler.extract_from_channel.return_value = [
            Path("/tmp/test1.md"),
            Path("/tmp/test2.md"),
        ]

        # Mock generator
        mock_gen_instance = MagicMock()
        mock_generator.return_value = mock_gen_instance
        mock_gen_instance.generate_from_document_sync.return_value = {
            "row_count": 50,
            "output_path": "/tmp/test-repo/data.jsonl",
        }

        result = cli_runner.invoke(
            app,
            [
                "youtube",
                "@testchannel",
                "--repo",
                "test-repo",
                "--count",
                "50",
                "--max-videos",
                "2",
            ],
        )

        assert result.exit_code == 0
        assert "Processing YouTube channel @testchannel" in result.stdout
        assert "Created 2 transcript files" in result.stdout
        assert "Generated 50 examples" in result.stdout

        # Verify handler was called correctly
        mock_handler.extract_from_channel.assert_called_once_with(
            "@testchannel", Path("outputs/youtube/test-repo"), 2
        )

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    @patch("data4ai.integrations.youtube_handler.YouTubeHandler")
    @patch("data4ai.generator.DatasetGenerator")
    def test_youtube_search_command_success(
        self, mock_generator_class, mock_handler_class, cli_runner
    ):
        """Test successful YouTube search processing via CLI."""
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler
        mock_handler.extract_from_search.return_value = [Path("/tmp/search1.md")]

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_from_document_sync.return_value = {
            "row_count": 25,
            "output_path": "/tmp/search-repo/data.jsonl",
        }

        result = cli_runner.invoke(
            app,
            [
                "youtube",
                "python tutorial",
                "--search",
                "--repo",
                "search-repo",
                "--count",
                "25",
            ],
        )

        if result.exit_code != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
        assert result.exit_code == 0
        assert "search results for 'python tutorial'" in result.stdout

        mock_handler.extract_from_search.assert_called_once_with(
            "python tutorial", Path("outputs/youtube/search-repo"), 50
        )

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    @patch("data4ai.integrations.youtube_handler.YouTubeHandler")
    @patch("data4ai.generator.DatasetGenerator")
    def test_youtube_url_command_success(
        self, mock_generator_class, mock_handler_class, cli_runner
    ):
        """Test successful YouTube URL processing via CLI."""
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler
        mock_handler.extract_from_url.return_value = [Path("/tmp/video.md")]

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_from_document_sync.return_value = {
            "row_count": 10,
            "output_path": "/tmp/video-repo/data.jsonl",
        }

        result = cli_runner.invoke(
            app,
            [
                "youtube",
                "https://www.youtube.com/watch?v=test123",
                "--repo",
                "video-repo",
                "--count",
                "10",
            ],
        )

        assert result.exit_code == 0
        assert "video https://www.youtube.com/watch?v=test123" in result.stdout

    @patch.dict("os.environ", {})
    def test_youtube_command_no_api_key(self, cli_runner):
        """Test YouTube command without API key."""
        result = cli_runner.invoke(
            app, ["youtube", "@testchannel", "--repo", "test-repo"]
        )

        assert result.exit_code == 1
        assert "OPENROUTER_API_KEY environment variable required" in result.stdout

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    def test_youtube_command_invalid_source(self, cli_runner):
        """Test YouTube command with invalid source."""
        result = cli_runner.invoke(
            app, ["youtube", "invalid-source", "--repo", "test-repo"]
        )

        assert result.exit_code == 1
        assert "Invalid YouTube source" in result.stdout

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    @patch("data4ai.integrations.youtube_handler.YouTubeHandler")
    def test_youtube_dry_run_success(self, mock_handler_class, cli_runner):
        """Test YouTube dry run functionality."""
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler
        mock_handler.extract_from_channel.return_value = [Path("/tmp/test.md")]

        result = cli_runner.invoke(
            app, ["youtube", "@testchannel", "--repo", "test-repo", "--dry-run"]
        )

        assert result.exit_code == 0
        assert "Dry run complete - transcripts extracted only" in result.stdout
        # Should not attempt dataset generation in dry run mode

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    @patch("data4ai.integrations.youtube_handler.YouTubeHandler")
    def test_youtube_no_videos_found(self, mock_handler_class, cli_runner):
        """Test YouTube command when no videos are found."""
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler
        mock_handler.extract_from_channel.return_value = []

        result = cli_runner.invoke(
            app, ["youtube", "@emptychannel", "--repo", "test-repo"]
        )

        assert result.exit_code == 1
        assert "No videos processed successfully" in result.stdout

    def test_youtube_handler_end_to_end_mock(self, mock_youtube_data, mock_transcript):
        """Test end-to-end YouTube handler functionality with mocks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Create handler
            handler = YouTubeHandler("test-key", "test-model")

            # Mock the client's complete method
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = (
                "## Processed Knowledge\n\nThis is processed content."
            )

            with (
                patch.object(
                    handler.client, "chat_completion", return_value=mock_response
                ),
                patch.object(handler, "_get_video_transcript") as mock_transcript_fn,
                patch.object(
                    handler, "_get_channel_videos", return_value=mock_youtube_data
                ),
                patch.object(
                    handler,
                    "_create_knowledge_notes",
                    return_value="## Processed Knowledge\n\nThis is processed content.",
                ),
            ):
                # Mock transcript extraction
                mock_transcript_fn.side_effect = [
                    (
                        mock_transcript,
                        {"title": "Updated Title 1", "channel": "Test Channel"},
                    ),
                    (
                        mock_transcript,
                        {"title": "Updated Title 2", "channel": "Test Channel"},
                    ),
                ]

                # Process videos
                created_files = handler.extract_from_channel(
                    "@testchannel", output_dir, max_videos=2
                )

                # Verify results
                assert len(created_files) == 2
                assert all(f.exists() for f in created_files)
                assert all(f.suffix == ".md" for f in created_files)

                # Verify markdown content
                for file_path in created_files:
                    content = file_path.read_text()
                    assert "# " in content  # Has title
                    assert "**Video ID:**" in content  # Has metadata
                    assert "**URL:**" in content
                    assert "**Channel:**" in content

    def test_folder_structure_creation(self):
        """Test that YouTube handler creates proper folder structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            # Create handler
            handler = YouTubeHandler("test-key", "test-model")

            # Test different folder structures
            test_cases = [
                ("outputs/youtube/channel-repo", "channel processing"),
                ("outputs/youtube/search-repo", "search processing"),
                ("outputs/youtube/video-repo", "single video processing"),
            ]

            for folder_path, description in test_cases:
                full_path = base_dir / folder_path

                # Mock a simple video processing
                with patch.object(
                    handler, "_get_video_transcript", return_value=(None, {})
                ):
                    video_data = [
                        {
                            "url": "https://www.youtube.com/watch?v=test",
                            "title": f"Test Video for {description}",
                            "id": "test123",
                            "duration": "600",
                            "upload_date": "20240101",
                            "channel": "Test Channel",
                        }
                    ]

                    created_files = handler._process_videos(video_data, full_path)

                    # Verify folder structure
                    assert full_path.exists()
                    assert full_path.is_dir()
                    assert len(created_files) == 1
                    assert created_files[0].parent == full_path

    @patch("subprocess.run")
    @patch.object(YouTubeHandler, "_process_videos")
    def test_youtube_handler_with_real_yt_dlp_interface(
        self, mock_process, mock_subprocess
    ):
        """Test YouTube handler with realistic yt-dlp interface mocking."""
        handler = YouTubeHandler("test-key", "test-model")

        # Mock successful yt-dlp calls
        def mock_subprocess_call(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()

            if "--flat-playlist" in cmd:
                # Mock channel/search listing
                result.stdout = (
                    "https://youtube.com/watch?v=test1|Test Video|test1|600|20240101"
                )
                return result
            elif "--dump-json" in cmd:
                # Mock metadata extraction
                result.stdout = json.dumps(
                    {"title": "Test Video", "channel": "Test Channel", "duration": 600}
                )
                return result
            else:
                # Mock subtitle extraction
                result.stdout = ""
                return result

        mock_subprocess.side_effect = mock_subprocess_call

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Create a real file for testing
            test_file = output_dir / "test1.md"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("# Test Video\n\nProcessed content")

            mock_process.return_value = [test_file]

            videos = handler._get_channel_videos("@testchannel")
            created_files = handler._process_videos(videos, output_dir)

            assert len(videos) == 1
            assert len(created_files) == 1
            assert created_files[0].exists()

    def test_youtube_handler_error_recovery(self):
        """Test YouTube handler error recovery and file creation."""
        handler = YouTubeHandler("test-key", "test-model")

        # Mock video that will cause processing error
        problem_video = {
            "url": "https://www.youtube.com/watch?v=error",
            "title": "Problem Video",
            "id": "error123",
            "duration": "600",
            "upload_date": "20240101",
            "channel": "Test Channel",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Mock transcript extraction to raise error
            with patch.object(
                handler, "_get_video_transcript", side_effect=Exception("Network error")
            ):
                created_files = handler._process_videos([problem_video], output_dir)

                # Should still create a file with error message
                assert len(created_files) == 1
                assert created_files[0].exists()

                content = created_files[0].read_text()
                assert "Error processing video" in content
                assert "Network error" in content
