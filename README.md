# Data4AI 🚀

> **AI-powered dataset generation for instruction tuning and model fine-tuning**

[![PyPI version](https://badge.fury.io/py/data4ai.svg)](https://pypi.org/project/data4ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Generate high-quality synthetic datasets using state-of-the-art language models through OpenRouter API. Perfect for creating training data for LLM fine-tuning.

## ✨ Key Features

- 🤖 **100+ AI Models** - Access to GPT-4, Claude, Llama, and more via OpenRouter
- 📊 **Multiple Formats** - Support for Alpaca, Dolly, ShareGPT schemas
- 🔮 **DSPy Integration** - Dynamic prompt optimization for better quality
- 💾 **Excel/CSV Support** - Start from templates or existing data
- ☁️ **HuggingFace Hub** - Direct dataset publishing
- ⚡ **Production Ready** - Rate limiting, checkpointing, deduplication

## 🚀 Quick Start

### Installation

```bash
pip install data4ai              # Core features
pip install data4ai[excel]       # With Excel support
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

# Optional: For publishing to HuggingFace
export HF_TOKEN="your_huggingface_token"
```

#### Option 2: Interactive Setup
```bash
# Use our setup helper
source setup_env.sh
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
data4ai env --check
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

### 2. Complete Partial Data from Excel

```bash
# Create template
data4ai create-sample template.xlsx

# Fill some examples in Excel, leave others blank
# Then generate completions
data4ai run template.xlsx --repo my-dataset --max-rows 100
```

### 3. Publish to HuggingFace

```bash
# Generate and publish
data4ai prompt \
  --repo my-public-dataset \
  --description "Educational content about machine learning" \
  --count 200 \
  --huggingface
```

## 🐍 Python API

```python
from data4ai import generate_from_description

result = generate_from_description(
    description="Create Python interview questions",
    repo="python-interviews",
    count=50
)

print(f"Generated {result.row_count} examples")
```

## 📋 Supported Schemas

**Alpaca** (Default - Instruction tuning)
```json
{
  "instruction": "What is machine learning?",
  "input": "Explain in simple terms",
  "output": "Machine learning is..."
}
```

**Dolly** (Context-based)
```json
{
  "instruction": "Summarize this text",
  "context": "Long text here...",
  "response": "Summary..."
}
```

**ShareGPT** (Conversations)
```json
{
  "conversations": [
    {"from": "human", "value": "Hello"},
    {"from": "gpt", "value": "Hi there!"}
  ]
}
```

## ⚙️ Configuration

Create `.env` file:
```bash
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini  # Optional (this is the default)
HF_TOKEN=your_huggingface_token                   # For publishing
```

Or use CLI:
```bash
data4ai config --save
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