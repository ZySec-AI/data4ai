# Data4AI 🚀

> **AI-powered dataset generation for instruction tuning and model fine-tuning**

Data4AI is a production-ready Python library and CLI tool that creates high-quality synthetic datasets using state-of-the-art language models through OpenRouter API. Generate, validate, and publish datasets in popular formats like Alpaca, Dolly, and ShareGPT.

[![PyPI version](https://badge.fury.io/py/data4ai.svg)](https://badge.fury.io/py/data4ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Quick Navigation

- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [📚 Usage Examples](#-usage-examples)
- [🔧 CLI Reference](#-cli-reference)
- [🐍 Python API](#-python-api)
- [📋 Supported Schemas](#-supported-schemas)
- [❓ FAQ & Troubleshooting](#-faq--troubleshooting)
- [🤝 Contributing](#-contributing)

## ✨ Features

### Core Capabilities
- **🤖 AI-Powered Generation**: Access 100+ models via OpenRouter API
- **🔮 DSPy Integration**: Dynamic prompt generation using DSPy signatures for high-quality output
- **📊 Multiple Input Formats**: Excel and CSV file support with auto-detection
- **💬 Natural Language Input**: Generate datasets from text descriptions
- **🔧 Schema Support**: Alpaca, Dolly, ShareGPT, and custom formats
- **☁️ HuggingFace Hub**: Direct dataset publishing integration

### Production Features  
- **⚡ Rate Limiting**: Adaptive token bucket algorithm with automatic backoff
- **💾 Atomic Operations**: Data integrity with temp file + atomic rename pattern
- **🔄 Checkpoint/Resume**: Fault-tolerant generation with session recovery
- **🎯 Deduplication**: Multiple strategies (exact, fuzzy, content-based)
- **📈 Progress Tracking**: Real-time metrics, progress bars, and ETA
- **🛡️ Error Handling**: Comprehensive error recovery with user-friendly messages
- **🚀 Performance**: Parallel processing with asyncio and streaming I/O
- **📦 Batch Processing**: Configurable batch sizes with memory optimization

## 🚀 Quick Start

### Method 1: DSPy Dynamic Prompt Generation (New!)

```bash
# Generate high-quality datasets using DSPy signatures
data4ai prompt \
  --repo dspy-example \
  --dataset alpaca \
  --description "Create programming questions about data structures" \
  --count 20 \
  --use-dspy  # Enable DSPy for dynamic prompts

# Compare with static prompts
data4ai prompt \
  --repo static-example \
  --dataset alpaca \
  --description "Create programming questions about data structures" \
  --count 20 \
  --no-use-dspy  # Use static prompts
```

### Method 2: Excel Template Workflow (Recommended)

```bash
# 1. Create an Excel template
data4ai create-sample my_dataset.xlsx --dataset alpaca

# 2. Edit the Excel file (add some examples, leave blanks for AI to fill)
# Open my_dataset.xlsx in Excel/LibreOffice/Numbers

# 3. Generate the complete dataset
data4ai run my_dataset.xlsx --repo my-dataset --dataset alpaca --max-rows 1000
```

### Method 2: Description-to-Dataset

```bash
# Generate dataset from a description
data4ai prompt \
  --repo code-review-assistant \
  --dataset alpaca \
  --description "Create code review examples that help developers improve their code quality" \
  --count 500
```

### Method 3: Push to Hugging Face

```bash
# Generate and publish in one command
data4ai run my_dataset.xlsx --repo my-dataset --dataset alpaca --huggingface --private
```

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- OpenRouter API key ([Get one here](https://openrouter.ai/))

### Install Data4AI

```bash
# Recommended: Install with pipx for CLI isolation
pipx install data4ai

# Install with pip (choose your features)
pip install data4ai              # Core features only
pip install data4ai[excel]       # With Excel support
pip install data4ai[hf]          # With HuggingFace publishing
pip install data4ai[all]         # All features

# For development
git clone https://github.com/zysec/data4ai.git
cd data4ai
pip install -e .
```

### Verify Installation

```bash
data4ai --version
data4ai --help
```

### 🧪 Local Development & Testing

For developers who want to test and modify the code:

```bash
# Quick setup for local testing
cd data4ai
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your OpenRouter API key

# Test the installation
data4ai --help
data4ai create-sample tests/samples/test.xlsx  # Works without API

# Run tests
pytest

# Run comprehensive tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=data4ai --cov-report=html
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Required
export OPENROUTER_API_KEY="your_openrouter_key_here"

# Optional (with defaults)
export OPENROUTER_MODEL="meta-llama/llama-3-8b-instruct"  # Default model
export DATA4AI_DATASET="alpaca"                           # Default schema
export HF_TOKEN="your_huggingface_token"                  # For HF publishing
export HF_ORG="ZySecAI"                                   # HF organization
export DATA4AI_TEMPERATURE="0.7"                          # Default temperature
export DATA4AI_MAX_ROWS="1000"                            # Default max rows
```

### Configuration File

Create `~/.data4ai/config.yaml` for persistent settings:

```yaml
openrouter:
  api_key: "your_key_here"
  model: "meta-llama/llama-3-8b-instruct"
  temperature: 0.7

huggingface:
  token: "your_hf_token"
  org: "ZySecAI"

defaults:
  dataset: "alpaca"
  max_rows: 1000
  seed: 42
```

## 📚 Usage Examples

### 🚀 Quick Start (Copy-Paste Ready)

```bash
# 1. Set your API key
export OPENROUTER_API_KEY="your_key_here"

# 2. Generate a simple dataset from description
data4ai prompt \
  --repo my-first-dataset \
  --dataset alpaca \
  --description "Create 10 questions and answers about Python programming" \
  --count 10

# 3. Check the results
ls my-first-dataset/
cat my-first-dataset/data.jsonl | head -3
```

### 📊 Excel Template Workflow

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

### 💼 Real-World Examples

#### Example 1: Customer Support Dataset
```bash
# Generate customer support Q&A
data4ai prompt \
  --repo customer-support-qa \
  --dataset alpaca \
  --description "Create customer support questions and answers for a SaaS product. Include common issues like login problems, billing questions, and feature requests." \
  --count 200 \
  --temperature 0.6
```

#### Example 2: Code Review Examples
```bash
# Generate code review dataset
data4ai prompt \
  --repo code-review-dataset \
  --dataset alpaca \
  --description "Create code review examples that help developers improve code quality. Include security issues, performance problems, and best practices." \
  --count 150 \
  --model "anthropic/claude-3-5-sonnet"
```

#### Example 3: Financial Education Dataset
```bash
# Generate financial education content
data4ai prompt \
  --repo financial-education \
  --dataset alpaca \
  --description "Create educational content about personal finance. Cover topics like budgeting, investing, saving, and debt management." \
  --count 300 \
  --temperature 0.8
```

#### Example 4: Multi-language Support
```bash
# Generate Spanish language dataset
data4ai prompt \
  --repo spanish-tech-qa \
  --dataset alpaca \
  --description "Crear preguntas y respuestas en español sobre tecnología, programación y desarrollo de software" \
  --count 100 \
  --model "meta-llama/llama-3-8b-instruct"
```

### 🔧 Advanced Examples

#### Example 5: Custom Schema with Dolly
```bash
# Generate dataset using Dolly schema
data4ai prompt \
  --repo legal-summarizer \
  --dataset dolly \
  --description "Summarize legal case briefs into concise bullet points for junior lawyers" \
  --count 100 \
  --model "anthropic/claude-3-5-sonnet"
```

#### Example 6: Chat-style Dataset
```bash
# Generate conversation dataset
data4ai prompt \
  --repo ai-chat-examples \
  --dataset sharegpt \
  --description "Create conversations between users and AI assistants about various topics" \
  --count 50
```

#### Example 7: Reproducible Generation
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

#### Example 8: Preview Generation
```bash
# Test generation without saving
data4ai prompt \
  --repo test-preview \
  --dataset alpaca \
  --description "Create 5 cooking recipe instructions" \
  --count 5 \
  --dry-run
```

### 📈 Publishing to Hugging Face

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

### 🧪 Testing and Validation

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

### 📋 Main Commands

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

### ⚙️ Common Options

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

### 🚀 Quick Command Examples

```bash
# Generate 10 examples quickly
data4ai prompt --repo test --description "Create 10 cooking recipes" --count 10

# Use a specific model
data4ai prompt --repo test --description "Math problems" --model "anthropic/claude-3-5-sonnet" --count 50

# Generate with high creativity
data4ai prompt --repo test --description "Creative stories" --temperature 0.9 --count 20

# Generate reproducible results
data4ai prompt --repo test --description "Programming questions" --seed 42 --count 100

# Preview without saving
data4ai prompt --repo test --description "Test prompt" --count 5 --dry-run

# Generate and publish to HF
data4ai prompt --repo public-dataset --description "Educational content" --count 200 --huggingface

# Use DSPy for dynamic prompts (default)
data4ai prompt --repo dspy-dataset --description "Programming questions" --count 50 --use-dspy

# Use static prompts (disable DSPy)
data4ai prompt --repo static-dataset --description "Programming questions" --count 50 --no-use-dspy
```

### 📊 Excel Workflow Examples

```bash
# Create template
data4ai create-sample my_data.xlsx --dataset alpaca

# Generate from Excel (fill partial rows)
data4ai run my_data.xlsx --repo my-dataset --max-rows 100

# Generate from Excel with custom settings
data4ai run my_data.xlsx --repo my-dataset --model "anthropic/claude-3-5-sonnet" --temperature 0.6 --max-rows 500

# Convert Excel to dataset without AI (for complete files)
data4ai file-to-dataset my_data.xlsx --repo my-dataset
```

### 🔍 Utility Commands

```bash
# Validate your dataset
data4ai validate --repo my-dataset

# Get dataset statistics
data4ai stats --repo my-dataset

# List available models
data4ai list-models

# Check your configuration
data4ai config

# Show version
data4ai version

# Convert file to dataset (without AI)
data4ai file-to-dataset my_data.xlsx --repo my-dataset
```

## 🐍 Python API

### 🚀 Quick Start (Copy-Paste Ready)

```python
import os
from data4ai import generate_from_description

# Set your API key
os.environ["OPENROUTER_API_KEY"] = "your_key_here"

# Generate a simple dataset
result = generate_from_description(
    description="Create 10 questions and answers about Python programming",
    repo="my-first-dataset",
    dataset="alpaca",
    count=10
)

print(f"✅ Generated {result.row_count} rows")
print(f"📁 Output: {result.jsonl_path}")
```

### 📊 Excel Template Workflow

```python
from data4ai import create_sample_excel, generate_from_excel

# 1. Create Excel template
create_sample_excel("my_data.xlsx", dataset="alpaca")

# 2. Edit the Excel file manually (add some examples)
# Open my_data.xlsx in Excel/LibreOffice/Numbers

# 3. Generate complete dataset
result = generate_from_excel(
    excel_path="my_data.xlsx",
    repo="my-excel-dataset",
    dataset="alpaca",
    max_rows=100,
    temperature=0.7
)

print(f"✅ Generated {result.row_count} rows")
```

### 💼 Real-World Examples

#### Example 1: Customer Support Dataset
```python
from data4ai import generate_from_description

result = generate_from_description(
    description="Create customer support questions and answers for a SaaS product. Include common issues like login problems, billing questions, and feature requests.",
    repo="customer-support-qa",
    dataset="alpaca",
    count=200,
    temperature=0.6
)

print(f"✅ Generated {result.row_count} customer support examples")
```

#### Example 2: Code Review Dataset
```python
from data4ai import generate_from_description

result = generate_from_description(
    description="Create code review examples that help developers improve code quality. Include security issues, performance problems, and best practices.",
    repo="code-review-dataset",
    dataset="alpaca",
    count=150,
    model="anthropic/claude-3-5-sonnet"
)

print(f"✅ Generated {result.row_count} code review examples")
```

#### Example 3: Multi-language Dataset
```python
from data4ai import generate_from_description

result = generate_from_description(
    description="Crear preguntas y respuestas en español sobre tecnología, programación y desarrollo de software",
    repo="spanish-tech-qa",
    dataset="alpaca",
    count=100,
    model="meta-llama/llama-3-8b-instruct"
)

print(f"✅ Generated {result.row_count} Spanish tech examples")
```

### 🔧 Advanced Python Usage

#### Example 4: Object-Oriented API
```python
from data4ai import Data4AI

# Initialize with custom configuration
ai = Data4AI(
    openrouter_api_key="your_key_here",
    openrouter_model="anthropic/claude-3-5-sonnet",
    temperature=0.8
)

# Generate dataset
result = ai.generate_from_description(
    description="Create examples of Python code reviews",
    repo="python-reviews",
    dataset="alpaca",
    count=500,
    push_to_hf=True,
    private=True
)

# Access detailed metadata
print(f"📊 Schema: {result.schema}")
print(f"🤖 Model: {result.model}")
print(f"⚙️ Parameters: {result.params}")
print(f"📁 Output: {result.jsonl_path}")
```

#### Example 5: Batch Processing
```python
from data4ai import generate_from_description

# Generate multiple datasets
datasets = [
    {
        "description": "Create cooking recipe instructions",
        "repo": "cooking-recipes",
        "count": 50
    },
    {
        "description": "Create math word problems",
        "repo": "math-problems", 
        "count": 100
    },
    {
        "description": "Create programming interview questions",
        "repo": "interview-qa",
        "count": 75
    }
]

for dataset in datasets:
    result = generate_from_description(
        description=dataset["description"],
        repo=dataset["repo"],
        dataset="alpaca",
        count=dataset["count"]
    )
    print(f"✅ Generated {result.row_count} rows for {dataset['repo']}")
```

#### Example 6: Custom Configuration
```python
import os
from data4ai import generate_from_description

# Set multiple environment variables
os.environ.update({
    "OPENROUTER_API_KEY": "your_key_here",
    "OPENROUTER_MODEL": "meta-llama/llama-3-8b-instruct",
    "DATA4AI_TEMPERATURE": "0.7",
    "HF_TOKEN": "your_hf_token",
    "HF_ORG": "ZySecAI"
})

# Generate with custom parameters
result = generate_from_description(
    description="Create educational content about machine learning",
    repo="ml-education",
    dataset="alpaca",
    count=300,
    temperature=0.8,
    seed=42,  # For reproducibility
    push_to_hf=True,
    private=False
)

print(f"✅ Generated {result.row_count} ML education examples")
print(f"📁 Published to: https://huggingface.co/datasets/ZySecAI/ml-education")
```

### 🧪 Testing and Validation

```python
from data4ai import validate_dataset, get_dataset_stats

# Validate your dataset
validation_result = validate_dataset("my-dataset")
print(f"✅ Validation: {validation_result.is_valid}")
print(f"📊 Quality score: {validation_result.quality_score}")

# Get statistics
stats = get_dataset_stats("my-dataset")
print(f"📈 Total rows: {stats.total_rows}")
print(f"📏 Avg instruction length: {stats.avg_instruction_length}")
print(f"📏 Avg output length: {stats.avg_output_length}")
```

## 📋 Supported Schemas

### Alpaca Schema (Default)
```json
{
  "instruction": "What is machine learning?",
  "input": "Explain in simple terms",
  "output": "Machine learning is a type of artificial intelligence..."
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
    {"from": "human", "value": "Hello, how are you?"},
    {"from": "gpt", "value": "I'm doing well, thank you!"}
  ]
}
```

### Custom Schema
```python
# Define custom schema
custom_schema = {
    "columns": ["question", "answer", "category"],
    "template": "Create {category} questions and answers"
}

# Use custom schema
data4ai run data.xlsx --repo custom-dataset --schema custom_schema
```

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

## ❓ FAQ & Troubleshooting

### Common Issues

**Q: "OpenRouter API key not found"**
```bash
# Set your API key
export OPENROUTER_API_KEY="your_key_here"
# Or use a .env file
echo "OPENROUTER_API_KEY=your_key_here" > .env
```

**Q: "Model not available"**
```bash
# Check available models
data4ai models list
# Use a different model
data4ai run data.xlsx --model "anthropic/claude-3-5-sonnet"
```

**Q: "Excel file not found"**
```bash
# Create template first
data4ai create-sample my_data.xlsx --dataset alpaca
# Then edit and run
data4ai run my_data.xlsx --repo my-dataset
```

**Q: "Hugging Face push failed"**
```bash
# Set HF token
export HF_TOKEN="your_hf_token"
# Check token validity
data4ai hf test
```

### Performance Tips

- **Start Small**: Use `--max-rows 100` to test quality before scaling
- **Use Specific Prompts**: Detailed descriptions produce better results
- **Set Seeds**: Use `--seed 42` for reproducible results
- **Monitor Costs**: Check OpenRouter usage dashboard
- **Batch Processing**: Use multiple small runs instead of one large run

### Quality Improvement

- **Template Examples**: Provide 5-10 good examples in Excel
- **Clear Instructions**: Be specific about desired output format
- **Temperature Tuning**: Lower (0.3-0.5) for factual, higher (0.7-0.9) for creative
- **Model Selection**: Use larger models for complex tasks

## 🔮 DSPy Integration

Data4AI now includes **DSPy (Declarative Self-Improving Language Programs)** integration for dynamic, high-quality prompt generation. DSPy uses signatures to optimize prompts automatically, resulting in better dataset quality.

### Key Benefits

- **🎯 Dynamic Prompts**: Generate context-aware prompts instead of static templates
- **🔄 Adaptive Learning**: Improve prompts based on previous examples
- **📊 Schema Awareness**: Optimized prompts for different dataset schemas
- **🛡️ Fallback Support**: Automatic fallback to static prompts if DSPy fails
- **⚡ Performance**: Efficient prompt generation with caching

### Usage Examples

#### Basic DSPy Generation
```bash
# Enable DSPy (default)
data4ai prompt \
  --repo dspy-dataset \
  --description "Create educational content about machine learning" \
  --count 10 \
  --use-dspy

# Disable DSPy (use static prompts)
data4ai prompt \
  --repo static-dataset \
  --description "Create educational content about machine learning" \
  --count 10 \
  --no-use-dspy
```

#### Python API with DSPy
```python
from data4ai.integrations.dspy_prompts import create_prompt_generator
from data4ai.generator import DatasetGenerator

# Create DSPy prompt generator
prompt_generator = create_prompt_generator(
    model_name="meta-llama/llama-3-8b-instruct",
    use_dspy=True
)

# Generate dynamic prompt
prompt = prompt_generator.generate_schema_prompt(
    description="Create programming questions",
    schema_name="alpaca",
    count=5,
    use_dspy=True
)

# Use with dataset generator
generator = DatasetGenerator(model="meta-llama/llama-3-8b-instruct")
result = generator.generate_from_prompt_sync(
    description="Create programming questions",
    output_dir="outputs/dspy-example",
    schema_name="alpaca",
    count=10
)
```

#### Adaptive Prompting
```python
# Generate adaptive prompts using previous examples
previous_examples = [
    {"instruction": "Write a function", "input": "", "output": "def func(): pass"},
    {"instruction": "Create a class", "input": "", "output": "class MyClass: pass"}
]

adaptive_prompt = prompt_generator.generate_adaptive_prompt(
    description="Create more programming examples",
    schema_name="alpaca",
    count=3,
    previous_examples=previous_examples
)
```

### Configuration

DSPy is enabled by default. You can configure it in your `.env` file:

```bash
# Enable/disable DSPy
DATA4AI_USE_DSPY=true

# DSPy model (defaults to your main model)
DATA4AI_DSPY_MODEL=meta-llama/llama-3-8b-instruct
```

### Advanced Features

- **Schema-Specific Optimization**: Different prompt strategies for Alpaca, Dolly, ShareGPT
- **Few-Shot Learning**: Use previous examples to improve future prompts
- **Error Recovery**: Automatic fallback to static prompts if DSPy fails
- **Performance Monitoring**: Track prompt generation performance and quality

## 🧰 Advanced Features

### Batch Processing

```bash
# Process multiple Excel files
for file in datasets/*.xlsx; do
  data4ai run "$file" --repo "$(basename "$file" .xlsx)" --dataset alpaca
done
```

### Data Validation

```bash
# Validate generated dataset
data4ai validate --repo my-dataset

# Check quality metrics
data4ai stats --repo my-dataset
```

### Custom Templates

```python
# Create custom Excel template
from data4ai import create_custom_template

template = {
    "columns": ["question", "answer", "difficulty", "topic"],
    "examples": [
        ["What is Python?", "Python is a programming language", "easy", "programming"],
        ["Explain recursion", "Recursion is when a function calls itself", "medium", "algorithms"]
    ]
}

create_custom_template("custom.xlsx", template)
```

### Integration with Training Pipelines

```python
# Direct integration with unsloth
from data4ai import generate_from_excel
from unsloth import FastLanguageModel

# Generate dataset
result = generate_from_excel("data.xlsx", repo="training-data")

# Load for training
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=True,
)

# Train with generated data
trainer = SFTTrainer(
    model=model,
    train_dataset=result.load_dataset(),
    # ... other training params
)
```

## 📚 Documentation

- [Getting Started Guide](GETTING_STARTED.md) - Quick start with examples
- [CLI Command Reference](docs/COMMANDS.md) - Complete command documentation
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Codebase organization
- [Documentation Index](docs/README.md) - All documentation links

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Development Setup

```bash
git clone https://github.com/zysec/data4ai.git
cd data4ai
pip install -e ".[dev]"
pre-commit install
```

### Areas for Contribution

- **New Schemas**: Add support for more dataset formats
- **Quality Improvements**: Better validation and error handling
- **Performance**: Optimize generation speed and cost
- **Documentation**: Improve examples and guides
- **Testing**: Add more test cases and edge cases

### Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License © ZySec AI

## 🔗 Links

- [GitHub Repository](https://github.com/zysec/data4ai)
- [PyPI Package](https://pypi.org/project/data4ai/)
- [OpenRouter](https://openrouter.ai/) - AI Model API
- [Unsloth](https://github.com/unslothai/unsloth) - Training Framework
- [Hugging Face](https://huggingface.co/) - Dataset Hosting

---

**ZySec AI — Future Starts Here** 🚀