# Data4AI 🚀

> **Professional-grade AI dataset generation - The same technology ZySec AI uses to build small, powerful models for enterprise customers**

[![PyPI version](https://badge.fury.io/py/data4ai.svg)](https://pypi.org/project/data4ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Generate high-quality synthetic datasets using state-of-the-art language models. Data4AI leverages **Bloom's Revised Taxonomy** and advanced DSPy optimization to create training data that produces superior model performance - the same secret sauce ZySec AI has been using to build efficient, powerful models for their enterprise customers.

**Building domain-specific models is now as easy as a single command.** Whether you need medical LLMs, legal assistants, financial advisors, or any specialized AI - Data4AI generates the high-quality, object-oriented training data you need.

## 🎯 Why Data4AI?

- **🧠 Cognitive Intelligence**: Built-in Bloom's Revised Taxonomy ensures diverse thinking patterns across all six cognitive levels
- **🔬 Enterprise-Proven**: The same technology ZySec AI uses for customer model development
- **⚡ Domain-Specific Models Made Easy**: Generate specialized datasets for any field - medical, legal, finance, or any domain with just one command
- **📊 Quality First**: Advanced DSPy integration and quality verification out of the box

## 🚀 Quick Start

### Installation
```bash
uv pip install data4ai
```

### Get Your API Key
Get your OpenRouter API key from [openrouter.ai/keys](https://openrouter.ai/keys) for access to 100+ AI models.

```bash
export OPENROUTER_API_KEY="your_key_here"
```

### Generate Your First Dataset

**From a simple description (any domain):**
```bash
data4ai prompt \
  --repo medical-qa \
  --description "Medical diagnosis questions for common symptoms and conditions" \
  --count 100
```

**From domain documents (PDFs, Word docs, etc.):**
```bash
data4ai doc legal-contracts.pdf \
  --repo legal-qa \
  --count 100 \
  --taxonomy balanced
```

That's it! Your domain-specific dataset is ready in `medical-qa/data.jsonl` with professional-quality examples.

## 🧠 Bloom's Taxonomy Integration

Data4AI automatically applies **Bloom's Revised Taxonomy** to ensure cognitive diversity:

- **Remember** (20%): Basic recall and recognition
- **Understand** (20%): Comprehension and interpretation
- **Apply** (15%): Using knowledge in new situations
- **Analyze** (15%): Breaking down complex information
- **Evaluate** (15%): Making judgments and assessments
- **Create** (15%): Synthesizing new ideas and solutions

This cognitive balance is what makes Data4AI datasets so effective for training models that can think across all levels of complexity.

## 📊 Sample Output Quality

```json
{
  "messages": [
    {
      "role": "user",
      "content": "How would you design a caching system for a high-traffic web application?"
    },
    {
      "role": "assistant",
      "content": "I'd design a multi-tier caching system with: 1) Browser cache for static assets, 2) CDN for global content distribution, 3) Application-level cache (Redis/Memcached) for database queries, and 4) Database query cache. Key considerations include cache invalidation strategies, TTL policies, and cache warming..."
    }
  ],
  "taxonomy_level": "create"
}
```

Notice the `taxonomy_level` field - every example is cognitively classified for optimal training balance.

## 🌟 Key Features

- **🤖 100+ AI Models** - GPT-4, Claude, Llama, and more via OpenRouter
- **📄 Multi-Format Support** - PDFs, Word docs, Markdown, text files
- **🎯 ChatML & Alpaca** - Industry-standard dataset formats
- **☁️ HuggingFace Integration** - Direct publishing to the Hub
- **⚡ Production Ready** - Rate limiting, error recovery, deduplication

## 📚 Domain-Specific Examples

**🏥 Medical LLM Dataset:**
```bash
data4ai prompt \
  --repo medical-assistant \
  --description "Medical diagnosis and treatment recommendations for common conditions" \
  --count 500 \
  --taxonomy balanced
```

**⚖️ Legal AI Dataset:**
```bash
data4ai doc legal-documents/ \
  --repo legal-advisor \
  --count 1000 \
  --taxonomy balanced \
  --provenance
```

**💰 Financial Advisory Dataset:**
```bash
data4ai prompt \
  --repo financial-advisor \
  --description "Investment advice and financial planning for different risk profiles" \
  --count 300 \
  --taxonomy advanced
```

**🔬 Research Assistant Dataset:**
```bash
data4ai doc research-papers/ \
  --repo research-assistant \
  --count 800 \
  --taxonomy balanced \
  --verify
```

**🏗️ Engineering Dataset:**
```bash
data4ai prompt \
  --repo engineering-qa \
  --description "Software architecture and system design questions with detailed solutions" \
  --count 400 \
  --taxonomy balanced
```

## 🏢 Enterprise Heritage

Data4AI embodies the same quality standards and methodologies that ZySec AI has refined through building custom models for enterprise customers. When you use Data4AI, you're leveraging battle-tested technology that has powered real-world AI deployments.

## 📖 Documentation

For advanced features, configuration options, and detailed guides:

- [Complete Documentation](docs/README.md)
- [Advanced Usage](docs/DETAILED_USAGE.md)
- [Quality Features](docs/FEATURES.md)
- [API Reference](docs/API.md)

## 🚀 Quick Links

- **Installation**: `uv pip install data4ai`
- **Get API Key**: [openrouter.ai/keys](https://openrouter.ai/keys)
- **GitHub**: [github.com/zysec-ai/data4ai](https://github.com/zysec-ai/data4ai)
- **PyPI**: [pypi.org/project/data4ai](https://pypi.org/project/data4ai)

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

**Made with ❤️ by [ZySec AI](https://zysec.ai)** - Empowering enterprises with intelligent AI solutions.
