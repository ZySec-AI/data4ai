# 📚 Data4AI Documentation

Welcome to the Data4AI documentation! This directory contains comprehensive guides and references for using Data4AI.

## 📖 Documentation Index

### Getting Started
- [**Main README**](../README.md) - Quick start guide and overview
- [**Getting Started Guide**](../GETTING_STARTED.md) - Step-by-step tutorial for beginners
- [**CHANGELOG**](../CHANGELOG.md) - Version history and release notes

### Usage Guides  
- [**Detailed Usage Guide**](DETAILED_USAGE.md) - Complete CLI reference and advanced usage
- [**Examples**](EXAMPLES.md) - Code examples, recipes, and common patterns
- [**Commands Reference**](COMMANDS.md) - Complete CLI command documentation
- [**Features Overview**](FEATURES.md) - Complete feature list and capabilities
- [**ChatML Default**](CHATML_DEFAULT.md) - Understanding the default schema

### Configuration & Output
- [**Environment Setup Guide**](ENVIRONMENT_SETUP.md) - Complete guide for setting up environment variables
- [**Output Structure**](OUTPUT_STRUCTURE.md) - Where datasets are saved
- [**Troubleshooting Guide**](TROUBLESHOOTING.md) - Common issues and solutions

## 🗂️ Documentation Organization

```
data4ai/
├── Root Documentation
│   ├── README.md           # Quick start & overview
│   ├── GETTING_STARTED.md  # Step-by-step tutorial
│   ├── CHANGELOG.md        # Release history
│   └── CONTRIBUTING.md     # Contribution guide
│
├── docs/ (User Documentation)
│   ├── README.md           # This index file
│   ├── COMMANDS.md         # CLI reference
│   ├── DETAILED_USAGE.md   # Complete usage guide
│   ├── EXAMPLES.md         # Code examples & recipes
│   ├── FEATURES.md         # Feature overview
│   ├── ADVANCED_GENERATION.md # Budget-based generation
│   ├── CHATML_DEFAULT.md   # Default schema info
│   ├── ENVIRONMENT_SETUP.md # Environment setup
│   ├── OUTPUT_STRUCTURE.md # Output organization
│   └── TROUBLESHOOTING.md  # Problem solving
│
└── docs/maintainers/       # Maintainer Documentation
    ├── PUBLISHING.md       # PyPI release process
    └── OPENROUTER_DSPY.md  # Technical integration details
```

## 🗺️ Quick Navigation

### For New Users
1. Start with the [Main README](../README.md) for quick start
2. Follow the [Getting Started Guide](../GETTING_STARTED.md) for detailed setup
3. Check [Examples](EXAMPLES.md) for common use cases

### For Contributors
1. Read [Contributing Guide](../CONTRIBUTING.md) for guidelines
2. Check [Commands Reference](COMMANDS.md) for CLI details
3. Review [Output Structure](OUTPUT_STRUCTURE.md) for data organization

### For Advanced Users
1. Explore [Detailed Usage Guide](DETAILED_USAGE.md) for all features
2. Check [Examples](EXAMPLES.md) for advanced patterns
3. Review Python API examples in [Examples](EXAMPLES.md#-python-api-examples)

## 📋 Common Tasks

### Generate a Dataset
```bash
data4ai prompt --repo my-dataset --description "Your task" --count 100
```

### Generate from Documents
```bash
data4ai doc research_paper.pdf --repo doc-dataset --count 100
data4ai doc ./documents/ --repo multi-doc-dataset --count 500
```

### Publish to HuggingFace
```bash
data4ai push --repo my-dataset --private
```

### Validate Dataset
```bash
data4ai validate --repo my-dataset
data4ai stats --repo my-dataset
```

## 🔍 Finding Information

- **Installation?** → See [Main README](../README.md#-quick-start)
- **Environment Setup?** → See [Environment Setup Guide](ENVIRONMENT_SETUP.md)
- **CLI Options?** → See [Detailed Usage Guide](DETAILED_USAGE.md#cli-reference)
- **Code Examples?** → Check [Examples](EXAMPLES.md)
- **Having Problems?** → Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- **Error Messages?** → Review [Troubleshooting Guide](TROUBLESHOOTING.md)
- **Configuration?** → See [Environment Setup Guide](ENVIRONMENT_SETUP.md)
- **Contributing?** → See [Contributing Guide](../CONTRIBUTING.md)

## 📝 Documentation Standards

All documentation follows these principles:
- Clear, concise explanations
- Practical examples for every feature
- Updated with each release
- Accessible to users of all skill levels

## 🤝 Contributing to Docs

Help us improve the documentation:
1. Found an error? [Open an issue](https://github.com/zysec/data4ai/issues)
2. Have a better example? Submit a PR
3. Missing information? Let us know

## 📮 Contact

- GitHub Issues: [Report problems](https://github.com/zysec/data4ai/issues)
- Discussions: [Ask questions](https://github.com/zysec/data4ai/discussions)

---

*Last updated: 2025-08-17 | Version: 0.1.1*

**Data4AI** - AI-powered dataset generation made simple