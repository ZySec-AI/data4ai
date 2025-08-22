# 🎯 Data4AI Examples

This directory contains practical, runnable examples demonstrating Data4AI's core functionality. Each example is designed to be educational and immediately useful.

## 📁 Example Files

| File | Description | Type |
|------|-------------|------|
| `01_basic_cli_examples.sh` | Core CLI commands and options | Shell Script |
| `02_python_api_examples.py` | Python API usage patterns | Python Script |
| `03_youtube_integration_examples.sh` | YouTube content extraction | Shell Script |
| `04_document_processing_examples.sh` | Document-based generation | Shell Script |

## 🚀 Quick Start

### Prerequisites

1. **Install Data4AI**:
   ```bash
   pip install data4ai
   ```

2. **Set up environment**:
   ```bash
   export OPENROUTER_API_KEY="your-key-here"
   export HF_TOKEN="your-hf-token"  # Optional, for publishing
   ```

3. **Verify setup**:
   ```bash
   data4ai env
   ```

### Running Examples

All examples include `--dry-run` flags by default to prevent accidental data generation. Remove these flags when you're ready to generate real datasets.

#### 1. Basic CLI Examples
```bash
cd examples
./01_basic_cli_examples.sh
```

Demonstrates:
- Simple prompt-based generation
- Different taxonomy levels (basic, balanced, advanced)
- Schema formats (alpaca, chatml)
- Advanced options and configurations

#### 2. Python API Examples
```bash
cd examples
python 02_python_api_examples.py
```

Demonstrates:
- Programmatic dataset generation
- Document-based processing
- Object-oriented API usage
- Batch processing multiple datasets
- Error handling and configuration

#### 3. YouTube Integration Examples
```bash
cd examples
./03_youtube_integration_examples.sh
```

Demonstrates:
- Single video extraction
- Channel content processing
- Search-based extraction
- Different output formats
- Advanced YouTube-specific options

#### 4. Document Processing Examples
```bash
cd examples
./04_document_processing_examples.sh
```

Demonstrates:
- Single document processing
- Multiple document directories
- Different file types (PDF, DOCX, MD, TXT)
- Content-aware generation
- Educational taxonomy levels

## 🎓 Example Scenarios

### Educational Content Creation
```bash
# Generate beginner programming Q&A
data4ai prompt \
  --repo programming-basics \
  --description "Basic Python programming concepts for beginners" \
  --taxonomy basic \
  --count 100

# Generate advanced computer science discussions
data4ai doc ./textbooks/ \
  --repo cs-advanced \
  --description "Advanced computer science concepts" \
  --taxonomy advanced \
  --dataset chatml \
  --count 200
```

### Training Data for Models
```bash
# Instruction-following dataset
data4ai prompt \
  --repo code-instructions \
  --description "Programming task instructions" \
  --dataset alpaca \
  --count 500

# Conversational AI dataset
data4ai youtube "@TechExplained" \
  --repo tech-conversations \
  --description "Technology explanation conversations" \
  --dataset chatml \
  --count 300
```

### Content Processing Pipeline
```bash
# Extract knowledge from multiple sources
data4ai doc ./research_papers/ --repo research-qa --count 200
data4ai youtube "machine learning tutorial" --search --repo ml-tutorials --count 150
data4ai prompt --repo ml-synthetic --description "Machine learning Q&A" --count 250

# Publish all to HuggingFace
data4ai push --repo research-qa
data4ai push --repo ml-tutorials  
data4ai push --repo ml-synthetic
```

## 🔧 Customization Guide

### Environment Variables
```bash
# Core configuration
export OPENROUTER_API_KEY="your-key"           # Required
export OPENROUTER_MODEL="openai/gpt-4o-mini"  # Optional
export HF_TOKEN="your-hf-token"               # For publishing
export HF_ORG="YourOrganization"              # For publishing

# Advanced options
export TEMPERATURE="0.7"                      # Generation creativity
export BATCH_SIZE="5"                         # Processing batch size
export MAX_RETRIES="3"                        # Error recovery
```

### Command Options

#### Taxonomy Levels
- `--taxonomy basic`: Focus on Remember & Understand (Bloom's taxonomy)
- `--taxonomy balanced`: Even distribution across all cognitive levels
- `--taxonomy advanced`: Focus on Analyze, Evaluate & Create

#### Schema Formats
- `--dataset alpaca`: Instruction-following format (instruction, input, output)
- `--dataset chatml`: Conversation format (messages array)

#### Quality Controls
- `--seed 42`: Reproducible results
- `--temperature 0.1-1.0`: Control creativity (0.1=focused, 1.0=creative)
- `--batch-size N`: Process N items at a time
- `--dry-run`: Preview without generating

## 📊 Output Structure

Generated datasets follow this structure:
```
data/
├── repo-name/
│   ├── data.jsonl              # Generated dataset
│   ├── metadata.json           # Generation metadata
│   └── config.json             # Configuration used
└── repo-name.log               # Generation log

outputs/
├── datasets/                   # Generated datasets
│   └── repo-name/
│       ├── data.jsonl          # Dataset file
│       ├── metadata.json       # Generation metadata
│       └── config.json         # Configuration used
└── youtube/                    # YouTube transcripts
    └── repo-name/
        ├── video1.md           # Transcript files
        └── video2.md
```

## 🔍 Troubleshooting

### Common Issues

#### "No API key found"
```bash
# Check environment
data4ai env

# Set API key
export OPENROUTER_API_KEY="your-key-here"
```

#### "Failed to extract transcript" (YouTube)
```bash
# Install/update yt-dlp
pip install --upgrade yt-dlp

# Check video accessibility
yt-dlp --list-formats "https://youtube.com/watch?v=VIDEO_ID"
```

#### "Document processing failed"
```bash
# Check file permissions
ls -la your-document.pdf

# Try with a simple text file first
echo "Test content" > test.txt
data4ai doc test.txt --repo test --count 5 --dry-run
```

#### Rate limiting errors
```bash
# Reduce batch size
data4ai prompt --batch-size 1 --count 10 ...

# Add delays between requests
data4ai prompt --delay 2 --count 50 ...
```

### Debug Mode
Enable verbose logging for troubleshooting:
```bash
# Set debug environment
export DEBUG=1
export LOG_LEVEL=DEBUG

# Run with verbose output
data4ai prompt --repo debug-test --count 5 --dry-run
```

## 📚 Additional Resources

- **[Core Documentation](../docs/README.md)**: Complete feature reference
- **[Commands Guide](../docs/COMMANDS.md)**: Detailed command documentation
- **[YouTube Integration](../docs/YOUTUBE.md)**: YouTube-specific features
- **[API Reference](../docs/EXAMPLES.md)**: More code examples

## 🤝 Contributing Examples

Have a useful example? Consider contributing:

1. Create a clear, documented example
2. Include both CLI and Python versions when applicable
3. Add error handling and --dry-run support
4. Test with different configurations
5. Submit a pull request

Example format:
```bash
#!/bin/bash
# Brief description of what this example demonstrates

echo "Example: Description"
echo "--------------------"

# Show the command with explanation
data4ai command \
  --option1 value1 \
  --option2 value2 \
  --dry-run  # Always include dry-run in examples

echo "✅ Example completed!"
```

## 📝 License

These examples are part of Data4AI and follow the same license terms.