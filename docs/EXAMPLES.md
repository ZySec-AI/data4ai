# 🎯 Data4AI Examples

## Quick Command Examples

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

## Excel Workflow Examples

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

## Utility Commands

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

### Excel Template Workflow
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

### Object-Oriented API
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

### Batch Processing
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

### Custom Configuration
```python
import os
from data4ai import generate_from_description

# Set multiple environment variables
os.environ.update({
    "OPENROUTER_API_KEY": "your_key_here",
    "OPENROUTER_MODEL": "openai/gpt-4o-mini",
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

### Testing and Validation
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