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

### Technical Documentation
- [**Project Structure**](PROJECT_STRUCTURE.md) - Codebase organization and architecture
- [**Publishing Guide**](PUBLISHING.md) - PyPI publishing instructions for maintainers
- [**Contributing Guide**](../CONTRIBUTING.md) - How to contribute to the project

### Configuration & Setup
- [**Environment Setup Guide**](ENVIRONMENT_SETUP.md) - Complete guide for setting up environment variables
- [**Troubleshooting Guide**](TROUBLESHOOTING.md) - Common issues and solutions
- [**.env.example**](../.env.example) - Example environment variables (reference only)

## 🗂️ Documentation Organization

```
data4ai/
├── User-Facing Docs (Root)
│   ├── README.md           # Quick start & overview
│   ├── GETTING_STARTED.md  # Detailed setup guide
│   ├── CHANGELOG.md        # Release history
│   └── CONTRIBUTING.md     # Contribution guide
│
└── docs/ (Detailed Documentation)
    ├── README.md           # This index file
    ├── DETAILED_USAGE.md   # Complete usage guide
    ├── EXAMPLES.md         # Code examples & recipes
    ├── COMMANDS.md         # CLI reference
    ├── ENVIRONMENT_SETUP.md # Environment configuration guide
    ├── TROUBLESHOOTING.md  # Problem solving guide
    ├── PROJECT_STRUCTURE.md # Architecture details
    └── PUBLISHING.md       # Release procedures
```

## 🗺️ Quick Navigation

### For New Users
1. Start with the [Main README](../README.md) for quick start
2. Follow the [Getting Started Guide](../GETTING_STARTED.md) for detailed setup
3. Check [Examples](EXAMPLES.md) for common use cases

### For Developers
1. Review [Project Structure](PROJECT_STRUCTURE.md) to understand the codebase
2. Check [Commands Reference](COMMANDS.md) for CLI implementation
3. See [Publishing Guide](PUBLISHING.md) for release process

### For Advanced Users
1. Explore [Detailed Usage Guide](DETAILED_USAGE.md) for all features
2. Check [Examples](EXAMPLES.md) for advanced patterns
3. Review Python API examples in [Examples](EXAMPLES.md#-python-api-examples)

## 📋 Common Tasks

### Generate a Dataset
```bash
data4ai prompt --repo my-dataset --description "Your task" --count 100
```

### Use Excel Template
```bash
data4ai create-sample template.xlsx
data4ai run template.xlsx --repo my-dataset
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