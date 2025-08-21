# Contributing to Data4AI

Thank you for your interest in contributing to Data4AI! This guide will help you get started with contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- OpenRouter API key (for testing generation features)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/data4ai.git
   cd data4ai
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev,excel,hf]"
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=data4ai --cov-report=html

# Run specific test file
pytest tests/test_schemas.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Add unit tests in `tests/unit/`
- Add integration tests in `tests/integration/`
- Use fixtures from `tests/conftest.py`
- Aim for >80% code coverage

## 📝 Code Style

### Formatting and Linting

We use `black` for formatting and `ruff` for linting:

```bash
# Format code
black .

# Check linting
ruff check .

# Fix linting issues
ruff check --fix .

# Type checking
mypy data4ai/
```

### Style Guidelines

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all function signatures
- Write descriptive docstrings (Google style)
- Keep functions focused and small
- Use meaningful variable names

### Example Code Style

```python
from typing import Optional, Dict, Any

def generate_dataset(
    description: str,
    count: int = 100,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a dataset from a natural language description.

    Args:
        description: Natural language description of the dataset
        count: Number of examples to generate
        model: Optional model override

    Returns:
        Dictionary containing generation results

    Raises:
        ValueError: If description is empty
        APIError: If API call fails
    """
    # Implementation here
    pass
```

## 🔄 Pull Request Process

### Before Submitting

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation if needed

3. **Run quality checks**
   ```bash
   # Format code
   black .

   # Lint
   ruff check .

   # Test
   pytest

   # Type check
   mypy data4ai/
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "feat: add support for custom schemas"
   ```

   Use conventional commit prefixes:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test additions/changes
   - `refactor:` Code refactoring
   - `chore:` Maintenance tasks

### Submitting PR

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Use a clear, descriptive title
   - Fill out the PR template
   - Link related issues
   - Add screenshots for UI changes

3. **PR Requirements**
   - All tests must pass
   - Code coverage maintained or improved
   - No linting errors
   - Documentation updated if needed
   - Approved by at least one maintainer

## 🐛 Reporting Issues

### Bug Reports

Please include:
- Python version (`python --version`)
- Data4AI version (`data4ai version`)
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/stack traces
- Minimal reproducible example

### Feature Requests

Please describe:
- The problem you're trying to solve
- Your proposed solution
- Alternative solutions considered
- Additional context or examples

## 📚 Documentation

### Adding Documentation

- User guides go in root directory (e.g., `GETTING_STARTED.md`)
- Technical docs go in `docs/` directory
- Update `README.md` for major features
- Add docstrings to all public functions/classes
- Include code examples where helpful

### Documentation Style

- Use clear, concise language
- Include code examples
- Add screenshots for UI features
- Keep formatting consistent
- Test all code examples

## 🏗️ Architecture Decisions

### Adding New Features

1. **Discuss first** - Open an issue for significant changes
2. **Follow existing patterns** - Maintain consistency with current architecture
3. **Keep it simple** - Avoid over-engineering
4. **Document decisions** - Add comments explaining non-obvious choices

### Dependencies

- Minimize new dependencies
- Use well-maintained packages
- Add to appropriate extras group if optional
- Document why dependency is needed

## 🚀 Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking API changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Checklist

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Build and check package
5. Create git tag
6. Push to PyPI

## 💬 Communication

### Getting Help

- **Discord**: [Join our server](https://discord.gg/data4ai)
- **Issues**: [GitHub Issues](https://github.com/zysec/data4ai/issues)
- **Email**: support@zysec.ai

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on what's best for the community

## 🙏 Recognition

Contributors will be:
- Listed in `CONTRIBUTORS.md`
- Mentioned in release notes
- Given credit in documentation

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Data4AI!** 🎉

Made with ❤️ by the ZySec AI Team
