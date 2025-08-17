# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1] - 2024-08-17

### 🔮 DSPy Integration Release

#### New Features
- **DSPy Integration**: Dynamic prompt generation using DSPy signatures for high-quality output
- **Adaptive Prompting**: Support for few-shot learning with previous examples
- **Schema-Aware Optimization**: Different prompt strategies for different schemas
- **Fallback Support**: Automatic fallback to static prompts if DSPy fails
- **CLI Options**: Added `--use-dspy/--no-use-dspy` flags for prompt generation control

#### Enhanced Features
- **Dynamic Prompt Generation**: Replaced static prompts with DSPy-powered dynamic prompts
- **Better Error Handling**: Improved retry logic and JSON parsing
- **Configuration**: Added `DATA4AI_USE_DSPY` environment variable

## [0.1.0] - 2024-08-17

### 🎉 Initial Beta Release

#### Core Features
- **AI-Powered Generation**: Access to 100+ models via OpenRouter API
- **Multiple Input Formats**: Excel and CSV file support with auto-detection
- **Schema Support**: Alpaca, Dolly, and ShareGPT formats
- **Natural Language Input**: Generate datasets from text descriptions
- **HuggingFace Integration**: Direct dataset publishing

#### Production Features
- **Rate Limiting**: Adaptive token bucket algorithm with automatic backoff
- **Atomic Operations**: Data integrity with temp file + atomic rename pattern
- **Checkpoint/Resume**: Fault-tolerant generation with session recovery
- **Deduplication**: Multiple strategies (exact, fuzzy, content-based)
- **Progress Tracking**: Real-time metrics, progress bars, and ETA
- **Error Handling**: Comprehensive error recovery with user-friendly messages
- **Streaming I/O**: Handle large files without memory issues
- **Batch Processing**: Configurable batch sizes with memory optimization

#### CLI Commands
- `create-sample`: Create template files (Excel/CSV)
- `run`: Process files with AI completion
- `prompt`: Generate from natural language description
- `file-to-dataset`: Convert files without AI
- `push`: Publish to HuggingFace Hub
- `validate`: Validate dataset quality
- `stats`: Show dataset statistics
- `list-models`: List available models
- `config`: Manage configuration

#### Configuration
- Environment variable support via `.env` file
- Default output to `outputs/` directory (gitignored)
- Configurable models, temperature, batch size
- Site attribution for analytics
