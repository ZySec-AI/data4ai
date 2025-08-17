# 📋 Data4AI Command Reference

Complete reference for all available CLI commands.

## 🎯 Main Commands

### `data4ai create-sample`
Create a template file for the specified schema.

```bash
data4ai create-sample <path.xlsx> [--dataset <schema>]

# Examples
data4ai create-sample my_data.xlsx --dataset alpaca
data4ai create-sample legal_data.xlsx --dataset dolly
data4ai create-sample chat_data.xlsx --dataset sharegpt
```

### `data4ai file-to-dataset`
Convert filled Excel/CSV file to dataset without AI completion.

```bash
data4ai file-to-dataset <path.xlsx> --repo <name> [--dataset <schema>]

# Examples
data4ai file-to-dataset my_data.xlsx --repo my-dataset
data4ai file-to-dataset complete_data.xlsx --repo legal-dataset --dataset dolly
```

### `data4ai excel-to-dataset` (Deprecated)
Convert filled Excel file to dataset without AI completion (deprecated, use file-to-dataset).

```bash
data4ai excel-to-dataset <path.xlsx> --repo <name> [--dataset <schema>]
```

### `data4ai run`
Process Excel/CSV file with AI completion for partial rows.

```bash
data4ai run <path.xlsx> --repo <name> [options]

# Examples
data4ai run my_data.xlsx --repo my-dataset
data4ai run partial_data.xlsx --repo my-dataset --max-rows 100 --temperature 0.7
data4ai run data.xlsx --repo my-dataset --model "anthropic/claude-3-5-sonnet"
```

### `data4ai prompt`
Generate dataset from natural language description.

```bash
data4ai prompt --repo <name> --dataset <schema> --description "<text>" [options]

# Examples
data4ai prompt --repo my-dataset --dataset alpaca --description "Create programming questions"
data4ai prompt --repo customer-support --dataset alpaca --description "Customer support Q&A" --count 200
data4ai prompt --repo legal-data --dataset dolly --description "Legal summaries" --model "anthropic/claude-3-5-sonnet"
```

### `data4ai push`
Upload dataset to HuggingFace Hub.

```bash
data4ai push --repo <name> [--private]

# Examples
data4ai push --repo my-dataset
data4ai push --repo my-dataset --private
```

## 🔧 Utility Commands

### `data4ai validate`
Validate dataset quality and schema compliance.

```bash
data4ai validate --repo <name>

# Examples
data4ai validate --repo my-dataset
```

### `data4ai stats`
Display dataset statistics and metrics.

```bash
data4ai stats --repo <name>

# Examples
data4ai stats --repo my-dataset
```

### `data4ai list-models`
Show available OpenRouter models.

```bash
data4ai list-models

# Examples
data4ai list-models
```

### `data4ai config`
Display or save current configuration.

```bash
data4ai config

# Examples
data4ai config
```

### `data4ai version`
Show Data4AI version.

```bash
data4ai version

# Examples
data4ai version
```

## ⚙️ Common Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--repo <name>` | Output directory and HF repo name | Required | `--repo my-dataset` |
| `--dataset <schema>` | Dataset schema (alpaca, dolly, sharegpt) | `alpaca` | `--dataset dolly` |
| `--model <model>` | OpenRouter model to use | From env var | `--model anthropic/claude-3-5-sonnet` |
| `--max-rows <N>` | Maximum rows to generate | `1000` | `--max-rows 500` |
| `--count <N>` | Number of rows (prompt mode) | `500` | `--count 200` |
| `--temperature <F>` | Sampling temperature (0.0-2.0) | `0.7` | `--temperature 0.8` |
| `--seed <N>` | Random seed for reproducibility | Random | `--seed 42` |
| `--huggingface` | Push to Hugging Face after generation | `false` | `--huggingface` |
| `--private` | Make HF dataset private | `false` | `--private` |
| `--verbose` | Show detailed output | `false` | `--verbose` |
| `--dry-run` | Show what would be generated | `false` | `--dry-run` |

## 🚀 Quick Examples

### Generate Your First Dataset
```bash
# Set API key
export OPENROUTER_API_KEY="your_key_here"

# Generate 10 examples
data4ai prompt --repo my-first-dataset --description "Create 10 programming questions" --count 10
```

### Excel Template Workflow
```bash
# Create template
data4ai create-sample my_data.xlsx --dataset alpaca

# Edit in Excel, then generate
data4ai run my_data.xlsx --repo my-dataset --max-rows 100
```

### Convert Complete Excel File
```bash
# Convert without AI (for complete files)
data4ai file-to-dataset my_data.xlsx --repo my-dataset
```

### Publish to Hugging Face
```bash
# Generate and publish
data4ai prompt --repo public-dataset --description "Educational content" --count 100 --huggingface

# Or publish existing dataset
data4ai push --repo my-dataset --private
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

### Dolly Schema
```json
{
  "instruction": "Summarize this text",
  "context": "Long text to summarize...",
  "response": "Summary of the text..."
}
```

### ShareGPT Schema (Chat)
```json
{
  "conversations": [
    {"from": "human", "value": "Hello!"},
    {"from": "gpt", "value": "Hi there!"}
  ]
}
```

## 🔍 Help Commands

```bash
# General help
data4ai --help

# Command-specific help
data4ai create-sample --help
data4ai run --help
data4ai prompt --help
data4ai push --help
data4ai validate --help
data4ai stats --help
data4ai list-models --help
data4ai config --help
```

## 🚨 Troubleshooting

### Common Issues

**"Command not found"**
```bash
# Check if data4ai is installed
data4ai --version

# Reinstall if needed
pip install data4ai
```

**"OpenRouter API key not found"**
```bash
export OPENROUTER_API_KEY="your_key_here"
```

**"Model not available"**
```bash
# Check available models
data4ai list-models

# Use a different model
data4ai prompt --repo test --description "test" --model "meta-llama/llama-3-8b-instruct"
```

**"Excel file not found"**
```bash
# Create template first
data4ai create-sample my_data.xlsx --dataset alpaca
```

---

**For more examples, see [GETTING_STARTED.md](GETTING_STARTED.md)**
