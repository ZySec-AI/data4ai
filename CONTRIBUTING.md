# Contributing to Data4AI 🤝

Thanks for wanting to help make Data4AI better! Whether you're fixing bugs, adding features, or improving docs, every contribution matters.

## ⚡ Quick Start

### What You Need
- Python 3.9+
- Git
- OpenRouter API key (for testing) - get one [here](https://openrouter.ai/keys)

### Setup in 30 seconds
```bash
# Fork the repo on GitHub, then:
git clone https://github.com/yourusername/data4ai.git
cd data4ai

# Install for development
pip install -e ".[dev]"

# Set up quality checks
pre-commit install

# Add your API key for testing
export OPENROUTER_API_KEY="your_key_here"
```

Done! You're ready to contribute 🎉

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=data4ai

# Test a specific file
pytest tests/test_cli.py -v
```

## 🔄 Making Changes

### 1. Create a branch
```bash
git checkout -b fix/your-feature-name
```

### 2. Make your changes
- Write clean, readable code
- Add tests for new features
- Update docs if needed

### 3. Check quality
```bash
# Format code
black .

# Check linting
ruff check .

# Run tests
pytest
```

### 4. Commit and push
```bash
git add .
git commit -m "fix: describe what you fixed"
git push origin fix/your-feature-name
```

### 5. Create Pull Request
- Go to GitHub and create a PR
- Fill out the description
- Wait for review

## 🐛 Reporting Issues

Found a bug? Please include:
- Your Python version (`python --version`)
- Data4AI version (`data4ai version`)
- What you were trying to do
- What happened vs what you expected
- Error message (if any)

## 💡 Ideas & Requests

Have an idea for a new feature? Open an issue and tell us:
- What problem you're trying to solve
- How you think it should work
- Why it would be useful

## 📝 Code Style

We keep it simple:
- Use `black` for formatting (runs automatically)
- Use `ruff` for linting (runs automatically)
- Add type hints to function signatures
- Write docstrings for public functions
- Keep functions small and focused

Example:
```python
def generate_dataset(description: str, count: int = 100) -> dict[str, Any]:
    """Generate a dataset from a description.
    
    Args:
        description: What kind of dataset to create
        count: Number of examples to generate
        
    Returns:
        Dictionary with generation results
    """
    # Your code here
```

## 🤔 Types of Contributions

We welcome:
- 🐛 **Bug fixes** - Make something work better
- ✨ **New features** - Add cool new capabilities  
- 📚 **Documentation** - Help others understand the code
- 🧪 **Tests** - Make the codebase more robust
- 🎨 **Examples** - Show people how to use features
- 💬 **Community** - Answer questions, help users

## 📋 Good First Issues

New to the project? Look for issues labeled:
- `good first issue` - Perfect for beginners
- `help wanted` - We'd love help with these
- `documentation` - Improve our docs

## 🎯 Project Priorities

We're focusing on:
1. **Stability** - Making everything work reliably
2. **Usability** - Making it easy to use
3. **Performance** - Making it fast
4. **Features** - Adding cool new capabilities

## 🏗️ Architecture

Data4AI is organized as:
```
data4ai/
├── data4ai/           # Core library
│   ├── cli.py         # Command-line interface
│   ├── generator.py   # Dataset generation engine
│   ├── publisher.py   # HuggingFace publishing
│   └── utils.py       # Shared utilities
├── docs/             # User documentation
├── tests/            # Test suite
└── CONTRIBUTING.md   # This file
```

## 💬 Getting Help

Stuck? Need guidance?
- 💬 **Ask questions**: [GitHub Discussions](https://github.com/zysec-ai/data4ai/discussions)
- 🐛 **Report bugs**: [GitHub Issues](https://github.com/zysec-ai/data4ai/issues)
- 📧 **Email us**: [research@zysec.ai](mailto:research@zysec.ai)

## 🙏 Recognition

All contributors get:
- Listed in release notes
- Credit in the README
- Our eternal gratitude! 

## 🎉 Community Values

We believe in:
- **Being welcoming** - Everyone starts somewhere
- **Being helpful** - Share knowledge freely  
- **Being respectful** - Treat others well
- **Being collaborative** - We build better things together

## 📄 License

By contributing, you agree your code will be licensed under MIT (same as the project).

---

**Ready to contribute?** Fork the repo and dive in! We can't wait to see what you build. 🚀