# 📚 Detailed Usage Guide

## 🚀 Quick Start Examples

### Basic Dataset Generation
```bash
# Generate your first dataset
data4ai prompt \
  --repo my-first-dataset \
  --dataset alpaca \
  --description "Create 10 Python programming questions for beginners" \
  --count 10
```

### Document-based Generation
```bash
# Generate from a single document
data4ai doc research_paper.pdf \
  --repo research-qa \
  --dataset chatml \
  --count 100 \
  --taxonomy advanced

# Generate from multiple documents
data4ai doc ./documents/ \
  --repo knowledge-base \
  --dataset alpaca \
  --count 500 \
  --taxonomy balanced
```

## 💼 Real-World Examples

### Customer Support Dataset
```bash
# Generate customer support Q&A
data4ai prompt \
  --repo customer-support-qa \
  --dataset alpaca \
  --description "Create customer support questions and answers for a SaaS product. Include common issues like login problems, billing questions, and feature requests." \
  --count 200 \
  --temperature 0.6
```

### Code Review Examples
```bash
# Generate code review dataset
data4ai prompt \
  --repo code-review-dataset \
  --dataset alpaca \
  --description "Create code review examples that help developers improve code quality. Include security issues, performance problems, and best practices." \
  --count 150 \
  --model "anthropic/claude-3-5-sonnet"
```

### Financial Education Dataset
```bash
# Generate financial education content
data4ai prompt \
  --repo financial-education \
  --dataset alpaca \
  --description "Create educational content about personal finance. Cover topics like budgeting, investing, saving, and debt management." \
  --count 300 \
  --temperature 0.8 \
  --taxonomy balanced
```

### Multi-language Support
```bash
# Generate Spanish language dataset
data4ai prompt \
  --repo spanish-tech-qa \
  --dataset alpaca \
  --description "Crear preguntas y respuestas en español sobre tecnología, programación y desarrollo de software" \
  --count 100 \
  --model "openai/gpt-4o-mini"
```

## 🎯 Advanced Taxonomy Examples

### Beginner-Friendly Content
```bash
# Focus on Remember & Understand levels
data4ai prompt \
  --repo programming-basics \
  --dataset alpaca \
  --description "Basic programming concepts for complete beginners" \
  --count 100 \
  --taxonomy basic \
  --temperature 0.5
```

### Advanced Critical Thinking
```bash
# Focus on Analyze, Evaluate & Create levels
data4ai prompt \
  --repo research-methodology \
  --dataset chatml \
  --description "Advanced research methodology and analysis techniques" \
  --count 150 \
  --taxonomy advanced \
  --model "anthropic/claude-3-5-sonnet"
```

### Balanced Distribution
```bash
# All cognitive levels (default)
data4ai prompt \
  --repo comprehensive-training \
  --dataset alpaca \
  --description "Complete programming curriculum covering all skill levels" \
  --count 500 \
  --taxonomy balanced
```

## 🔧 Advanced Configuration

### Chat-style Conversations
```bash
# Generate conversation dataset with ChatML format
data4ai prompt \
  --repo ai-chat-examples \
  --dataset chatml \
  --description "Create conversations between users and AI assistants about various technical topics" \
  --count 200 \
  --temperature 0.8
```

### Reproducible Generation
```bash
# Generate with specific seed for reproducibility
data4ai prompt \
  --repo reproducible-dataset \
  --dataset alpaca \
  --description "Create math word problems for middle school students" \
  --count 100 \
  --seed 42 \
  --temperature 0.5
```

### High-Volume Generation
```bash
# Generate large datasets efficiently
data4ai prompt \
  --repo large-dataset \
  --dataset alpaca \
  --description "Comprehensive programming tutorials and exercises" \
  --count 2000 \
  --batch-size 5 \
  --temperature 0.7
```

### Preview Generation
```bash
# Test generation without saving
data4ai prompt \
  --repo test-preview \
  --dataset alpaca \
  --description "Create 5 cooking recipe instructions" \
  --count 5 \
  --dry-run
```

## 📄 Document Processing Examples

### Single Document Analysis
```bash
# Generate Q&A from research paper
data4ai doc research_paper.pdf \
  --repo research-qa \
  --dataset chatml \
  --count 150 \
  --taxonomy advanced \
  --model "anthropic/claude-3-5-sonnet"
```

### Folder Processing
```bash
# Process entire documentation folder
data4ai doc ./technical-docs/ \
  --repo tech-knowledge \
  --dataset alpaca \
  --count 1000 \
  --taxonomy balanced \
  --batch-size 10
```

### Mixed Document Types
```bash
# Process various document formats
data4ai doc ./mixed-documents/ \
  --repo comprehensive-qa \
  --dataset chatml \
  --count 500 \
  --taxonomy advanced
```

## 📈 Publishing to HuggingFace

### Generate and Publish
```bash
# Set environment variables
export HF_TOKEN="your_hf_token"

# Generate dataset
data4ai prompt \
  --repo my-public-dataset \
  --dataset alpaca \
  --description "Create 100 programming interview questions" \
  --count 100

# Publish to HuggingFace
data4ai push --repo my-public-dataset
```

### Private Datasets
```bash
# Create and publish private dataset
data4ai prompt \
  --repo internal-training \
  --dataset alpaca \
  --description "Internal company training materials" \
  --count 200

data4ai push --repo internal-training --private
```

## 🔧 Quality Control

### DSPy Optimization
```bash
# Use DSPy for optimized prompts (default)
data4ai prompt \
  --repo optimized-dataset \
  --dataset alpaca \
  --description "Complex reasoning tasks" \
  --count 100

# Disable DSPy for faster generation
data4ai prompt \
  --repo simple-dataset \
  --dataset alpaca \
  --description "Basic Q&A" \
  --count 100 \
  --no-use-dspy
```

### Model Selection for Quality
```bash
# High-quality creative content
data4ai prompt \
  --repo creative-writing \
  --dataset alpaca \
  --description "Creative writing prompts and stories" \
  --count 100 \
  --model "anthropic/claude-3-5-sonnet" \
  --temperature 0.9

# Factual, consistent content
data4ai prompt \
  --repo factual-qa \
  --dataset alpaca \
  --description "Factual questions about science" \
  --count 200 \
  --model "openai/gpt-4o-mini" \
  --temperature 0.3
```

## 🔧 CLI Reference

### Available Commands

```bash
# Get help
data4ai --help
data4ai <command> --help

# Generate from description
data4ai prompt --repo my-dataset --description "Your description here"

# Generate from documents
data4ai doc ./documents/ --repo doc-dataset

# Push to HuggingFace
data4ai push --repo my-dataset --private
```

### Common Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--repo <name>` | Output directory and HF repo name | Required | `--repo my-dataset` |
| `--dataset <schema>` | Dataset schema (alpaca, chatml) | `alpaca` | `--dataset chatml` |
| `--model <model>` | OpenRouter model to use | `openai/gpt-4o-mini` | `--model anthropic/claude-3-5-sonnet` |
| `--count <N>` | Number of examples to generate | `500` | `--count 200` |
| `--temperature <F>` | Sampling temperature (0.0-2.0) | `0.7` | `--temperature 0.8` |
| `--taxonomy <level>` | Bloom's taxonomy level | `balanced` | `--taxonomy advanced` |
| `--batch-size <N>` | Examples per API call | `10` | `--batch-size 5` |
| `--seed <N>` | Random seed for reproducibility | Random | `--seed 42` |
| `--no-use-dspy` | Disable DSPy optimization | `false` | `--no-use-dspy` |
| `--verbose` | Show detailed output | `false` | `--verbose` |
| `--dry-run` | Show what would be generated | `false` | `--dry-run` |

## 📦 Output Structure

```
my-dataset/
├── data.jsonl          # Main dataset file (compatible with unsloth)
├── metadata.json       # Generation metadata and parameters
└── README.md           # Auto-generated dataset documentation
```

### Metadata Example
```json
{
  "version": "0.2.0",
  "schema": "alpaca",
  "model": "openai/gpt-4o-mini",
  "row_count": 1000,
  "generated_at": "2024-01-15T10:30:00Z",
  "parameters": {
    "temperature": 0.7,
    "count": 1000,
    "taxonomy": "balanced",
    "batch_size": 10
  },
  "metrics": {
    "avg_instruction_length": 45,
    "avg_output_length": 120,
    "completion_rate": 0.98,
    "total_rows": 1000,
    "empty_rows": 20
  }
}
```

## 🎨 Schema Examples

### Alpaca Format Output
```json
{
  "instruction": "Write a Python function to reverse a string",
  "input": "def reverse_string(s):",
  "output": "def reverse_string(s):\n    return s[::-1]"
}
```

### ChatML Format Output
```json
{
  "messages": [
    {"role": "user", "content": "How do I reverse a string in Python?"},
    {"role": "assistant", "content": "You can reverse a string in Python using slicing: s[::-1]"}
  ]
}
```

---

**For more examples, see [EXAMPLES.md](EXAMPLES.md) and [COMMANDS.md](COMMANDS.md)**
