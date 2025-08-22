"""YouTube video transcript extraction and processing for Data4AI."""

import json
import logging
import re
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from data4ai.checkpoint import SessionCheckpointManager
from data4ai.client import OpenRouterConfig, SyncOpenRouterClient
from data4ai.content_tracker import ContentTracker
from data4ai.exceptions import ValidationError
from data4ai.session_manager import SessionData, SessionManager

logger = logging.getLogger("data4ai")


class YouTubeHandler:
    """Handle YouTube video transcript extraction and processing with session support."""

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
        session_manager: Optional[SessionManager] = None,
    ):
        """Initialize YouTube handler.

        Args:
            api_key: OpenRouter API key
            model: Model to use for processing
            session_manager: Optional session manager for resumable workflows
        """
        self.api_key = api_key
        self.model = model
        self.session_manager = session_manager
        self.content_tracker = ContentTracker()

        # Initialize OpenRouter client
        config = OpenRouterConfig(
            api_key=api_key,
            model=model,
            max_tokens=8000,
            temperature=0.1,
        )
        self.client = SyncOpenRouterClient(config)

    def extract_from_channel(
        self, channel_handle: str, output_dir: Path, max_videos: Optional[int] = None
    ) -> list[Path]:
        """Extract transcripts from a YouTube channel.

        Args:
            channel_handle: Channel handle (@channelname or URL)
            output_dir: Directory to save markdown files
            max_videos: Maximum number of videos to process

        Returns:
            List of paths to created markdown files
        """
        logger.info(f"Extracting videos from channel: {channel_handle}")

        # Get channel videos
        videos = self._get_channel_videos(channel_handle)
        if not videos:
            logger.warning(f"No videos found for channel: {channel_handle}")
            return []

        # Limit videos if specified
        if max_videos:
            videos = videos[:max_videos]
            logger.info(f"Processing first {len(videos)} videos")

        return self._process_videos(videos, output_dir)

    def extract_from_search(
        self, keywords: str, output_dir: Path, max_results: int = 50
    ) -> list[Path]:
        """Extract transcripts from YouTube search results.

        Args:
            keywords: Comma-separated search keywords
            output_dir: Directory to save markdown files
            max_results: Maximum results per keyword

        Returns:
            List of paths to created markdown files
        """
        logger.info(f"Searching YouTube for: {keywords}")

        # Search for videos
        videos = self._search_youtube_videos(keywords, max_results)
        if not videos:
            logger.warning(f"No videos found for search: {keywords}")
            return []

        return self._process_videos(videos, output_dir)

    def extract_from_url(self, video_url: str, output_dir: Path) -> list[Path]:
        """Extract transcript from a single YouTube video.

        Args:
            video_url: YouTube video URL
            output_dir: Directory to save markdown file

        Returns:
            List containing path to created markdown file
        """
        logger.info(f"Processing video: {video_url}")

        # Extract video ID from URL
        video_id = self._extract_video_id(video_url)
        if not video_id:
            raise ValidationError(f"Invalid YouTube URL: {video_url}")

        # Create video info
        video = {
            "url": video_url,
            "id": video_id,
            "title": f"Video {video_id}",  # Will be updated from metadata
            "duration": "Unknown",
            "upload_date": "Unknown",
            "channel": "Unknown",
        }

        return self._process_videos([video], output_dir)

    def _get_channel_videos(self, channel_handle: str) -> list[dict[str, Any]]:
        """Get all videos from a YouTube channel."""
        # Handle different channel formats
        if channel_handle.startswith("https://www.youtube.com/@"):
            channel_url = channel_handle + "/videos"
        elif channel_handle.startswith("@"):
            channel_url = f"https://www.youtube.com/{channel_handle}/videos"
        else:
            channel_url = f"https://www.youtube.com/@{channel_handle}/videos"

        try:
            cmd = [
                "yt-dlp",
                "--flat-playlist",
                "--print",
                "%(url)s|%(title)s|%(id)s|%(duration)s|%(upload_date)s",
                channel_url,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            videos = []
            for line in result.stdout.strip().split("\n"):
                if line and "|" in line:
                    parts = line.split("|", 4)  # Limit splits to handle titles with |
                    if len(parts) >= 3:
                        videos.append(
                            {
                                "url": parts[0],
                                "title": parts[1],
                                "id": parts[2],
                                "duration": parts[3] if len(parts) > 3 else "Unknown",
                                "upload_date": (
                                    parts[4] if len(parts) > 4 else "Unknown"
                                ),
                            }
                        )

            logger.info(f"Found {len(videos)} videos in channel")
            return videos

        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting channel videos: {e}")
            return []

    def _search_youtube_videos(
        self, keywords: str, max_results: int
    ) -> list[dict[str, Any]]:
        """Search YouTube for videos using keywords."""
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        all_videos = []

        for keyword in keyword_list:
            try:
                logger.info(f"Searching for: {keyword}")

                cmd = [
                    "yt-dlp",
                    "--flat-playlist",
                    "--print",
                    "%(url)s|%(title)s|%(id)s|%(duration)s|%(upload_date)s|%(channel)s",
                    f"ytsearch{max_results}:{keyword}",
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, check=True)

                keyword_videos = []
                for line in result.stdout.strip().split("\n"):
                    if line and "|" in line:
                        parts = line.split("|", 5)  # Limit splits
                        if len(parts) >= 3:
                            video_id = parts[2].strip()
                            # Validate video ID format
                            if self._is_valid_video_id(video_id):
                                video = {
                                    "url": parts[0],
                                    "title": parts[1],
                                    "id": video_id,
                                    "duration": (
                                        parts[3] if len(parts) > 3 else "Unknown"
                                    ),
                                    "upload_date": (
                                        parts[4] if len(parts) > 4 else "Unknown"
                                    ),
                                    "channel": (
                                        parts[5] if len(parts) > 5 else "Unknown"
                                    ),
                                    "search_keyword": keyword,
                                }
                                keyword_videos.append(video)

                logger.info(f"Found {len(keyword_videos)} videos for '{keyword}'")
                all_videos.extend(keyword_videos)

            except subprocess.CalledProcessError as e:
                logger.warning(f"Error searching for '{keyword}': {e}")

        # Remove duplicates based on video ID
        unique_videos = {}
        for video in all_videos:
            if video["id"] not in unique_videos:
                unique_videos[video["id"]] = video

        final_videos = list(unique_videos.values())
        logger.info(f"Total unique videos found: {len(final_videos)}")

        return final_videos

    def _process_videos(
        self, videos: list[dict[str, Any]], output_dir: Path, max_workers: int = 3
    ) -> list[Path]:
        """Process list of videos and create markdown files with multithreading."""
        output_dir.mkdir(parents=True, exist_ok=True)
        created_files = []

        # Filter out videos that already exist
        videos_to_process = []
        for video in videos:
            video_id = video["id"]
            output_file = output_dir / f"{video_id}.md"
            if output_file.exists():
                logger.info(f"Skipping {video_id} (already exists)")
                created_files.append(output_file)
            else:
                videos_to_process.append(video)

        if not videos_to_process:
            return created_files

        logger.info(
            f"Processing {len(videos_to_process)} videos with {max_workers} threads"
        )

        # Process videos in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all video processing tasks
            future_to_video = {
                executor.submit(self._process_single_video, video, output_dir): video
                for video in videos_to_process
            }

            # Collect results as they complete
            for future in as_completed(future_to_video):
                video = future_to_video[future]
                try:
                    output_file = future.result()
                    if output_file:
                        created_files.append(output_file)
                        logger.info(f"✅ Completed {video['id']}.md")
                except Exception as e:
                    logger.warning(f"❌ Failed to process video {video['id']}: {e}")
                    # Create error file
                    output_file = output_dir / f"{video['id']}.md"
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(
                            f"# {video['title']}\n\n❌ Error processing video: {str(e)}"
                        )
                    created_files.append(output_file)

        return created_files

    def _process_single_video(self, video: dict[str, Any], output_dir: Path) -> Path:
        """Process a single video and create markdown file."""
        video_id = video["id"]
        output_file = output_dir / f"{video_id}.md"

        try:
            # Get transcript and metadata
            transcript, metadata = self._get_video_transcript(video_id)

            # Update video info with metadata if available
            if metadata.get("title"):
                video["title"] = metadata["title"]

            # Create markdown content
            markdown_content = self._create_markdown(video, transcript, metadata)

            # Save to file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            # Small delay to be respectful to APIs (reduced since we have concurrency control)
            time.sleep(0.2)

            return output_file

        except Exception as e:
            logger.warning(f"Error processing video {video_id}: {e}")
            raise

    def _get_video_transcript(
        self, video_id: str
    ) -> tuple[Optional[str], dict[str, Any]]:
        """Extract transcript and metadata from a video."""
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            # Get video metadata
            info_cmd = ["yt-dlp", "--dump-json", "--no-download", video_url]

            info_result = subprocess.run(
                info_cmd, capture_output=True, text=True, check=True
            )
            metadata = json.loads(info_result.stdout)

            # Get subtitles in a temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                subtitle_cmd = [
                    "yt-dlp",
                    "--write-subs",
                    "--write-auto-subs",
                    "--sub-langs",
                    "en",
                    "--skip-download",
                    "--output",
                    f"{temp_dir}/%(id)s.%(ext)s",
                    video_url,
                ]

                subprocess.run(subtitle_cmd, capture_output=True, text=True)

                # Look for subtitle files
                temp_path = Path(temp_dir)
                vtt_files = list(temp_path.glob(f"{video_id}*.vtt"))

                if not vtt_files:
                    logger.warning(f"No subtitles found for {video_id}")
                    return None, metadata

                # Process VTT file
                with open(vtt_files[0], encoding="utf-8") as f:
                    vtt_content = f.read()

                transcript = self._clean_vtt_transcript(vtt_content)
                return transcript, metadata

        except Exception as e:
            logger.error(f"Error getting transcript for {video_id}: {e}")
            return None, {}

    def _clean_vtt_transcript(self, vtt_content: str) -> str:
        """Clean VTT transcript content."""
        lines = vtt_content.split("\n")
        transcript_lines = []

        for line in lines:
            line = line.strip()
            # Skip VTT headers, timestamps, and empty lines
            if (
                line
                and not line.startswith("WEBVTT")
                and not line.startswith("NOTE")
                and not line.startswith("Kind:")
                and not line.startswith("Language:")
                and "-->" not in line
                and not line.isdigit()
                and not line.startswith("[")
                and not line.startswith("<")
            ):
                # Clean timestamps and formatting
                line = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", " ", line)
                line = re.sub(r"<[^>]+>", "", line)
                line = re.sub(r"\s+", " ", line).strip()

                if line and len(line) > 2:
                    transcript_lines.append(line)

        return " ".join(transcript_lines)

    def _create_markdown(
        self, video: dict[str, Any], transcript: Optional[str], metadata: dict[str, Any]
    ) -> str:
        """Create markdown content for a video."""
        video_id = video["id"]
        title = video["title"]

        # Create header with metadata
        markdown_content = f"""# {title}

**Video ID:** {video_id}
**URL:** {video["url"]}
**Duration:** {video.get("duration", "Unknown")}
**Upload Date:** {video.get("upload_date", "Unknown")}
**Channel:** {metadata.get("channel", video.get("channel", "Unknown"))}
**Processed:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""

        if transcript:
            # Process transcript into structured knowledge notes using AI
            try:
                knowledge_notes = self._create_knowledge_notes(transcript, metadata)
                markdown_content += knowledge_notes
            except Exception as e:
                logger.warning(f"Error creating knowledge notes for {video_id}: {e}")
                markdown_content += f"## Raw Transcript\n\n{transcript}"
        else:
            markdown_content += "❌ No transcript available for this video."

        return markdown_content

    def _create_knowledge_notes(self, transcript: str, metadata: dict[str, Any]) -> str:
        """Create structured knowledge notes from transcript using AI."""
        if not transcript:
            return "No transcript available."

        # Limit transcript length for processing
        max_transcript_length = 15000
        if len(transcript) > max_transcript_length:
            transcript = transcript[:max_transcript_length] + "..."

        prompt = f"""Transform this YouTube video transcript into clean, structured knowledge notes.

Video: {metadata.get("title", "Unknown")}
Duration: {metadata.get("duration", "Unknown")} seconds

Transcript:
{transcript}

Create comprehensive structured details should be clear for reader to understand follow content.

IMPORTANT RULES:
1. Remove ALL speaker names and attributions
2. Present information as factual knowledge, not as "someone said"
3. Organize content logically by topic, not chronologically
4. Focus on technical concepts, methods, and actionable insights
5. Use clear, professional language
6. Include specific technical details when mentioned
7. Do not include person name or reference, this is only for knowledge notes
8. Markdown format should be clear and easy to read, use markdown syntax to format the content

Return ONLY the structured markdown notes."""

        try:
            response = self.client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical writer who creates comprehensive knowledge notes from video transcripts. Remove all speaker attributions and present pure knowledge content in a well-structured format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=8000,
            )

            return response["choices"][0]["message"]["content"].strip()

        except Exception as e:
            logger.warning(f"Error creating AI knowledge notes: {e}")
            return f"## Raw Transcript\n\n{transcript}"

    def _extract_video_id(self, video_url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
            r"youtube\.com/v/([a-zA-Z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)

        return None

    def _is_valid_video_id(self, video_id: str) -> bool:
        """Validate YouTube video ID format."""
        return (
            video_id
            and len(video_id) == 11
            and video_id.replace("-", "").replace("_", "").isalnum()
        )

    # Session-aware methods for resumable workflows

    def extract_from_channel_with_session(
        self,
        session_data: SessionData,
        channel_handle: str,
        output_dir: Path,
        max_videos: Optional[int] = None,
        incremental: bool = True,
    ) -> tuple[list[Path], dict[str, Any]]:
        """Extract transcripts from YouTube channel with session support.

        Args:
            session_data: Session data for tracking progress
            channel_handle: Channel handle (@channelname or URL)
            output_dir: Directory to save markdown files
            max_videos: Maximum number of videos to process
            incremental: Only process new/changed videos

        Returns:
            Tuple of (created_files, processing_stats)
        """
        logger.info(f"Starting session-based extraction from channel: {channel_handle}")

        # Initialize session checkpoint manager
        checkpoint_manager = SessionCheckpointManager(session_data.session_id)

        # Load or create extraction stage checkpoint
        extraction_checkpoint = checkpoint_manager.load_stage_checkpoint("extraction")
        if not extraction_checkpoint:
            extraction_checkpoint = checkpoint_manager.create_stage_checkpoint(
                stage_name="extraction",
                stage_config={
                    "channel_handle": channel_handle,
                    "max_videos": max_videos,
                    "incremental": incremental,
                },
                input_source=channel_handle,
                output_target=str(output_dir),
                total_items=0,  # Will be updated when we get video list
            )

        # Get channel videos
        videos = self._get_channel_videos(channel_handle)
        if not videos:
            logger.warning(f"No videos found for channel: {channel_handle}")
            return [], {"total_videos": 0, "processed": 0, "skipped": 0, "failed": 0}

        # Limit videos if specified
        if max_videos:
            videos = videos[:max_videos]

        # Update total items count
        checkpoint_manager.add_pending_items("extraction", [v["id"] for v in videos])

        # Process videos with session tracking
        return self._process_videos_with_session(
            videos, output_dir, session_data, checkpoint_manager, incremental
        )

    def extract_from_search_with_session(
        self,
        session_data: SessionData,
        keywords: str,
        output_dir: Path,
        max_results: int = 50,
        incremental: bool = True,
    ) -> tuple[list[Path], dict[str, Any]]:
        """Extract transcripts from YouTube search with session support.

        Args:
            session_data: Session data for tracking progress
            keywords: Comma-separated search keywords
            output_dir: Directory to save markdown files
            max_results: Maximum results per keyword
            incremental: Only process new/changed videos

        Returns:
            Tuple of (created_files, processing_stats)
        """
        logger.info(f"Starting session-based search extraction: {keywords}")

        # Initialize session checkpoint manager
        checkpoint_manager = SessionCheckpointManager(session_data.session_id)

        # Load or create extraction stage checkpoint
        extraction_checkpoint = checkpoint_manager.load_stage_checkpoint("extraction")
        if not extraction_checkpoint:
            extraction_checkpoint = checkpoint_manager.create_stage_checkpoint(
                stage_name="extraction",
                stage_config={
                    "keywords": keywords,
                    "max_results": max_results,
                    "incremental": incremental,
                },
                input_source=f"search:{keywords}",
                output_target=str(output_dir),
                total_items=0,
            )

        # Search for videos
        videos = self._search_youtube_videos(keywords, max_results)
        if not videos:
            logger.warning(f"No videos found for search: {keywords}")
            return [], {"total_videos": 0, "processed": 0, "skipped": 0, "failed": 0}

        # Update total items count
        checkpoint_manager.add_pending_items("extraction", [v["id"] for v in videos])

        # Process videos with session tracking
        return self._process_videos_with_session(
            videos, output_dir, session_data, checkpoint_manager, incremental
        )

    def _process_videos_with_session(
        self,
        videos: list[dict[str, Any]],
        output_dir: Path,
        session_data: SessionData,
        checkpoint_manager: SessionCheckpointManager,
        incremental: bool = True,
    ) -> tuple[list[Path], dict[str, Any]]:
        """Process videos with session tracking and smart skipping.

        Args:
            videos: List of video information
            output_dir: Output directory
            session_data: Session data
            checkpoint_manager: Checkpoint manager for this session
            incremental: Whether to skip unchanged content

        Returns:
            Tuple of (created_files, processing_stats)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        created_files = []
        stats = {"total_videos": len(videos), "processed": 0, "skipped": 0, "failed": 0}

        # Get extraction checkpoint info
        extraction_info = checkpoint_manager.get_stage_resume_info("extraction")
        completed_items = set(
            extraction_info.get("completed_items", []) if extraction_info else []
        )

        for video in videos:
            video_id = video["id"]
            output_file = output_dir / f"{video_id}.md"

            try:
                # Check if we should skip this video
                should_skip = False

                if incremental and video_id in completed_items:
                    should_skip = True
                    logger.debug(f"Skipping {video_id} (already completed)")

                elif output_file.exists() and incremental:
                    # Check if content has changed
                    # content_id = self.content_tracker.create_youtube_content_id(video)

                    if video_id in session_data.content_items:
                        # cached_item = session_data.content_items[video_id]
                        # For now, skip if file exists (could add content hash comparison)
                        should_skip = True
                        logger.debug(f"Skipping {video_id} (file exists)")

                if should_skip:
                    created_files.append(output_file)
                    stats["skipped"] += 1

                    # Update session tracking
                    (
                        self.session_manager.update_content_item_status(
                            session_data, video_id, "skipped", "extraction"
                        )
                        if self.session_manager
                        else None
                    )

                    checkpoint_manager.update_stage_progress(
                        "extraction", skipped_items=[video_id]
                    )
                    continue

                # Process the video
                start_time = time.time()

                # Get transcript and metadata
                transcript, metadata = self._get_video_transcript(video_id)

                # Update video info with metadata if available
                if metadata.get("title"):
                    video["title"] = metadata["title"]
                if metadata.get("channel"):
                    video["channel"] = metadata["channel"]

                # Create content hash for change tracking
                content_hash = self.content_tracker.create_youtube_content_hash(
                    video, transcript
                )

                # Add/update content item in session
                if self.session_manager:
                    if video_id not in session_data.content_items:
                        self.session_manager.add_content_item(
                            session_data,
                            item_id=video_id,
                            source_path=video["url"],
                            content_hash=content_hash,
                            size=len(transcript) if transcript else 0,
                            metadata=video,
                        )

                    self.session_manager.update_content_item_status(
                        session_data, video_id, "processing", "extraction"
                    )

                # Create markdown content
                markdown_content = self._create_markdown(video, transcript, metadata)

                # Save to file
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                created_files.append(output_file)
                stats["processed"] += 1

                processing_time = time.time() - start_time

                # Update session and checkpoint
                if self.session_manager:
                    self.session_manager.update_content_item_status(
                        session_data, video_id, "completed", "extraction"
                    )

                checkpoint_manager.update_stage_progress(
                    "extraction",
                    completed_items=[video_id],
                    processing_time=processing_time,
                    api_usage={"videos_processed": 1},
                )

                logger.info(f"Processed {video_id} in {processing_time:.2f}s")

                # Small delay to be respectful
                time.sleep(0.5)

            except Exception as e:
                stats["failed"] += 1
                logger.warning(f"Error processing video {video_id}: {e}")

                # Create minimal error file
                try:
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(
                            f"# {video['title']}\n\n❌ Error processing video: {str(e)}"
                        )
                    created_files.append(output_file)
                except Exception:
                    pass

                # Update session and checkpoint with failure
                if self.session_manager:
                    self.session_manager.update_content_item_status(
                        session_data, video_id, "failed", "extraction"
                    )

                checkpoint_manager.update_stage_progress(
                    "extraction",
                    failed_items=[video_id],
                    error_info={"video_id": video_id, "error": str(e)},
                )

        # Update session manager
        if self.session_manager:
            self.session_manager.update_session(session_data)

        logger.info(
            f"Extraction completed: {stats['processed']} processed, "
            f"{stats['skipped']} skipped, {stats['failed']} failed"
        )

        return created_files, stats

    def resume_extraction(
        self, session_id: str
    ) -> Optional[tuple[list[Path], dict[str, Any]]]:
        """Resume a previously interrupted extraction session.

        Args:
            session_id: Session ID to resume

        Returns:
            Tuple of (created_files, stats) or None if session not found
        """
        if not self.session_manager:
            logger.error("Cannot resume: no session manager provided")
            return None

        session_data = self.session_manager.load_session(session_id)
        if not session_data:
            logger.error(f"Session not found: {session_id}")
            return None

        checkpoint_manager = SessionCheckpointManager(session_id)
        extraction_info = checkpoint_manager.get_stage_resume_info("extraction")

        if not extraction_info or not extraction_info.get("can_resume"):
            logger.info(f"Session {session_id} has no pending extraction work")
            return [], {"total_videos": 0, "processed": 0, "skipped": 0, "failed": 0}

        logger.info(f"Resuming extraction session: {session_id}")
        logger.info(f"Pending items: {extraction_info['pending_count']}")

        # Get source configuration from session
        source_config = session_data.source_config
        source_type = session_data.source_type

        # Determine output directory
        output_dir = Path("outputs/youtube") / session_data.output_repo

        if source_type == "youtube_channel":
            channel_handle = source_config.get("channel_handle")
            max_videos = source_config.get("max_videos")

            return self.extract_from_channel_with_session(
                session_data, channel_handle, output_dir, max_videos, incremental=True
            )

        elif source_type == "youtube_search":
            keywords = source_config.get("keywords")
            max_results = source_config.get("max_results", 50)

            return self.extract_from_search_with_session(
                session_data, keywords, output_dir, max_results, incremental=True
            )

        else:
            logger.error(f"Unsupported source type for resume: {source_type}")
            return None

    def get_session_summary(self, session_id: str) -> Optional[dict[str, Any]]:
        """Get comprehensive summary of a YouTube processing session.

        Args:
            session_id: Session ID to summarize

        Returns:
            Session summary or None if session not found
        """
        if not self.session_manager:
            return None

        session_data = self.session_manager.load_session(session_id)
        if not session_data:
            return None

        checkpoint_manager = SessionCheckpointManager(session_id)
        checkpoint_summary = checkpoint_manager.get_session_summary()
        session_summary = self.session_manager.get_session_summary(session_data)

        return {
            **session_summary,
            "checkpoint_details": checkpoint_summary,
            "can_resume": any(
                stage_info.get("pending", 0) > 0
                for stage_info in checkpoint_summary.get("stages", {}).values()
            ),
        }
