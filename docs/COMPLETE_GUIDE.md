# Data4AI Complete Documentation

## Table of Contents

- [Installation & Setup](#installation--setup)
- [Environment Configuration](#environment-configuration)
- [Command Reference](#command-reference)
- [Quality Features](#quality-features)
- [Advanced Usage](#advanced-usage)
- [Python API](#python-api)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Installation & Setup

### Installation

```bash
uv pip install data4ai
```

### Environment Variables

Data4AI requires environment variables to be set in your terminal:

#### Option 1: Quick Setup (Current Session)
```bash
# Get your API key from https://openrouter.ai/keys
export OPENROUTER_API_KEY="your_key_here"

# Optional: Set a specific model (default: openai/gpt-4o-mini)
export OPENROUTER_MODEL="anthropic/claude-3-5-sonnet"

# Optional: Set default dataset schema (default: chatml)
export DEFAULT_SCHEMA="chatml"  # Options: chatml, alpaca

# Optional: For publishing to HuggingFace
export HF_TOKEN="your_huggingface_token"
```

#### Option 2: Using .env File
```bash
# Create a .env file in your project directory
echo 'OPENROUTER_API_KEY=your_key_here' > .env
# The tool will automatically load from .env
```

#### Option 3: Permanent Setup
```bash
# Add to your shell config (~/.bashrc, ~/.zshrc, or ~/.profile)
echo 'export OPENROUTER_API_KEY="your_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## Command Reference

### `data4ai prompt` - Generate from Description

Generate dataset from natural language description using AI.

```bash
data4ai prompt --repo <name> --description <text> [options]
```

**Options:**
- `--repo, -r`: Output directory and repo name (required)
- `--description, -desc`: Dataset description (required)
- `--count, -c`: Number of examples (default: 100)
- `--dataset, -d`: Schema format - chatml, alpaca (default: chatml)
- `--model, -m`: AI model to use
- `--temperature, -t`: Sampling temperature 0.0-2.0 (default: 0.7)
- `--batch-size`: Examples per batch (default: 10)
- `--taxonomy`: Bloom's taxonomy - balanced, basic, advanced
- `--all-levels`: Ensure all Bloom levels coverage
- `--dry-run`: Preview without generating

**Examples:**
```bash
# Basic generation
data4ai prompt \
  --repo my-dataset \
  --description "Create Python programming questions with answers" \
  --count 100

# With quality features
data4ai prompt \
  --repo advanced-dataset \
  --description "Complex machine learning interview questions" \
  --count 200 \
  --taxonomy balanced \
  --model "anthropic/claude-3-5-sonnet"
```

### `data4ai doc` - Generate from Documents

Generate dataset from document(s) - supports PDF, DOCX, MD, and TXT files.

```bash
data4ai doc <file_or_folder> --repo <name> [options]
```

**Options:**
- `--repo, -r`: Output directory and repo name (required)
- `--type, -t`: Extraction type - qa, summary, instruction (default: qa)
- `--count, -c`: Number of examples (default: 100)
- `--batch-size, -b`: Examples per batch (default: 10)
- `--chunk-size`: Document chunk size in characters (default: 1000)
- `--chunk-tokens`: Chunk size in tokens (overrides --chunk-size)
- `--chunk-overlap`: Overlap between chunks (default: 200)
- `--taxonomy`: Bloom's taxonomy - balanced, basic, advanced
- `--provenance`: Include source references
- `--all-levels`: Ensure all Bloom levels per document
- `--verify`: Enable quality verification pass
- `--long-context`: Merge chunks for long-context models
- `--recursive`: Scan folders recursively
- `--file-types`: Comma-separated file types (pdf,docx,md,txt)
- `--advanced`: Use advanced extraction (slower but better)
- `--per-document`: Write one dataset per input document
- `--dedup-strategy`: Deduplication - exact, fuzzy, content (default: content)
- `--dry-run`: Simulate generation

**Examples:**
```bash
# Basic document processing
data4ai doc research-paper.pdf \
  --repo paper-qa \
  --count 100

# Advanced processing with all quality features
data4ai doc documents/ \
  --repo knowledge-base \
  --count 500 \
  --taxonomy balanced \
  --provenance \
  --verify \
  --long-context \
  --advanced

# Process specific file types
data4ai doc /path/to/docs \
  --repo pdf-dataset \
  --file-types pdf \
  --count 200 \
  --recursive
```

### `data4ai push` - Upload to HuggingFace

Upload existing dataset to HuggingFace Hub.

```bash
data4ai push --repo <name> [options]
```

## Quality Features

### Bloom's Taxonomy Integration

Data4AI uses Bloom's Revised Taxonomy to ensure cognitive diversity in generated examples:

**Taxonomy Levels:**
- **Remember** (20%): Basic recall - "What is...?", "Define...", "List..."
- **Understand** (20%): Comprehension - "Explain...", "Summarize...", "Interpret..."
- **Apply** (15%): Use knowledge - "How would you...?", "Demonstrate...", "Solve..."
- **Analyze** (15%): Break down - "Compare...", "What caused...?", "Classify..."
- **Evaluate** (15%): Judge - "Critique...", "Justify...", "Which is better...?"
- **Create** (15%): Synthesize - "Design...", "Propose...", "What if...?"

**Usage:**
```bash
# Balanced distribution across all levels
--taxonomy balanced

# Focus on foundational skills
--taxonomy basic

# Emphasize higher-order thinking
--taxonomy advanced
```

### Provenance Tracking

Include source references with character offsets for transparency and verification:

```bash
--provenance
```

**Output Example:**
```json
{
  "messages": [...],
  "source_start": 1250,
  "source_end": 1890,
  "source_document": "research-paper.pdf"
}
```

### Quality Verification

Optional verification pass that reviews and improves generated examples:

```bash
--verify
```

**Note:** This doubles API calls but significantly improves quality.

### Long-Context Processing

Merge chunks for better coherence with long-context models:

```bash
--long-context
```

## Advanced Usage

### Token-Based Chunking

Use token count instead of character count for more precise chunking:

```bash
data4ai doc document.pdf \
  --repo token-dataset \
  --chunk-tokens 250 \
  --count 100
```

### Deduplication Strategies

Control how duplicates are handled:

```bash
# Content-based deduplication (default)
--dedup-strategy content --dedup-threshold 0.97

# Exact string matching
--dedup-strategy exact

# Fuzzy matching
--dedup-strategy fuzzy --dedup-threshold 0.85

# Instruction-level deduplication
--dedup-strategy instruction
```

### Per-Document vs Combined Output

```bash
# Generate separate dataset for each input document
--per-document

# Combine all documents into single dataset
--combined
```

## Python API

```python
from data4ai import generate_from_description, generate_from_document

# Generate from description
result = generate_from_description(
    description="Create Python interview questions",
    repo="python-interviews",
    count=50,
    schema="chatml",
    taxonomy="balanced"
)

# Generate from document with quality features
result = generate_from_document(
    document_path="research-paper.pdf",
    repo="paper-qa",
    extraction_type="qa",
    count=100,
    taxonomy="balanced",
    include_provenance=True,
    verify_quality=True
)

print(f"Generated {result['row_count']} examples")
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | Required |
| `OPENROUTER_MODEL` | Default model | `openai/gpt-4o-mini` |
| `DEFAULT_SCHEMA` | Default schema | `chatml` |
| `HF_TOKEN` | HuggingFace token | Optional |
| `DATA4AI_USE_DSPY` | Enable DSPy | `true` |

### Configuration File

Create `~/.data4ai/config.yaml`:

```yaml
openrouter:
  api_key: your_key_here
  model: openai/gpt-4o-mini
  temperature: 0.7

defaults:
  schema: chatml
  max_rows: 1000
  batch_size: 10

huggingface:
  token: your_hf_token
  organization: your_org
```

## Supported Schemas

### ChatML (Default - OpenAI format)
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is machine learning?"},
    {"role": "assistant", "content": "Machine learning is..."}
  ]
}
```

### Alpaca (Instruction tuning)
```json
{
  "instruction": "What is machine learning?",
  "input": "Explain in simple terms",
  "output": "Machine learning is..."
}
```

## Troubleshooting

### Common Issues

**API Key Not Found:**
```bash
export OPENROUTER_API_KEY="your_key_here"
```

**Permission Denied:**
```bash
# Check file permissions
chmod +r document.pdf

# For folders
chmod -R +r documents/
```

**Memory Issues:**
```bash
# Use smaller chunk sizes
--chunk-size 500

# Process fewer examples at once
--batch-size 5
```

**Rate Limiting:**
The tool automatically handles rate limits with exponential backoff. If you hit limits frequently, consider:
- Using a slower model
- Reducing batch size
- Adding delays between requests

### Debug Mode

Enable verbose logging:
```bash
data4ai --verbose doc document.pdf --repo debug-dataset
```

### Performance Optimization

**For Large Documents:**
```bash
# Use token-based chunking
--chunk-tokens 250

# Enable long-context merging
--long-context

# Use advanced extraction
--advanced
```

**For Speed:**
```bash
# Increase batch size
--batch-size 20

# Skip quality verification
# (don't use --verify)

# Use faster model
--model "openai/gpt-4o-mini"
```
