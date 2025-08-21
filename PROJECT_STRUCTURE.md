# Data4AI Project Structure

## 📁 Directory Layout

```
data4ai/
├── .github/                    # GitHub Actions workflows
│   └── workflows/
│       ├── ci.yml              # Continuous Integration
│       ├── publish.yml         # Auto-publish to PyPI
│       └── manual-publish.yml  # Manual PyPI publish
│
├── data4ai/                    # Main package
│   ├── __init__.py            # Package initialization & exports
│   ├── __main__.py            # CLI entry point
│   ├── cli.py                 # CLI commands implementation
│   ├── cli_wrapper.py         # CLI wrapper for entry point
│   ├── config.py              # Configuration management
│   ├── generator.py           # Core dataset generation engine
│   ├── client.py              # OpenRouter API client
│   ├── schemas.py             # Dataset schema definitions
│   ├── utils.py               # Utility functions
│   ├── atomic_writer.py       # Atomic file operations
│   ├── checkpoint.py          # Checkpoint & resume functionality
│   ├── deduplicator.py        # Data deduplication
│   ├── rate_limiter.py        # API rate limiting
│   ├── publisher.py           # HuggingFace publishing
│   ├── document_handler.py    # PDF/DOCX/MD/TXT processing
│   ├── excel_handler.py       # Excel file processing
│   ├── csv_handler.py         # CSV file processing
│   ├── exceptions.py          # Custom exceptions
│   ├── error_handler.py       # User-friendly error messages
│   │
│   └── integrations/          # External service integrations
│       ├── __init__.py
│       ├── dspy_prompts.py           # DSPy prompt optimization
│       ├── dspy_document_prompts.py  # Document-specific DSPy
│       └── openrouter_dspy.py        # OpenRouter DSPy client
│
├── docs/                      # User documentation
│   ├── README.md              # Documentation index
│   ├── COMMANDS.md            # CLI command reference
│   ├── DETAILED_USAGE.md      # Complete usage guide
│   ├── EXAMPLES.md            # Code examples
│   ├── FEATURES.md            # Feature overview
│   ├── ADVANCED_GENERATION.md # Budget-based generation
│   ├── CHATML_DEFAULT.md      # Default schema info
│   ├── ENVIRONMENT_SETUP.md   # Environment setup
│   ├── OUTPUT_STRUCTURE.md    # Output organization
│   ├── TROUBLESHOOTING.md     # Problem solving
│   │
│   └── maintainers/           # Maintainer documentation
│       ├── README.md          # Maintainer doc index
│       ├── PUBLISHING.md      # PyPI release process
│       ├── PYPI_UPLOAD.md     # PyPI upload guide
│       └── OPENROUTER_DSPY.md # Technical integration
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py            # Pytest configuration
│   ├── unit/                  # Unit tests
│   │   └── test_*.py          # Individual unit tests
│   ├── integration/           # Integration tests
│   │   └── __init__.py
│   ├── fixtures/              # Test fixtures
│   └── sample_docs/           # Sample documents for testing
│
├── scripts/                   # Utility scripts
│   ├── create_release.sh      # Release automation
│   └── upload_to_pypi.sh      # PyPI upload script
│
├── outputs/                   # Generated datasets (gitignored)
│   └── [dataset-name]/
│       ├── data.jsonl         # Generated data
│       └── metadata.json      # Generation metadata
│
├── README.md                  # Project overview & quick start
├── GETTING_STARTED.md         # Detailed setup guide
├── CHANGELOG.md               # Release history
├── CONTRIBUTING.md            # Contribution guidelines
├── LICENSE                    # MIT license
├── pyproject.toml            # Project configuration
├── setup_env.sh              # Environment setup script
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
└── .pre-commit-config.yaml  # Pre-commit hooks
```

## 🔧 Key Components

### Core Package (`data4ai/`)
- **CLI**: Command-line interface implementation (`cli.py`)
- **Generator**: Core engine for dataset generation (`generator.py`)
- **Client**: API client for OpenRouter (`client.py`)
- **Schemas**: Support for multiple dataset formats (`schemas.py`)
- **Config**: Settings and environment management (`config.py`)

### Integrations (`data4ai/integrations/`)
- **DSPy Prompts**: Dynamic prompt optimization
- **Document DSPy**: Document-specific optimization
- **OpenRouter DSPy**: OpenRouter integration for DSPy

### File Handlers
- **Documents**: PDF, DOCX, Markdown, Text (`document_handler.py`)
- **Excel**: Excel file processing (`excel_handler.py`)
- **CSV**: CSV file processing (`csv_handler.py`)

### Production Features
- **Atomic Operations**: Safe file writing (`atomic_writer.py`)
- **Checkpointing**: Resume on failure (`checkpoint.py`)
- **Rate Limiting**: API throttling (`rate_limiter.py`)
- **Deduplication**: Remove duplicates (`deduplicator.py`)
- **Publishing**: HuggingFace integration (`publisher.py`)

### Error Handling
- **Exceptions**: Custom exception classes (`exceptions.py`)
- **Error Handler**: User-friendly messages (`error_handler.py`)

### Documentation (`docs/`)
- **User Guides**: Complete documentation
- **Examples**: Code samples and recipes
- **Maintainer Docs**: Internal documentation

### Testing (`tests/`)
- **Unit Tests**: Component testing
- **Integration Tests**: End-to-end testing
- **Fixtures**: Test data and mocks

## 📦 Package Exports

The main package exports (from `__init__.py`):
- `DatasetGenerator` - Core generation class
- `generate_from_description` - Generate from text
- `generate_from_document` - Generate from files
- `generate_from_excel` - Generate from Excel
- `Session` - Context manager for generation
- `__version__` - Package version

## 🔐 Environment Variables

Required:
- `OPENROUTER_API_KEY` - API access key

Optional:
- `OPENROUTER_MODEL` - Model selection
- `HF_TOKEN` - HuggingFace token
- `DATA4AI_OUTPUT_DIR` - Output directory
- `DEFAULT_SCHEMA` - Default dataset format

## 📝 Configuration Files

- `pyproject.toml` - Package metadata and dependencies
- `.env.example` - Environment template
- `.gitignore` - Version control exclusions
- `.pre-commit-config.yaml` - Code quality hooks
