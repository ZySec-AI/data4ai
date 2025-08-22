# 🎯 Data4AI Examples

## 🚀 Quick Command Examples

### Basic Generation
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
```

### Document-based Generation
```bash
# Generate from a single document
data4ai doc research_paper.pdf --repo research-qa --count 100

# Generate from multiple documents
data4ai doc ./documents/ --repo knowledge-base --count 500

# Use specific taxonomy level
data4ai doc tutorial.md --repo tutorial-qa --taxonomy basic --count 50

# Generate conversations from documents
data4ai doc manual.pdf --repo manual-chat --dataset chatml --count 200
```

### Advanced Options
```bash
# Use Bloom's taxonomy levels
data4ai prompt --repo beginner --description "Basic math concepts" --taxonomy basic --count 100
data4ai prompt --repo advanced --description "Research methodology" --taxonomy advanced --count 100

# Control batch processing
data4ai prompt --repo large-dataset --description "Programming tutorials" --count 1000 --batch-size 5

# Use DSPy optimization (default)
data4ai prompt --repo optimized-dataset --description "Programming questions" --count 50

# Disable DSPy for faster generation
data4ai prompt --repo static-dataset --description "Programming questions" --count 50 --no-use-dspy
```

### Publishing to HuggingFace
```bash
# Set HF token
export HF_TOKEN="your_hf_token"

# Generate and publish separately
data4ai prompt --repo public-dataset --description "Educational content" --count 200
data4ai push --repo public-dataset

# Generate private dataset
data4ai prompt --repo private-dataset --description "Internal training data" --count 100
data4ai push --repo private-dataset --private
```

## 🐍 Python API Examples

### Quick Start
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

### Document-based Generation
```python
from data4ai import generate_from_documents

# Generate from a single document
result = generate_from_documents(
    document_path="research_paper.pdf",
    repo="research-qa",
    dataset="chatml",
    count=100,
    taxonomy="advanced"
)

print(f"✅ Generated {result.row_count} Q&A pairs")
print(f"📁 Output: {result.jsonl_path}")
```

### Object-Oriented API
```python
from data4ai import Data4AI

# Initialize with custom configuration
ai = Data4AI(
    openrouter_api_key="your_key_here",
    openrouter_model="anthropic/claude-3-5-sonnet",
    temperature=0.8,
    hf_token="your_hf_token",
    hf_org="YourOrg"
)

# Generate dataset
result = ai.generate_from_description(
    description="Create examples of Python code reviews",
    repo="python-reviews",
    dataset="alpaca",
    count=500
)

# Publish to HuggingFace
ai.publish_to_huggingface(
    repo="python-reviews",
    private=True
)

print(f"📊 Schema: {result.schema}")
print(f"🤖 Model: {result.model}")
print(f"📁 Output: {result.jsonl_path}")
```

### Batch Processing
```python
from data4ai import generate_from_description

# Generate multiple datasets
datasets = [
    {
        "description": "Create cooking recipe instructions",
        "repo": "cooking-recipes",
        "count": 50,
        "taxonomy": "basic"
    },
    {
        "description": "Create math word problems",
        "repo": "math-problems",
        "count": 100,
        "taxonomy": "balanced"
    },
    {
        "description": "Create programming interview questions",
        "repo": "interview-qa",
        "count": 75,
        "taxonomy": "advanced"
    }
]

for dataset in datasets:
    result = generate_from_description(
        description=dataset["description"],
        repo=dataset["repo"],
        dataset="alpaca",
        count=dataset["count"],
        taxonomy=dataset["taxonomy"]
    )
    print(f"✅ Generated {result.row_count} rows for {dataset['repo']}")
```

### Custom Configuration
```python
import os
from data4ai import generate_from_description

# Set multiple environment variables
os.environ.update({
    "OPENROUTER_API_KEY": "your_key_here",
    "OPENROUTER_MODEL": "openai/gpt-4o-mini",
    "HF_TOKEN": "your_hf_token"
})

# Generate with custom parameters
result = generate_from_description(
    description="Create educational content about machine learning",
    repo="ml-education",
    dataset="alpaca",
    count=300,
    temperature=0.8,
    taxonomy="balanced",
    batch_size=10
)

print(f"✅ Generated {result.row_count} ML education examples")
print(f"📁 Dataset saved to: {result.output_dir}")
```

## 📊 Schema Examples

### Alpaca Format (Default)
```python
# Generate instruction-following examples
result = generate_from_description(
    description="Create Python programming tutorials",
    repo="python-tutorials",
    dataset="alpaca",
    count=100
)

# Example output:
# {
#   "instruction": "Write a Python function to reverse a string",
#   "input": "def reverse_string(s):",
#   "output": "def reverse_string(s):\n    return s[::-1]"
# }
```

### ChatML Format (Conversations)
```python
# Generate conversation examples
result = generate_from_description(
    description="Create customer support conversations",
    repo="support-chat",
    dataset="chatml",
    count=200
)

# Example output:
# {
#   "messages": [
#     {"role": "user", "content": "How do I reset my password?"},
#     {"role": "assistant", "content": "To reset your password, click..."}
#   ]
# }
```

## 🎯 Taxonomy Examples

### Basic Level (Beginner-friendly)
```python
# Focus on Remember & Understand
result = generate_from_description(
    description="Basic Python concepts for beginners",
    repo="python-basics",
    taxonomy="basic",
    count=100
)
# Generates simple recall and comprehension questions
```

### Advanced Level (Critical thinking)
```python
# Focus on Analyze, Evaluate & Create
result = generate_from_description(
    description="Advanced software architecture patterns",
    repo="architecture-advanced",
    taxonomy="advanced",
    count=100
)
# Generates complex analysis and design questions
```

### Balanced Level (All cognitive levels)
```python
# Balanced distribution across all Bloom's levels
result = generate_from_description(
    description="Complete programming curriculum",
    repo="programming-complete",
    taxonomy="balanced",
    count=500
)
# Generates varied complexity questions
```

## 🔧 Troubleshooting Examples

### API Key Issues
```python
import os

# Check if API key is set
if not os.getenv("OPENROUTER_API_KEY"):
    print("❌ Please set OPENROUTER_API_KEY")
    print("export OPENROUTER_API_KEY='your-key-here'")
else:
    print("✅ API key is configured")
```

### Model Selection
```python
# Use different models for different tasks
models = {
    "creative": "anthropic/claude-3-5-sonnet",
    "factual": "openai/gpt-4o-mini",
    "coding": "deepseek/deepseek-coder"
}

# Generate creative content
result = generate_from_description(
    description="Write creative short stories",
    repo="stories",
    model=models["creative"],
    temperature=0.9,
    count=50
)
```

### Error Handling
```python
from data4ai import generate_from_description
from data4ai.exceptions import GenerationError, ConfigurationError

try:
    result = generate_from_description(
        description="Test generation",
        repo="test-dataset",
        count=10
    )
    print(f"✅ Success: {result.row_count} examples generated")

except ConfigurationError as e:
    print(f"❌ Configuration error: {e}")
    print("Check your API keys and settings")

except GenerationError as e:
    print(f"❌ Generation error: {e}")
    print("Try reducing batch size or count")

except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

---

## 📁 Runnable Example Scripts

For complete, ready-to-run examples, see the [`examples/`](../examples/) directory:

- **[01_basic_cli_examples.sh](../examples/01_basic_cli_examples.sh)** - Core CLI commands and options
- **[02_python_api_examples.py](../examples/02_python_api_examples.py)** - Python API usage patterns  
- **[03_youtube_integration_examples.sh](../examples/03_youtube_integration_examples.sh)** - YouTube content extraction
- **[04_document_processing_examples.sh](../examples/04_document_processing_examples.sh)** - Document-based generation

**For more details, see [README.md](../README.md) and [COMMANDS.md](COMMANDS.md)**
