# Data4AI 🤖

[![PyPI version](https://badge.fury.io/py/data4ai.svg)](https://pypi.org/project/data4ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Stars](https://img.shields.io/github/stars/zysec-ai/data4ai.svg)](https://github.com/zysec-ai/data4ai/stargazers)

> **Generate high-quality AI training datasets from simple descriptions or documents**

Data4AI makes it easy to create instruction-tuning datasets for training and fine-tuning language models. Whether you're building domain-specific models or need quality training data, Data4AI has you covered.

## ✨ Features

- 🎯 **Simple Commands** - Generate datasets from descriptions or documents  
- 📚 **Multiple Formats** - Support for ChatML, Alpaca, and custom schemas
- 🔄 **Smart Processing** - Automatic chunking, deduplication, and quality validation
- 🏷️ **Cognitive Taxonomy** - Built-in Bloom's taxonomy for balanced learning
- ☁️ **Direct Upload** - Push datasets directly to HuggingFace Hub
- 🌐 **100+ Models** - Access to GPT, Claude, Llama, and more via OpenRouter

## 🚀 Quick Start

### Install
```bash
pip install data4ai
```

### Get API Key
Get your free API key from [OpenRouter](https://openrouter.ai/keys):
```bash
export OPENROUTER_API_KEY="your_key_here"
```

### Generate Your First Dataset

**From a description:**
```bash
data4ai prompt \
  --repo my-dataset \
  --description "Python programming questions for beginners" \
  --count 100
```

**From documents:**
```bash
data4ai doc document.pdf \
  --repo doc-dataset \
  --count 100
```

**From YouTube videos:**
```bash
data4ai youtube @3Blue1Brown \
  --repo math-videos \
  --count 100
```

**Upload to HuggingFace:**
```bash
data4ai push --repo my-dataset
```

That's it! Your dataset is ready at `outputs/datasets/my-dataset/data.jsonl` 🎉

## 📖 Documentation

- **[Examples](docs/EXAMPLES.md)** - Real-world usage examples
- **[Commands](docs/COMMANDS.md)** - Complete CLI reference  
- **[Features](docs/FEATURES.md)** - Advanced features and options
- **[YouTube Integration](docs/YOUTUBE.md)** - Extract datasets from YouTube videos
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Runnable Examples](examples/)** - Ready-to-run example scripts

## 🤝 Community

### Contributing
We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines  
- Testing requirements
- Pull request process

### Getting Help
- 🐛 **Bug reports**: [GitHub Issues](https://github.com/zysec-ai/data4ai/issues)
- 💬 **Questions**: [GitHub Discussions](https://github.com/zysec-ai/data4ai/discussions)
- 📧 **Contact**: [research@zysec.ai](mailto:research@zysec.ai)

### Project Structure
```
data4ai/
├── data4ai/           # Core library code
├── docs/             # User documentation  
├── tests/            # Test suite
├── README.md         # You are here
├── CONTRIBUTING.md   # How to contribute
└── CHANGELOG.md      # Release history
```

## 🎯 Use Cases

**🏥 Medical Training Data**
```bash
data4ai prompt --repo medical-qa \
  --description "Medical diagnosis Q&A for common symptoms" \
  --count 500
```

**⚖️ Legal Assistant Data** 
```bash
data4ai doc legal-docs/ --repo legal-assistant --count 1000
```

**💻 Code Training Data**
```bash
data4ai prompt --repo code-qa \
  --description "Python debugging and best practices" \
  --count 300
```

**📺 Educational Video Content**
```bash
# Programming tutorials
data4ai youtube --search "python tutorial,programming" --repo python-course --count 200

# Educational channels  
data4ai youtube @3Blue1Brown --repo math-education --count 150

# Conference talks
data4ai youtube @pycon --repo conference-talks --count 100
```

## 🛠️ Advanced Usage

### Quality Control
```bash
data4ai doc document.pdf \
  --repo high-quality \
  --verify \
  --taxonomy advanced \
  --dedup-strategy content
```

### Batch Processing
```bash
data4ai doc documents/ \
  --repo batch-dataset \
  --count 1000 \
  --batch-size 20 \
  --recursive
```

### Custom Models
```bash
export OPENROUTER_MODEL="anthropic/claude-3-5-sonnet"
data4ai prompt --repo custom-model --description "..." --count 100
```

## 🏗️ Architecture

Data4AI is built with:
- **Async Processing** - Fast concurrent generation
- **DSPy Integration** - Advanced prompt optimization  
- **Quality Validation** - Automatic content verification
- **Atomic Writes** - Safe file operations
- **Schema Validation** - Ensures data consistency

## 📊 Sample Output

```json
{
  "messages": [
    {
      "role": "user", 
      "content": "How do I handle exceptions in Python?"
    },
    {
      "role": "assistant",
      "content": "In Python, use try-except blocks to handle exceptions: ..."
    }
  ],
  "taxonomy_level": "understand"
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
export OPENROUTER_API_KEY="your_key"

# Optional  
export OPENROUTER_MODEL="openai/gpt-4o-mini"  # Default model
export HF_TOKEN="your_hf_token"               # For HuggingFace uploads
export OUTPUT_DIR="./outputs/datasets"       # Default output directory
```

### Config File
Create `.data4ai.yaml` in your project:
```yaml
default_model: "anthropic/claude-3-5-sonnet"
default_schema: "chatml" 
default_count: 100
quality_check: true
```

## 🚀 Roadmap

- [ ] **Custom Schema Support** - Define your own data formats
- [ ] **Local Model Support** - Use local LLMs (Ollama, vLLM)
- [ ] **Multi-language Datasets** - Generate data in multiple languages  
- [ ] **Dataset Analytics** - Advanced quality metrics and visualization
- [ ] **API Service** - RESTful API for dataset generation

## 📈 Performance

- **Speed**: Generate 100 examples in ~2 minutes
- **Quality**: Built-in validation and deduplication
- **Scale**: Tested with datasets up to 100K examples
- **Memory**: Efficient streaming for large documents

## ⭐ Show Your Support

If Data4AI helps you, please:
- ⭐ Star this repository
- 🐦 Share on social media  
- 🤝 Contribute improvements
- 💝 Sponsor the project

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🏢 About ZySec AI

ZySec AI empowers enterprises to confidently adopt AI where data sovereignty, privacy, and security are non-negotiable—helping them move beyond fragmented, siloed systems into a new era of intelligence, from data to agentic AI, on a single platform. Data4AI is developed by [ZySec AI](https://zysec.ai).

---

<div align="center">
  <b>Made with ❤️ by ZySec AI to the open source community</b>
</div>