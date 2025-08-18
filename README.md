# Data4AI 🚀

> **AI-powered dataset generation for instruction tuning and model fine-tuning**

[![PyPI version](https://badge.fury.io/py/data4ai.svg)](https://pypi.org/project/data4ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Generate high-quality synthetic datasets using state-of-the-art language models through OpenRouter API. Perfect for creating training data for LLM fine-tuning.

## ✨ Key Features

- 🤖 **100+ AI Models** - Access to GPT-4, Claude, Llama, and more via OpenRouter
- 📊 **Multiple Formats** - Support for ChatML (default) and Alpaca schemas
- 🔮 **DSPy Integration** - Dynamic prompt optimization for better quality
- 📄 **Document Support** - Generate datasets from PDFs, Word docs, Markdown, and text files
- 🎯 **Quality Features** - Optional Bloom's taxonomy, provenance tracking, and quality verification
- 🤖 **Smart Generation** - Both prompt-based and document-based dataset creation
- ☁️ **HuggingFace Hub** - Direct dataset publishing
- ⚡ **Production Ready** - Rate limiting, checkpointing, deduplication

## 🚀 Quick Start

### Installation

```bash
pip install data4ai              # All features included
pip install data4ai[all]         # All features
```

### Set Up Environment Variables

Data4AI requires environment variables to be set in your terminal:

#### Option 1: Quick Setup (Current Session)
```bash
# Get your API key from https://openrouter.ai/keys
export OPENROUTER_API_KEY="your_key_here"

# Optional: Set a specific model (default: openai/gpt-4o-mini)
export OPENROUTER_MODEL="anthropic/claude-3-5-sonnet"  # Or another model

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

#### Check Your Setup
```bash
# Verify environment variables are set
echo "OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:0:10}..." # Shows first 10 chars
```

### Generate Your First Dataset

```bash
# Generate from description
data4ai prompt \
  --repo my-dataset \
  --description "Create 10 Python programming questions with answers" \
  --count 10

# View results
cat my-dataset/data.jsonl
```

## 📚 Common Use Cases

### 1. Generate from Natural Language

```bash
data4ai prompt \
  --repo customer-support \
  --description "Create customer support Q&A for a SaaS product" \
  --count 100
```

### 2. Generate from Documents

```bash
# From single PDF document
data4ai doc research-paper.pdf \
  --repo paper-qa \
  --type qa \
  --count 100

# From entire folder of documents
data4ai doc /path/to/docs/folder \
  --repo multi-doc-dataset \
  --type qa \
  --count 500 \
  --recursive

# Process only specific file types in folder
data4ai doc /path/to/docs \
  --repo pdf-only-dataset \
  --file-types pdf \
  --count 200

# From Word document with summaries
data4ai doc manual.docx \
  --repo manual-summaries \
  --type summary \
  --count 50

# From Markdown with advanced extraction
data4ai doc README.md \
  --repo docs-dataset \
  --type instruction \
  --advanced

# Generate with optional quality features
data4ai doc document.pdf \
  --repo high-quality-dataset \
  --count 200 \
  --taxonomy balanced \    # Use Bloom's taxonomy for diverse questions
  --provenance \           # Include source references
  --verify \               # Verify quality (2x API calls)
  --long-context           # Merge chunks for better coherence
```

### 4. High-Quality Generation

```bash
# Basic generation (simple and fast)
data4ai doc document.pdf --repo basic-dataset --count 100

# With cognitive diversity using Bloom's Taxonomy
data4ai doc document.pdf \
  --repo taxonomy-dataset \
  --count 100 \
  --taxonomy balanced  # Creates questions at all cognitive levels

# With source tracking for verifiable datasets
data4ai doc research-papers/ \
  --repo cited-dataset \
  --count 500 \
  --provenance  # Includes character offsets for each answer

# Full quality mode for production datasets
data4ai doc documents/ \
  --repo production-dataset \
  --count 1000 \
  --chunk-tokens 250 \     # Token-based chunking
  --taxonomy balanced \    # Cognitive diversity
  --provenance \          # Source tracking
  --verify \              # Quality verification
  --long-context          # Optimized context usage
```

### 5. Publish to HuggingFace

```bash
# Generate and publish
data4ai prompt \
  --repo my-public-dataset \
  --description "Educational content about machine learning" \
  --count 200 \
  --huggingface
```

## 📚 Available Commands

### `data4ai prompt`
Generate dataset from natural language description using AI.

```bash
data4ai prompt --repo <name> --description <text> [options]
```

### `data4ai doc`
Generate dataset from document(s) - supports PDF, DOCX, MD, and TXT files.

```bash
data4ai doc <file_or_folder> --repo <name> [options]
```

### `data4ai push`
Upload existing dataset to HuggingFace Hub.

```bash
data4ai push --repo <name> [options]
```

## 🐍 Python API

```python
from data4ai import generate_from_description, generate_from_document

# Generate from description (uses ChatML by default)
result = generate_from_description(
    description="Create Python interview questions",
    repo="python-interviews",
    count=50,
    schema="chatml"  # Optional, ChatML is default
)

# Generate from document with quality features
result = generate_from_document(
    document_path="research-paper.pdf",
    repo="paper-qa",
    extraction_type="qa",
    count=100,
    taxonomy="balanced",      # Optional: Bloom's taxonomy
    include_provenance=True,   # Optional: Source tracking
    verify_quality=True        # Optional: Quality verification
)

print(f"Generated {result['row_count']} examples")
```

## 📋 Supported Schemas

**ChatML** (Default - OpenAI format)
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is machine learning?"},
    {"role": "assistant", "content": "Machine learning is..."}
  ]
}
```

**Alpaca** (Instruction tuning)
```json
{
  "instruction": "What is machine learning?",
  "input": "Explain in simple terms",
  "output": "Machine learning is..."
}
```


## 🎯 Quality Features (Optional)

All quality features are **optional** - use them when you need higher quality datasets:

| Feature | Flag | Description | Performance Impact |
|---------|------|-------------|-------------------|
| **Token Chunking** | `--chunk-tokens N` | Use token count instead of characters | Minimal |
| **Bloom's Taxonomy** | `--taxonomy balanced` | Create cognitively diverse questions | None |
| **Provenance** | `--provenance` | Include source references | Minimal |
| **Quality Verification** | `--verify` | Verify and improve examples | 2x API calls |
| **Long Context** | `--long-context` | Merge chunks for coherence | May reduce API calls |

### When to Use Quality Features

- **Quick Prototyping**: No features needed - fast and simple
- **Production Datasets**: Use `--taxonomy` and `--verify`
- **Academic/Research**: Use all features for maximum quality
- **Citation Required**: Always use `--provenance`

## ⚙️ Configuration

Create `.env` file:
```bash
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini  # Optional (this is the default)
DEFAULT_SCHEMA=chatml                # Optional (this is the default)
HF_TOKEN=your_huggingface_token      # For publishing
```


## 📖 Documentation

- [Detailed Usage Guide](docs/DETAILED_USAGE.md) - Complete CLI reference
- [Examples](docs/EXAMPLES.md) - Code examples and recipes
- [API Documentation](docs/API.md) - Python API reference
- [Publishing Guide](docs/PUBLISHING.md) - PyPI publishing instructions
- [All Documentation](docs/README.md) - Complete documentation index

## 🛠️ Development

```bash
# Clone repository
git clone https://github.com/zysec/data4ai.git
cd data4ai

# Install for development
pip install -e ".[dev]"

# Run tests
pytest

# Check code quality
ruff check .
black --check .
```

## 🤝 Contributing

Contributions welcome! Please check our [Contributing Guide](CONTRIBUTING.md).

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🔗 Links

- [PyPI Package](https://pypi.org/project/data4ai/)
- [GitHub Repository](https://github.com/zysec/data4ai)
- [Documentation](https://github.com/zysec/data4ai/tree/main/docs)
- [Issue Tracker](https://github.com/zysec/data4ai/issues)

---

**Made with ❤️ by [ZySec AI](https://zysec.ai)**