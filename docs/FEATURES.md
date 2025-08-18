# Data4AI Features

## 🚀 Core Generation Modes

### 1. **Description-Based Generation** (`prompt`)
Generate datasets from natural language descriptions using AI.
```bash
data4ai prompt --repo my-dataset --description "Create Python Q&A" --count 100
```

### 2. **Document-Based Generation** (`doc`)
Extract high-quality datasets from documents with advanced processing.
```bash
data4ai doc document.pdf --repo doc-qa --count 100
data4ai doc ./documents/ --repo knowledge-base --count 500
```

### 3. **HuggingFace Publishing** (`push`)
Direct integration with HuggingFace Hub for dataset sharing.
```bash
data4ai push --repo my-dataset --private
```

## 📊 Supported Dataset Schemas

### ChatML Format
OpenAI's conversation format for chat models:
```json
{
  "messages": [
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is..."}
  ]
}
```

### Alpaca Format (Default)
Stanford's instruction-following format:
```json
{
  "instruction": "Explain Python",
  "input": "For beginners",
  "output": "Python is a programming language..."
}
```

## 🎯 Advanced Quality Features

### Bloom's Revised Taxonomy
Ensures cognitive diversity across all complexity levels:

- **`basic`** - Remember & Understand (beginner-friendly)
- **`balanced`** - All cognitive levels (default)
- **`advanced`** - Analyze, Evaluate & Create (critical thinking)
- **`none`** - No specific taxonomy requirements

```bash
data4ai prompt --repo beginner --description "Basic math" --taxonomy basic
data4ai prompt --repo advanced --description "Research analysis" --taxonomy advanced
```

### DSPy Integration
Dynamic prompt optimization for higher quality generation:
- Automatic prompt optimization
- Context-aware generation
- Adaptive learning from examples
- Chain-of-thought reasoning

```bash
# DSPy enabled by default
data4ai prompt --repo optimized --description "Complex reasoning tasks"

# Disable for faster generation
data4ai prompt --repo simple --description "Basic questions" --no-use-dspy
```

## 📄 Document Processing

### Supported Formats
- **PDF documents** - Research papers, manuals, reports
- **Markdown files** (.md) - Documentation, wikis
- **Plain text files** (.txt) - Articles, transcripts
- **Microsoft Word** (.docx) - Documents, reports

### Advanced Document Features
- **Recursive folder scanning** - Process entire directories
- **Intelligent chunking** - Optimal text segmentation
- **Context preservation** - Maintain document coherence
- **Taxonomy-aware generation** - Cognitive level distribution
- **Provenance tracking** - Source references and offsets

```bash
# Process single document
data4ai doc research.pdf --repo research-qa --taxonomy advanced

# Process entire folder
data4ai doc ./documents/ --repo knowledge-base --count 1000
```

## 🔧 Production-Ready Features

### Rate Limiting & Reliability
- Automatic rate limit handling
- Exponential backoff retry
- Request failure recovery
- Concurrent request management

### Data Quality Assurance
- **Atomic file operations** - Prevent data corruption
- **Automatic checkpointing** - Resume from interruptions
- **Schema validation** - Ensure format compliance
- **Deduplication** - Remove duplicate entries
- **Metrics calculation** - Quality assessment

### Error Recovery
```bash
# Resume interrupted generation
data4ai prompt --repo my-dataset --description "Continue generation" --count 500
# Automatically resumes from checkpoint if interrupted
```

## ☁️ Integration & Publishing

### HuggingFace Hub
Seamless dataset publishing with rich metadata:
```bash
# Generate and publish
data4ai prompt --repo public-dataset --description "Educational content" --count 200
data4ai push --repo public-dataset

# Private datasets
data4ai push --repo private-dataset --private
```

### OpenRouter API
Access to 100+ state-of-the-art language models:
- **OpenAI**: GPT-4, GPT-4 Turbo, GPT-4o
- **Anthropic**: Claude 3, Claude 3.5 Sonnet
- **Meta**: Llama 3, Llama 3.1
- **Google**: Gemini Pro, Gemini Flash
- **Mistral**: 7B, 8x7B, 8x22B
- **And many more...**

```bash
# Use specific models
data4ai prompt --repo creative --description "Stories" --model "anthropic/claude-3-5-sonnet"
data4ai prompt --repo coding --description "Code review" --model "deepseek/deepseek-coder"
```

## ⚡ Performance Optimization

### Intelligent Batching
- Configurable batch sizes
- Optimal API utilization
- Memory-efficient processing
- Progress tracking

```bash
# Control batch processing
data4ai prompt --repo large --description "Big dataset" --count 1000 --batch-size 5
```

### Smart Processing
- Token-aware chunking
- Context-preserving splits
- Efficient memory usage
- Streaming file writes

## 🛠️ Developer Features

### Python API
Full programmatic access to all functionality:
```python
from data4ai import generate_from_description, generate_from_documents

# Description-based generation
result = generate_from_description(
    description="Create programming tutorials",
    repo="tutorials",
    dataset="alpaca",
    count=100,
    taxonomy="balanced"
)

# Document-based generation
result = generate_from_documents(
    document_path="./docs/",
    repo="doc-qa",
    dataset="chatml",
    count=500,
    taxonomy="advanced"
)
```

### Object-Oriented Interface
```python
from data4ai import Data4AI

ai = Data4AI(
    openrouter_api_key="your-key",
    hf_token="your-token"
)

result = ai.generate_from_description(
    description="Educational content",
    repo="education",
    count=200
)

ai.publish_to_huggingface(repo="education", private=False)
```

### Configuration Management
- Environment variables
- Flexible parameter overrides
- Default settings
- Validation and error handling

## 🔐 Security & Privacy

### Secure API Management
- Environment-based key storage
- No credential logging
- Secure token handling
- Optional credential validation

### Privacy Protection
- No data retention by default
- Local processing option
- Configurable output locations
- User-controlled publishing

## 📈 Monitoring & Analytics

### Real-time Progress
- Live generation progress
- Token usage tracking
- Batch completion status
- Error rate monitoring

### Quality Metrics
- **Completion rate** - Successful generations
- **Average lengths** - Content size statistics
- **Schema compliance** - Format validation
- **Taxonomy distribution** - Cognitive level balance

### Cost Tracking
- Token usage per request
- Model cost estimation
- Batch efficiency metrics
- API usage statistics

## 🎨 Customization Options

### Generation Parameters
```bash
# Temperature control
data4ai prompt --repo creative --description "Stories" --temperature 0.9

# Reproducible generation
data4ai prompt --repo consistent --description "Facts" --seed 42

# Custom batch sizes
data4ai prompt --repo efficient --description "Large dataset" --batch-size 10
```

### Output Control
- Custom output directories
- Flexible naming schemes
- Metadata inclusion
- Format selection

### Model Selection
Choose the best model for your task:
```bash
# Creative writing
data4ai prompt --model "anthropic/claude-3-5-sonnet" --temperature 0.8

# Factual content
data4ai prompt --model "openai/gpt-4o-mini" --temperature 0.3

# Code generation
data4ai prompt --model "deepseek/deepseek-coder" --temperature 0.1
```

---

**Ready to get started? See [GETTING_STARTED.md](../GETTING_STARTED.md) for setup instructions!**