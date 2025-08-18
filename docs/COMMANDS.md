# 📋 Data4AI Command Reference

Complete reference for all available CLI commands.

## 🎯 Main Commands

### `data4ai prompt`
Generate dataset from natural language description using AI.

```bash
data4ai prompt --repo <name> --dataset <schema> --description "<text>" [options]

# Examples
data4ai prompt --repo my-dataset --dataset alpaca --description "Create programming questions"
data4ai prompt --repo customer-support --dataset chatml --description "Customer support conversations" --count 200
data4ai prompt --repo legal-data --dataset alpaca --description "Legal Q&A" --model "anthropic/claude-3-5-sonnet"
```

### `data4ai doc`
Generate dataset from document(s) - supports files and folders.

```bash
data4ai doc <path> --repo <name> [options]

# Examples
data4ai doc my_document.txt --repo doc-dataset --count 100
data4ai doc ./documents/ --repo multi-doc-dataset --count 500
data4ai doc research.pdf --repo research-qa --dataset chatml --count 200
```

### `data4ai push`
Upload dataset to HuggingFace Hub.

```bash
data4ai push --repo <name> [--private]

# Examples
data4ai push --repo my-dataset
data4ai push --repo my-dataset --private
```

## ⚙️ Common Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--repo <name>` | Output directory and HF repo name | Required | `--repo my-dataset` |
| `--dataset <schema>` | Dataset schema (alpaca, chatml) | `alpaca` | `--dataset chatml` |
| `--model <model>` | OpenRouter model to use | `openai/gpt-4o-mini` | `--model anthropic/claude-3-5-sonnet` |
| `--count <N>` | Number of examples to generate | `500` | `--count 200` |
| `--temperature <F>` | Sampling temperature (0.0-2.0) | `0.7` | `--temperature 0.8` |
| `--batch-size <N>` | Examples per API call | `10` | `--batch-size 5` |
| `--taxonomy <level>` | Bloom's taxonomy level | `balanced` | `--taxonomy advanced` |
| `--verbose` | Show detailed output | `false` | `--verbose` |
| `--dry-run` | Show what would be generated | `false` | `--dry-run` |
| `--no-use-dspy` | Disable DSPy optimization | `false` | `--no-use-dspy` |

## 🚀 Quick Examples

### Generate Your First Dataset
```bash
# Set API key
export OPENROUTER_API_KEY="your_key_here"

# Generate 10 examples
data4ai prompt --repo my-first-dataset --description "Create 10 programming questions" --count 10
```

### Document-based Generation
```bash
# Generate from a single document
data4ai doc research_paper.pdf --repo research-qa --count 100

# Generate from multiple documents
data4ai doc ./documents/ --repo knowledge-base --count 500 --taxonomy advanced
```

### Publish to Hugging Face
```bash
# Set HF token
export HF_TOKEN="your_hf_token"

# Generate and publish
data4ai prompt --repo public-dataset --description "Educational content" --count 100
data4ai push --repo public-dataset

# Or make it private
data4ai push --repo public-dataset --private
```

## 📊 Dataset Schemas

### Alpaca Schema (Default)
```json
{
  "instruction": "What is Python?",
  "input": "Explain in simple terms",
  "output": "Python is a programming language..."
}
```

### ChatML Schema (Conversations)
```json
{
  "messages": [
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language..."}
  ]
}
```

## 🎯 Taxonomy Levels

Use `--taxonomy` to control cognitive complexity:

- `basic` - Focus on Remember & Understand (beginner-friendly)
- `balanced` - All Bloom's levels (default)
- `advanced` - Focus on Analyze, Evaluate & Create (challenging)
- `none` - No specific taxonomy requirements

```bash
# Beginner-friendly questions
data4ai prompt --repo basics --description "Math concepts" --taxonomy basic

# Advanced analysis tasks
data4ai prompt --repo advanced --description "Research analysis" --taxonomy advanced
```

## 🔍 Help Commands

```bash
# General help
data4ai --help

# Command-specific help
data4ai prompt --help
data4ai doc --help
data4ai push --help
```

## 🚨 Troubleshooting

### Common Issues

**"Command not found"**
```bash
# Check if data4ai is installed
data4ai --version

# Install with uv
uv add data4ai

# Or with pip
pip install data4ai
```

**"OpenRouter API key not found"**
```bash
export OPENROUTER_API_KEY="your_key_here"
```

**"Model not available"**
```bash
# Use default model
data4ai prompt --repo test --description "test"

# Or specify a different model
data4ai prompt --repo test --description "test" --model "openai/gpt-4o-mini"
```

---

**For more examples, see [GETTING_STARTED.md](../GETTING_STARTED.md)**