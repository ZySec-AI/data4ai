#!/bin/bash
# YouTube Integration Examples for Data4AI
# These examples demonstrate how to extract datasets from YouTube content

echo "🎬 Data4AI YouTube Integration Examples"
echo "======================================="

# Check environment setup
echo "📋 Checking environment..."
data4ai env

echo ""
echo "🔍 YouTube Source Types"
echo "----------------------"
echo "1. Single Video URL: Extract from one specific video"
echo "2. Channel Handle: Extract from channel's recent videos" 
echo "3. Search Query: Extract from search results"

echo ""
echo "🎯 Single Video Examples"
echo "------------------------"

# Example 1: Extract from a single YouTube video
echo "Example 1: Extract dataset from a single programming tutorial"
data4ai youtube "https://www.youtube.com/watch?v=example123" \
  --repo programming-tutorial \
  --description "Programming concepts and tutorials" \
  --count 25 \
  --dry-run

# Example 2: Extract with specific schema
echo "Example 2: Extract conversation-style data from educational video"
data4ai youtube "https://www.youtube.com/watch?v=example456" \
  --repo educational-content \
  --description "Educational Q&A about the video content" \
  --dataset chatml \
  --count 30 \
  --dry-run

echo ""
echo "📺 Channel Examples"  
echo "------------------"

# Example 3: Extract from a YouTube channel
echo "Example 3: Extract from programming education channel"
data4ai youtube "@PythonTutorials" \
  --repo python-channel-content \
  --description "Python programming tutorials and examples" \
  --count 100 \
  --max-videos 5 \
  --dry-run

# Example 4: Extract with custom taxonomy
echo "Example 4: Advanced content from tech channel"
data4ai youtube "@TechExplained" \
  --repo tech-advanced \
  --description "Advanced technology concepts and explanations" \
  --taxonomy advanced \
  --count 75 \
  --max-videos 3 \
  --dry-run

echo ""
echo "🔍 Search Examples"
echo "-----------------"

# Example 5: Extract from YouTube search results
echo "Example 5: Extract from Python tutorial search"
data4ai youtube "python programming tutorial" \
  --search \
  --repo python-search-content \
  --description "Python programming tutorials from search results" \
  --count 50 \
  --max-videos 10 \
  --dry-run

# Example 6: Machine learning search with specific parameters
echo "Example 6: Extract from machine learning search"
data4ai youtube "machine learning explained" \
  --search \
  --repo ml-explanations \
  --description "Machine learning concepts and explanations" \
  --dataset chatml \
  --taxonomy balanced \
  --count 60 \
  --max-videos 8 \
  --dry-run

echo ""
echo "⚙️ Advanced Options"
echo "------------------"

# Example 7: Extract transcripts only (no dataset generation)
echo "Example 7: Extract transcripts only for later processing"
data4ai youtube "@DataScienceChannel" \
  --repo data-science-transcripts \
  --max-videos 5 \
  --dry-run \
  --description "Data science content transcripts"

# Example 8: Custom model and temperature
echo "Example 8: Creative content extraction with custom settings"
data4ai youtube "creative coding tutorial" \
  --search \
  --repo creative-coding \
  --description "Creative coding tutorials and artistic programming" \
  --model "anthropic/claude-3-5-sonnet" \
  --temperature 0.8 \
  --count 40 \
  --max-videos 6 \
  --dry-run

# Example 9: Large-scale extraction with batch processing
echo "Example 9: Large-scale channel extraction"
data4ai youtube "@ComprehensiveProgramming" \
  --repo comprehensive-programming \
  --description "Complete programming curriculum from video content" \
  --count 500 \
  --max-videos 20 \
  --batch-size 10 \
  --dry-run

echo ""
echo "📊 Schema-Specific Examples"
echo "--------------------------"

# Example 10: Alpaca format for instruction-following
echo "Example 10: Instruction-following format from coding videos"
data4ai youtube "code review tutorial" \
  --search \
  --repo code-review-instructions \
  --description "Code review instructions and examples" \
  --dataset alpaca \
  --count 50 \
  --dry-run

# Example 11: ChatML format for conversational AI
echo "Example 11: Conversational format from interview videos"
data4ai youtube "tech interview questions" \
  --search \
  --repo tech-interview-chat \
  --description "Technical interview conversations" \
  --dataset chatml \
  --count 75 \
  --dry-run

echo ""
echo "🎓 Educational Use Cases"
echo "-----------------------"

# Example 12: Basic level content for beginners
echo "Example 12: Beginner-friendly programming content"
data4ai youtube "@BeginnerProgramming" \
  --repo programming-basics \
  --description "Basic programming concepts for beginners" \
  --taxonomy basic \
  --count 100 \
  --max-videos 10 \
  --dry-run

# Example 13: Advanced technical content
echo "Example 13: Advanced computer science concepts"
data4ai youtube "advanced algorithms explained" \
  --search \
  --repo algorithms-advanced \
  --description "Advanced algorithms and data structures" \
  --taxonomy advanced \
  --count 80 \
  --max-videos 12 \
  --dry-run

echo ""
echo "🔧 Troubleshooting Examples"
echo "--------------------------"

# Example 14: Test with a known good video
echo "Example 14: Test extraction with minimal parameters"
data4ai youtube "https://www.youtube.com/watch?v=test" \
  --repo test-extraction \
  --description "Test YouTube extraction" \
  --count 5 \
  --dry-run

# Example 15: Debug mode for troubleshooting
echo "Example 15: Debug mode extraction"
# Note: Add --verbose flag when available
data4ai youtube "@TestChannel" \
  --repo debug-test \
  --description "Debug extraction test" \
  --count 10 \
  --max-videos 2 \
  --dry-run

echo ""
echo "📁 Output Structure"
echo "-----------------"
echo "Generated datasets are saved to:"
echo "• data/<repo-name>/"
echo "• outputs/youtube/<repo-name>/ (transcripts)"
echo ""
echo "Transcript files include:"
echo "• Original video metadata"
echo "• Cleaned transcript text"
echo "• AI-processed knowledge notes"

echo ""
echo "💡 Tips for YouTube Extraction"
echo "-----------------------------"
echo "1. Use --dry-run first to test parameters"
echo "2. Start with small --count values for testing"
echo "3. --max-videos controls how many videos to process"
echo "4. Channel handles start with @ (e.g., @ChannelName)"
echo "5. Use quotes around search queries with spaces"
echo "6. Transcripts are cached for faster re-processing"

echo ""
echo "✅ YouTube examples completed!"
echo "💡 Remove --dry-run to start real extraction"
echo "📤 Use 'data4ai push --repo <repo-name>' to publish results"
echo "🔧 Ensure yt-dlp is installed: pip install yt-dlp"