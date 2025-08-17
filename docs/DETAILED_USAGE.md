# 📚 Detailed Usage Guide

## 📊 Excel Template Workflow

```bash
# 1. Create an Excel template
data4ai create-sample my_data.xlsx --dataset alpaca

# 2. Open and edit the Excel file (add a few examples)
# Open my_data.xlsx in Excel/LibreOffice/Numbers
# Fill in some rows, leave others blank for AI to complete

# 3. Generate the complete dataset
data4ai run my_data.xlsx \
  --repo my-excel-dataset \
  --max-rows 100 \
  --temperature 0.7
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
  --temperature 0.8
```

### Multi-language Support
```bash
# Generate Spanish language dataset
data4ai prompt \
  --repo spanish-tech-qa \
  --dataset alpaca \
  --description "Crear preguntas y respuestas en español sobre tecnología, programación y desarrollo de software" \
  --count 100 \
  --model "meta-llama/llama-3-8b-instruct"
```

## 🔧 Advanced Examples

### Custom Schema with Dolly
```bash
# Generate dataset using Dolly schema
data4ai prompt \
  --repo legal-summarizer \
  --dataset dolly \
  --description "Summarize legal case briefs into concise bullet points for junior lawyers" \
  --count 100 \
  --model "anthropic/claude-3-5-sonnet"
```

### Chat-style Dataset
```bash
# Generate conversation dataset
data4ai prompt \
  --repo ai-chat-examples \
  --dataset sharegpt \
  --description "Create conversations between users and AI assistants about various topics" \
  --count 50
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

## 📈 Publishing to Hugging Face

```bash
# Generate and publish in one command
data4ai prompt \
  --repo my-public-dataset \
  --dataset alpaca \
  --description "Create 50 programming interview questions" \
  --count 50 \
  --huggingface

# Or publish existing dataset
data4ai push --repo my-public-dataset --private
```

## 🧪 Testing and Validation

```bash
# Validate your dataset
data4ai validate --repo my-dataset

# Check dataset statistics
data4ai stats --repo my-dataset

# List available models
data4ai list-models

# Check your configuration
data4ai config

# Show version
data4ai version
```

## 🔧 CLI Reference

### Main Commands

```bash
# Get help
data4ai --help
data4ai <command> --help

# Create Excel template
data4ai create-sample my_data.xlsx --dataset alpaca

# Generate from Excel file (with AI completion)
data4ai run my_data.xlsx --repo my-dataset

# Convert file to dataset (without AI)
data4ai file-to-dataset my_data.xlsx --repo my-dataset

# Generate from description
data4ai prompt --repo my-dataset --description "Your description here"

# Push to Hugging Face
data4ai push --repo my-dataset --private
```

### Common Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--repo <name>` | Output directory and HF repo name | Required | `--repo my-dataset` |
| `--dataset <schema>` | Dataset schema (alpaca, dolly, sharegpt) | `alpaca` | `--dataset dolly` |
| `--model <model>` | OpenRouter model to use | From env var | `--model anthropic/claude-3-5-sonnet` |
| `--max-rows <N>` | Maximum rows to generate | `1000` | `--max-rows 500` |
| `--count <N>` | Number of rows (prompt mode) | `500` | `--count 200` |
| `--temperature <F>` | Sampling temperature (0.0-2.0) | `0.7` | `--temperature 0.8` |
| `--seed <N>` | Random seed for reproducibility | Random | `--seed 42` |
| `--use-dspy` | Use DSPy for dynamic prompt generation | `true` | `--use-dspy` |
| `--no-use-dspy` | Disable DSPy (use static prompts) | `false` | `--no-use-dspy` |
| `--huggingface` | Push to Hugging Face after generation | `false` | `--huggingface` |
| `--private` | Make HF dataset private | `false` | `--private` |
| `--verbose` | Show detailed output | `false` | `--verbose` |
| `--dry-run` | Show what would be generated | `false` | `--dry-run` |

## 📦 Output Structure

```
my-dataset/
├── data.jsonl          # Main dataset file (unsloth compatible)
├── meta.json           # Generation metadata and parameters
├── sample.xlsx         # Original Excel template (if used)
├── validation.json     # Data quality metrics
└── README.md           # Auto-generated dataset documentation
```

### Metadata Example
```json
{
  "schema": "alpaca",
  "model": "meta-llama/llama-3-8b-instruct",
  "row_count": 1000,
  "generated_at": "2024-01-15T10:30:00Z",
  "parameters": {
    "temperature": 0.7,
    "max_rows": 1000,
    "seed": 42
  },
  "quality_metrics": {
    "avg_instruction_length": 45,
    "avg_output_length": 120,
    "completion_rate": 0.98
  }
}
```