# 📚 Data4AI Documentation

This directory contains user guides and technical documentation for Data4AI.

## 📖 Quick Navigation

- **[Main README](../README.md)** - Start here for installation and quick examples
- **[Examples](EXAMPLES.md)** - Real-world usage examples and recipes
- **[Commands](COMMANDS.md)** - Complete CLI reference
- **[Features](FEATURES.md)** - Advanced features and options
- **[YouTube Integration](YOUTUBE.md)** - Extract datasets from YouTube videos
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Contributing](../CONTRIBUTING.md)** - How to contribute to the project

## 🗂️ Documentation Structure

```
data4ai/
├── README.md              # Main documentation (start here)
├── CONTRIBUTING.md        # Contribution guidelines  
├── CHANGELOG.md           # Release history
│
├── docs/                  # User documentation
│   ├── README.md          # This file
│   ├── EXAMPLES.md        # Usage examples
│   ├── COMMANDS.md        # CLI reference
│   ├── FEATURES.md        # Feature overview
│   ├── YOUTUBE.md         # YouTube integration guide
│   └── TROUBLESHOOTING.md # Common issues
│
├── examples/              # Runnable example scripts
│   ├── README.md          # Examples overview
│   ├── 01_basic_cli_examples.sh
│   ├── 02_python_api_examples.py
│   ├── 03_youtube_integration_examples.sh
│   └── 04_document_processing_examples.sh
│
├── data4ai/              # Source code
└── tests/                # Test suite
```

## 📋 Common Tasks

### Generate Dataset from Description
```bash
data4ai prompt --repo my-dataset --description "Your description" --count 100
```

### Generate from Documents  
```bash
data4ai doc document.pdf --repo doc-dataset --count 100
```

### Upload to HuggingFace
```bash  
data4ai push --repo my-dataset
```

### Validate Dataset
```bash
data4ai validate --repo my-dataset
data4ai stats --repo my-dataset  
```

## 🔍 Need Help?

- **Installation issues?** → See [Main README](../README.md#-quick-start)
- **Command options?** → Check [Commands Reference](COMMANDS.md)
- **Real examples?** → Browse [Examples](EXAMPLES.md)
- **Error messages?** → Review [Troubleshooting](TROUBLESHOOTING.md)
- **Want to contribute?** → Read [Contributing Guide](../CONTRIBUTING.md)

## 🤝 Community

- **Report bugs**: [GitHub Issues](https://github.com/zysec-ai/data4ai/issues)
- **Ask questions**: [GitHub Discussions](https://github.com/zysec-ai/data4ai/discussions)  
- **Contact us**: [research@zysec.ai](mailto:research@zysec.ai)

---

*Documentation is kept simple and focused. Each file serves a specific purpose to help you get things done quickly.*