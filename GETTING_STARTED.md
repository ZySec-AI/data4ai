# 🚀 Getting Started with Data4AI

Quick start guide with copy-paste ready examples.

## 📦 Installation

```bash
# Install Data4AI (choose based on your needs)
pip install data4ai              # Core features only
pip install data4ai[excel]       # With Excel support
pip install data4ai[hf]          # With HuggingFace publishing  
pip install data4ai[all]         # All features (recommended)

# Or with pipx for CLI isolation
pipx install data4ai[all]
```

## ⚙️ Environment Setup

### 🎯 Method 1: Quick Setup (Recommended for Testing)

```bash
# Set API key for current terminal session
export OPENROUTER_API_KEY="your_key_here"

# Get your API key from: https://openrouter.ai/keys

# Verify setup
data4ai env --check
```

### 🔧 Method 2: Interactive Setup

```bash
# Run the interactive setup script
source setup_env.sh

# This will prompt you for:
# - OpenRouter API key (required)
# - Model selection (optional)
# - HuggingFace token (optional)
```

### 💾 Method 3: Permanent Setup

```bash
# For Bash (Linux/WSL)
echo 'export OPENROUTER_API_KEY="your_key_here"' >> ~/.bashrc
source ~/.bashrc

# For Zsh (macOS/Linux)
echo 'export OPENROUTER_API_KEY="your_key_here"' >> ~/.zshrc
source ~/.zshrc

# Verify it's permanent
data4ai env --check
```

### 🆘 Troubleshooting Environment Issues

```bash
# Check what's missing
data4ai env --check

# Show export commands
data4ai env --export

# Test if API key is working
data4ai prompt --repo test --description "test" --count 1 --dry-run
```

## 🎯 Quick Examples (Copy-Paste Ready)

### Example 1: Generate Your First Dataset

```bash
# Generate 10 programming questions
data4ai prompt \
  --repo my-first-dataset \
  --description "Create 10 programming interview questions" \
  --count 10

# Check the results (saved to outputs/ by default)
ls outputs/my-first-dataset/
cat outputs/my-first-dataset/data.jsonl | head -3
```

### Example 2: Create Excel Template

```bash
# Create Excel template
data4ai create-sample my_data.xlsx --dataset alpaca

# Open my_data.xlsx in Excel/LibreOffice/Numbers
# Add a few examples, leave some rows blank

# Generate complete dataset
data4ai run my_data.xlsx --repo my-excel-dataset --max-rows 50
```

### Example 3: Customer Support Dataset

```bash
# Generate customer support Q&A
data4ai prompt \
  --repo customer-support \
  --description "Create customer support questions and answers for a SaaS product" \
  --count 100 \
  --temperature 0.6
```

### Example 4: Code Review Examples

```bash
# Generate code review dataset
data4ai prompt \
  --repo code-reviews \
  --description "Create code review examples that help developers improve code quality" \
  --count 75 \
  --model "anthropic/claude-3-5-sonnet"
```

### Example 5: Publish to Hugging Face

```bash
# Generate and publish in one command
data4ai prompt \
  --repo my-public-dataset \
  --description "Create 50 educational programming examples" \
  --count 50 \
  --huggingface

# Or publish existing dataset
data4ai push --repo my-public-dataset --private
```

## 🐍 Python Examples

### Quick Python Example

```python
# Note: Requires pip install data4ai[all] for full features

import os
from data4ai import DatasetGenerator

# Set API key
os.environ["OPENROUTER_API_KEY"] = "your_key_here"

# Generate dataset
generator = DatasetGenerator()
# Use generator.generate_from_prompt_sync() or other methods

print("✅ Ready to generate datasets!")
```

### Excel Template in Python

```python
# Note: Requires pip install data4ai[excel] for Excel support

from data4ai.excel_handler import ExcelHandler
from data4ai import DatasetGenerator

# Create template
ExcelHandler.create_template("my_data.xlsx", "alpaca")

# After editing the Excel file, generate dataset
generator = DatasetGenerator()
# Use generator methods to process the Excel file

print("✅ Template created and ready for processing!")
```

## 🔧 Common Commands

```bash
# Get help
data4ai --help
data4ai prompt --help

# List available models
data4ai list-models

# Validate your dataset
data4ai validate --repo my-dataset

# Get dataset statistics
data4ai stats --repo my-dataset

# Check configuration
data4ai config

# Show version
data4ai version

# Convert file without AI
data4ai file-to-dataset my_data.xlsx --repo my-dataset
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

## 🎛️ Configuration Options

### Environment Variables
```bash
export OPENROUTER_API_KEY="your_key"
export OPENROUTER_MODEL="openai/gpt-4o-mini"  # This is now the default
export DATA4AI_TEMPERATURE="0.7"
export HF_TOKEN="your_hf_token"
export HF_ORG="ZySecAI"
```

### Command Line Options
```bash
# Basic options
--repo my-dataset          # Output directory name
--count 100               # Number of rows to generate
--temperature 0.8         # Creativity level (0.0-2.0)
--model "anthropic/claude-3-5-sonnet"  # Specific model

# Advanced options
--seed 42                 # Reproducible results
--dry-run                 # Preview without saving
--huggingface             # Push to HF after generation
--private                 # Make HF dataset private
--verbose                 # Detailed output
```

## 🚨 Troubleshooting

### Common Issues

**"OpenRouter API key not found"**
```bash
export OPENROUTER_API_KEY="your_key_here"
```

**"Model not available"**
```bash
# Check available models
data4ai list-models

# Use a different model
data4ai prompt --repo test --description "test" --model "openai/gpt-4o-mini"
```

**"Excel file not found"**
```bash
# Create template first
data4ai create-sample my_data.xlsx --dataset alpaca
```

## 📈 Next Steps

1. **Start Small**: Use `--count 10` to test quality
2. **Be Specific**: Detailed descriptions produce better results
3. **Use Seeds**: `--seed 42` for reproducible results
4. **Monitor Costs**: Check OpenRouter usage dashboard
5. **Validate**: Use `data4ai validate` to check quality

## 🆘 Need Help?

- **Documentation**: [README.md](README.md)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/zysec/data4ai/issues)

---

**Happy dataset generation! 🎉**
