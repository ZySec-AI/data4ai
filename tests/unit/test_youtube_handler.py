"""Unit tests for YouTube handler."""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from data4ai.exceptions import ValidationError
from data4ai.integrations.youtube_handler import YouTubeHandler


@pytest.fixture
def youtube_handler():
    """Create a YouTubeHandler instance for testing."""
    return YouTubeHandler(api_key="test-key", model="test-model")


@pytest.fixture
def mock_video_data():
    """Mock video data for testing."""
    return {
        "url": "https://www.youtube.com/watch?v=test123",
        "title": "Test Video Title",
        "id": "test123",
        "duration": "600",
        "upload_date": "20240101",
        "channel": "Test Channel",
    }


@pytest.fixture
def mock_vtt_content():
    """Mock VTT subtitle content."""
    return """WEBVTT
Kind: captions
Language: en

00:00:01.000 --> 00:00:03.000
This is the first line of transcript.

00:00:04.000 --> 00:00:06.000
This is the second line of transcript.

00:00:07.000 --> 00:00:10.000
This line has <c>formatting</c> and timestamps.
"""


class TestYouTubeHandler:
    """Test YouTube handler functionality."""

    def test_init(self):
        """Test YouTubeHandler initialization."""
        handler = YouTubeHandler("test-key", "test-model")
        assert handler.api_key == "test-key"
        assert handler.model == "test-model"
        assert handler.client is not None

    def test_extract_video_id_from_watch_url(self, youtube_handler):
        """Test extracting video ID from watch URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = youtube_handler._extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_from_short_url(self, youtube_handler):
        """Test extracting video ID from youtu.be URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = youtube_handler._extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_from_embed_url(self, youtube_handler):
        """Test extracting video ID from embed URL."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = youtube_handler._extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_invalid_url(self, youtube_handler):
        """Test extracting video ID from invalid URL."""
        url = "https://example.com/not-youtube"
        video_id = youtube_handler._extract_video_id(url)
        assert video_id is None

    def test_is_valid_video_id_valid(self, youtube_handler):
        """Test valid video ID validation."""
        assert youtube_handler._is_valid_video_id("dQw4w9WgXcQ")
        assert youtube_handler._is_valid_video_id("abcdefghijk")
        assert youtube_handler._is_valid_video_id("123-456-789")

    def test_is_valid_video_id_invalid(self, youtube_handler):
        """Test invalid video ID validation."""
        assert not youtube_handler._is_valid_video_id("")
        assert not youtube_handler._is_valid_video_id("short")
        assert not youtube_handler._is_valid_video_id("toolongvideoid")
        assert not youtube_handler._is_valid_video_id("invalid@chars")
        assert not youtube_handler._is_valid_video_id(None)

    def test_clean_vtt_transcript(self, youtube_handler, mock_vtt_content):
        """Test cleaning VTT transcript content."""
        cleaned = youtube_handler._clean_vtt_transcript(mock_vtt_content)

        # Should remove VTT headers, timestamps, and formatting
        assert "WEBVTT" not in cleaned
        assert "Kind:" not in cleaned
        assert "-->" not in cleaned
        assert "<c>" not in cleaned
        assert "</c>" not in cleaned

        # Should contain actual transcript content
        assert "This is the first line of transcript." in cleaned
        assert "This is the second line of transcript." in cleaned
        assert "This line has formatting and timestamps." in cleaned

    @patch("subprocess.run")
    def test_get_channel_videos_success(self, mock_run, youtube_handler):
        """Test successful channel video extraction."""
        # Mock subprocess output
        mock_result = MagicMock()
        mock_result.stdout = """https://youtube.com/watch?v=dQw4w9WgXcQ|Video 1|dQw4w9WgXcQ|300|20240101
https://youtube.com/watch?v=abc123defgh|Video 2|abc123defgh|400|20240102"""
        mock_run.return_value = mock_result

        videos = youtube_handler._get_channel_videos("@testchannel")

        assert len(videos) == 2
        assert videos[0]["id"] == "dQw4w9WgXcQ"
        assert videos[0]["title"] == "Video 1"
        assert videos[1]["id"] == "abc123defgh"
        assert videos[1]["title"] == "Video 2"

    @patch("subprocess.run")
    def test_get_channel_videos_command_error(self, mock_run, youtube_handler):
        """Test channel video extraction with command error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "yt-dlp")

        videos = youtube_handler._get_channel_videos("@testchannel")
        assert videos == []

    @patch("subprocess.run")
    def test_search_youtube_videos_success(self, mock_run, youtube_handler):
        """Test successful YouTube search."""
        mock_result = MagicMock()
        mock_result.stdout = """https://youtube.com/watch?v=dQw4w9WgXcQ|Python Tutorial|dQw4w9WgXcQ|300|20240101|Test Channel
https://youtube.com/watch?v=abc123defgh|Python Basics|abc123defgh|400|20240102|Another Channel"""
        mock_run.return_value = mock_result

        videos = youtube_handler._search_youtube_videos("python tutorial", 10)

        assert len(videos) == 2
        assert videos[0]["id"] == "dQw4w9WgXcQ"
        assert videos[0]["search_keyword"] == "python tutorial"
        assert videos[1]["id"] == "abc123defgh"

    @patch("subprocess.run")
    def test_search_youtube_videos_with_duplicates(self, mock_run, youtube_handler):
        """Test YouTube search with duplicate video IDs."""
        mock_result = MagicMock()
        mock_result.stdout = """https://youtube.com/watch?v=dQw4w9WgXcQ|Python Tutorial|dQw4w9WgXcQ|300|20240101|Test Channel
https://youtube.com/watch?v=dQw4w9WgXcQ|Python Tutorial|dQw4w9WgXcQ|300|20240101|Test Channel"""
        mock_run.return_value = mock_result

        videos = youtube_handler._search_youtube_videos("python", 10)

        # Should deduplicate based on video ID
        assert len(videos) == 1
        assert videos[0]["id"] == "dQw4w9WgXcQ"

    @patch("tempfile.TemporaryDirectory")
    @patch("subprocess.run")
    def test_get_video_transcript_success(
        self, mock_run, mock_temp_dir, youtube_handler, mock_vtt_content
    ):
        """Test successful transcript extraction."""
        # Mock temporary directory
        temp_path = Path("/tmp/test")
        mock_temp_dir.return_value.__enter__.return_value = str(temp_path)

        # Mock subprocess calls
        def subprocess_side_effect(*args, **kwargs):
            if "--dump-json" in args[0]:
                # Return metadata
                result = MagicMock()
                result.stdout = json.dumps(
                    {"title": "Test Video", "channel": "Test Channel"}
                )
                return result
            else:
                # Subtitle extraction
                result = MagicMock()
                return result

        mock_run.side_effect = subprocess_side_effect

        # Mock VTT file existence and content
        with (
            patch("pathlib.Path.glob") as mock_glob,
            patch("builtins.open", mock_open(read_data=mock_vtt_content)),
        ):
            mock_glob.return_value = [temp_path / "test123.en.vtt"]

            transcript, metadata = youtube_handler._get_video_transcript("test123")

            assert transcript is not None
            assert "This is the first line of transcript" in transcript
            assert metadata["title"] == "Test Video"

    @patch("tempfile.TemporaryDirectory")
    @patch("subprocess.run")
    def test_get_video_transcript_no_subtitles(
        self, mock_run, mock_temp_dir, youtube_handler
    ):
        """Test transcript extraction with no subtitles."""
        temp_path = Path("/tmp/test")
        mock_temp_dir.return_value.__enter__.return_value = str(temp_path)

        # Mock subprocess calls
        def subprocess_side_effect(*args, **kwargs):
            if "--dump-json" in args[0]:
                result = MagicMock()
                result.stdout = json.dumps({"title": "Test Video"})
                return result
            else:
                result = MagicMock()
                return result

        mock_run.side_effect = subprocess_side_effect

        # No VTT files found
        with patch("pathlib.Path.glob") as mock_glob:
            mock_glob.return_value = []

            transcript, metadata = youtube_handler._get_video_transcript("test123")

            assert transcript is None
            assert metadata["title"] == "Test Video"

    def test_create_markdown_with_transcript(self, youtube_handler, mock_video_data):
        """Test markdown creation with transcript."""
        transcript = "This is a test transcript with some content."
        metadata = {"title": "Updated Title", "channel": "Updated Channel"}

        with patch.object(youtube_handler, "_create_knowledge_notes") as mock_notes:
            mock_notes.return_value = "## Knowledge Notes\n\nProcessed content here."

            markdown = youtube_handler._create_markdown(
                mock_video_data, transcript, metadata
            )

            assert "# Test Video Title" in markdown
            assert "**Video ID:** test123" in markdown
            assert "**Channel:** Updated Channel" in markdown
            assert "## Knowledge Notes" in markdown

    def test_create_markdown_without_transcript(self, youtube_handler, mock_video_data):
        """Test markdown creation without transcript."""
        markdown = youtube_handler._create_markdown(mock_video_data, None, {})

        assert "# Test Video Title" in markdown
        assert "❌ No transcript available" in markdown

    @patch.object(YouTubeHandler, "_get_video_transcript")
    def test_process_videos_skip_existing(
        self, mock_get_transcript, youtube_handler, mock_video_data
    ):
        """Test processing videos with existing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Create existing file
            existing_file = output_dir / "test123.md"
            existing_file.write_text("# Existing content")

            created_files = youtube_handler._process_videos(
                [mock_video_data], output_dir
            )

            assert len(created_files) == 1
            assert created_files[0] == existing_file
            # Should not call transcript extraction for existing files
            mock_get_transcript.assert_not_called()

    @patch.object(YouTubeHandler, "_get_video_transcript")
    @patch.object(YouTubeHandler, "_create_markdown")
    def test_process_videos_success(
        self,
        mock_create_markdown,
        mock_get_transcript,
        youtube_handler,
        mock_video_data,
    ):
        """Test successful video processing."""
        mock_get_transcript.return_value = ("transcript", {"title": "Test"})
        mock_create_markdown.return_value = "# Test markdown content"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            created_files = youtube_handler._process_videos(
                [mock_video_data], output_dir
            )

            assert len(created_files) == 1
            assert created_files[0].name == "test123.md"
            assert created_files[0].exists()

    def test_extract_from_url_invalid_url(self, youtube_handler):
        """Test extracting from invalid YouTube URL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            with pytest.raises(ValidationError, match="Invalid YouTube URL"):
                youtube_handler.extract_from_url(
                    "https://example.com/invalid", output_dir
                )

    @patch.object(YouTubeHandler, "_process_videos")
    def test_extract_from_url_success(self, mock_process, youtube_handler):
        """Test successful URL extraction."""
        mock_process.return_value = [Path("test.md")]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

            result = youtube_handler.extract_from_url(url, output_dir)

            assert len(result) == 1
            # Verify the video data passed to _process_videos
            call_args = mock_process.call_args[0]
            video_list = call_args[0]
            assert len(video_list) == 1
            assert video_list[0]["id"] == "dQw4w9WgXcQ"
            assert video_list[0]["url"] == url

    @patch.object(YouTubeHandler, "_get_channel_videos")
    @patch.object(YouTubeHandler, "_process_videos")
    def test_extract_from_channel_success(
        self, mock_process, mock_get_videos, youtube_handler
    ):
        """Test successful channel extraction."""
        mock_get_videos.return_value = [mock_video_data for _ in range(5)]
        mock_process.return_value = [Path("test.md")]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            youtube_handler.extract_from_channel(
                "@testchannel", output_dir, max_videos=3
            )

            # Should limit to max_videos
            call_args = mock_process.call_args[0]
            video_list = call_args[0]
            assert len(video_list) == 3

    @patch.object(YouTubeHandler, "_get_channel_videos")
    def test_extract_from_channel_no_videos(self, mock_get_videos, youtube_handler):
        """Test channel extraction with no videos found."""
        mock_get_videos.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            result = youtube_handler.extract_from_channel("@testchannel", output_dir)

            assert result == []

    @patch.object(YouTubeHandler, "_search_youtube_videos")
    @patch.object(YouTubeHandler, "_process_videos")
    def test_extract_from_search_success(
        self, mock_process, mock_search, youtube_handler
    ):
        """Test successful search extraction."""
        mock_search.return_value = [mock_video_data]
        mock_process.return_value = [Path("test.md")]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            result = youtube_handler.extract_from_search(
                "python tutorial", output_dir, max_results=10
            )

            assert len(result) == 1
            mock_search.assert_called_once_with("python tutorial", 10)
