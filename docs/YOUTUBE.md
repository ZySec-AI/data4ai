# 📺 YouTube Integration Guide

Data4AI can extract content from YouTube videos and convert them into high-quality training datasets. This is perfect for creating educational datasets from programming tutorials, conference talks, and other learning content.

## 🚀 Quick Start

### Install yt-dlp
YouTube integration requires `yt-dlp` for video transcript extraction:

```bash
# yt-dlp is automatically installed with Data4AI
pip install data4ai
```

### Basic Usage

```bash
# Extract from a channel
data4ai youtube @3Blue1Brown --repo math-videos --count 100

# Search for videos
data4ai youtube --search "python tutorial" --repo python-course --count 50

# Process a single video
data4ai youtube "https://youtube.com/watch?v=dQw4w9WgXcQ" --repo single-video
```

## 📋 Command Reference

### Basic Syntax
```bash
data4ai youtube [SOURCE] --repo [REPO_NAME] [OPTIONS]
```

### Source Types

**Channel Processing**
```bash
# Channel handle
data4ai youtube @channelname --repo dataset-name

# Full channel URL
data4ai youtube "https://youtube.com/@channelname" --repo dataset-name
```

**Search Processing**
```bash
# Search keywords (comma-separated)
data4ai youtube --search "python,tutorial,programming" --repo search-dataset
```

**Single Video Processing**
```bash
# Video URL
data4ai youtube "https://youtube.com/watch?v=VIDEO_ID" --repo video-dataset

# Short URL
data4ai youtube "https://youtu.be/VIDEO_ID" --repo video-dataset
```

### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--repo, -r` | Output directory and dataset name | Required |
| `--count, -c` | Number of examples to generate | 100 |
| `--dataset, -d` | Dataset schema (chatml, alpaca) | chatml |
| `--type, -t` | Extraction type (qa, summary, instruction) | qa |
| `--max-videos` | Maximum videos to process | All (channels), 50 (search) |
| `--dry-run` | Extract transcripts only, don't generate dataset | False |
| `--huggingface, -hf` | Upload to HuggingFace after generation | False |

## 📁 Output Structure

YouTube processing creates a clean folder structure:

```
# During processing (temporary)
outputs/youtube/
└── repo-name/
    ├── video-id-1.md
    ├── video-id-2.md
    └── search_results.json (for search mode)

# Final output
repo-name/
├── data.jsonl          # Combined dataset
├── metadata.json       # Generation metadata
└── README.md          # HuggingFace dataset card
```

## 🎯 Real-World Examples

### Educational Channel Dataset
```bash
# Process math education content
data4ai youtube @3Blue1Brown \
  --repo math-education \
  --count 200 \
  --max-videos 20 \
  --dataset chatml

# Process programming tutorials
data4ai youtube @freecodecamp \
  --repo programming-tutorials \
  --count 500 \
  --max-videos 50
```

### Conference Talk Dataset
```bash
# Extract PyConf talks
data4ai youtube @pycon \
  --repo python-conferences \
  --count 300 \
  --type summary

# Process specific conference playlist
data4ai youtube --search "PyCon 2024,Python conference" \
  --repo pycon-2024 \
  --count 100
```

### Multi-Topic Search Dataset
```bash
# Create diverse programming dataset
data4ai youtube --search "python tutorial,javascript tutorial,react tutorial" \
  --repo web-development \
  --count 400 \
  --max-videos 150
```

### Research and Analysis
```bash
# Extract from research channels
data4ai youtube --search "machine learning,AI research,deep learning" \
  --repo ai-research \
  --count 200 \
  --type instruction \
  --huggingface
```

## 🔧 Advanced Usage

### Dry Run Mode
Extract transcripts without generating a dataset (useful for content review):

```bash
data4ai youtube @channel --repo test-extraction --dry-run
```

### Different Extraction Types
```bash
# Question-Answer format (default)
data4ai youtube @channel --repo qa-dataset --type qa

# Summary format
data4ai youtube @channel --repo summary-dataset --type summary  

# Instruction format
data4ai youtube @channel --repo instruction-dataset --type instruction
```

### Dataset Schemas
```bash
# ChatML format (default) - for chat models
data4ai youtube @channel --repo chat-dataset --dataset chatml

# Alpaca format - for instruction following
data4ai youtube @channel --repo instruction-dataset --dataset alpaca
```

### Limiting Processing
```bash
# Limit channel processing
data4ai youtube @largechannel --repo limited-dataset --max-videos 10

# Search with specific limits
data4ai youtube --search "tutorials" --repo search-limited --max-videos 25
```

## 🏷️ Quality Features

YouTube datasets inherit all Data4AI quality features:

### Automatic Deduplication
```bash
# Content-based deduplication (default)
data4ai youtube @channel --repo dedup-dataset --count 200
```

### Bloom's Taxonomy
```bash
# Balanced cognitive levels
data4ai youtube @educational-channel --repo taxonomy-dataset --taxonomy balanced

# Advanced taxonomy levels
data4ai youtube @channel --repo advanced-dataset --taxonomy advanced
```

### Quality Verification
```bash
# Enable verification pass (slower but higher quality)
data4ai youtube @channel --repo verified-dataset --verify --count 100
```

## 📊 Content Processing

### What Gets Extracted

1. **Video Metadata**: Title, duration, upload date, channel name
2. **Transcript Content**: Auto-generated or manual subtitles
3. **Processed Knowledge**: AI-cleaned content without speaker attributions

### Content Cleaning

Data4AI automatically:
- ✅ Removes speaker attributions ("he said", "she mentioned")
- ✅ Cleans timestamp markers and VTT formatting
- ✅ Organizes content by topics, not chronologically
- ✅ Focuses on technical concepts and actionable insights
- ✅ Creates structured markdown with proper headings

### Example Output
```json
{
  "messages": [
    {
      "role": "user",
      "content": "How do you implement a binary search algorithm?"
    },
    {
      "role": "assistant", 
      "content": "Binary search is implemented by repeatedly dividing the search space in half. Start with low and high pointers, calculate the middle index, compare the target with the middle element, and adjust the search bounds accordingly..."
    }
  ],
  "video_metadata": {
    "video_id": "abc123",
    "title": "Data Structures: Binary Search",
    "channel": "CS Education",
    "duration": "600"
  }
}
```

## 🚨 Troubleshooting

### Common Issues

**yt-dlp not found**
```bash
# Install yt-dlp manually if needed
pip install yt-dlp
```

**No subtitles available**
- Some videos don't have subtitles - these will be skipped
- Data4AI prefers English subtitles (auto-generated or manual)

**API rate limiting**
- Data4AI includes automatic rate limiting
- For large channels, use `--max-videos` to limit processing

**Network issues**
- yt-dlp may fail on some videos - these are logged and skipped
- Retry the command to continue from where it left off

### Video Access Issues

**Private/Deleted Videos**
- Private videos are automatically skipped
- Deleted videos return errors but don't stop processing

**Age-Restricted Content**
- Some videos may be inaccessible due to age restrictions
- These are logged and skipped automatically

**Geographic Restrictions**
- Some content may not be available in all regions
- Use VPN if necessary (following YouTube's terms of service)

### Performance Tips

**For Large Channels**
```bash
# Process in chunks
data4ai youtube @largechannel --repo part1 --max-videos 50
data4ai youtube @largechannel --repo part2 --max-videos 50
```

**For Search Optimization**
```bash
# Use specific search terms
data4ai youtube --search "python functions" --repo specific-topic

# Better than generic terms
# data4ai youtube --search "programming" --repo too-broad
```

## 🤝 Best Practices

### Content Selection
- ✅ Choose educational channels with clear, structured content
- ✅ Focus on channels with good audio quality (affects auto-subtitles)
- ✅ Prefer channels with manual subtitles over auto-generated
- ❌ Avoid music videos, vlogs, or non-educational content

### Dataset Quality
- ✅ Use `--verify` for important datasets (slower but higher quality)
- ✅ Enable taxonomy for educational content (`--taxonomy balanced`)
- ✅ Start with `--dry-run` to review content before full processing
- ✅ Use specific search terms rather than broad keywords

### Processing Efficiency
- ✅ Use `--max-videos` to test with small batches first
- ✅ Process during off-peak hours for better network performance
- ✅ Monitor disk space (transcripts and datasets can be large)

## 📜 Legal and Ethical Considerations

### YouTube Terms of Service
- ✅ Data4AI extracts publicly available content only
- ✅ Respects YouTube's robots.txt and rate limits
- ✅ Does not download video files, only transcripts
- ❌ Does not circumvent access controls or paywalls

### Content Attribution
- ✅ Metadata includes video source information
- ✅ Generated datasets include provenance tracking
- ✅ Respects content creator attribution

### Fair Use Guidelines
- ✅ Use for educational and research purposes
- ✅ Transform content into structured learning data
- ✅ Add significant value through AI processing
- ❌ Do not redistribute raw transcripts

## 🔗 Integration with Other Data4AI Features

YouTube datasets work seamlessly with all Data4AI features:

```bash
# Combine with document processing
data4ai doc course-materials/ --repo course-docs --count 200
data4ai youtube @course-channel --repo course-videos --count 200

# Upload both to HuggingFace
data4ai push --repo course-docs --huggingface
data4ai push --repo course-videos --huggingface
```

---

**Need help?** Check the [main documentation](README.md) or [troubleshooting guide](TROUBLESHOOTING.md).