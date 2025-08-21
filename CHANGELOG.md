# Changelog

All notable changes to this project will be documented in this file.

## [0.2.3] - 2025-08-21

### 📊 Analysis & Optimization Release

#### New Features
- **Performance Analysis**: Comprehensive codebase analysis and optimization recommendations
- **Architecture Review**: Detailed review of current implementation with improvement suggestions
- **Recommendation Report**: Added `recommendation.md` with specific performance and scalability improvements

#### Technical Improvements
- **Import Optimization**: Lazy loading for DatasetGenerator to reduce startup time
- **Documentation Cleanup**: Removed references to non-existent schemas and commands
- **Code Quality**: Enhanced modular architecture analysis

#### Documentation
- Added comprehensive performance benchmarks and optimization strategies
- Detailed architectural analysis with concrete improvement examples
- Implementation priority guidelines for future development

## [0.2.0] - 2025-08-17

### 🚀 Advanced Document Generation & Quality Features

#### Major New Features
- **Budget-Based Generation**: New `doc-plan-generate` command with token budget allocation
- **Document-Level Planning**: Intelligent analysis and section-based example allocation
- **DSPy-Only for Documents**: Removed static prompts, all document generation now uses DSPy
- **Bloom's Taxonomy Integration**: Cognitive diversity with balanced/basic/advanced options
- **Quality Verification**: Optional verification pass for answer accuracy
- **Provenance Tracking**: Include source references with character offsets
- **Long-Context Processing**: Merge chunks for better coherence
- **PDF to Markdown Conversion**: Convert PDFs before processing for better quality
- **Folder Processing**: Process entire folders of documents recursively
- **ChatML as Default**: Changed default schema from Alpaca to ChatML

#### CLI Enhancements
- Added `doc-plan-generate` command for budget-based generation
- Added `pdf-to-markdown` command for PDF conversion
- Added quality flags: `--taxonomy`, `--provenance`, `--verify`, `--long-context`
- Added `--chunk-tokens` for token-based chunking
- Added `--file-types` for filtering document types in folders
- Added `--dry-run` for previewing operations

#### Technical Improvements
- Strict JSON-only system messages for reliability
- Dynamic count allocation (no fixed N in prompts)
- Document-level context understanding
- Section-based concept extraction
- Enhanced error messages and recovery
- Better token budget management

#### Documentation
- Comprehensive feature documentation
- Advanced generation guide
- Updated examples and tutorials
- API reference improvements

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
