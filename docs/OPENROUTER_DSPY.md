# OpenRouter DSPy Integration

This document explains how to use the OpenRouter DSPy integration in data4ai.

## Overview

The OpenRouter DSPy integration allows you to use OpenRouter models with DSPy for dynamic prompt generation and optimization. This is based on a workaround since DSPy doesn't natively support OpenRouter.

## Features

- ✅ **Direct OpenRouter API Integration**: Uses OpenRouter's API directly with proper attribution
- ✅ **Rate Limiting**: Built-in rate limiting to respect API limits
- ✅ **DSPy Compatibility**: Full compatibility with DSPy's LM interface
- ✅ **Fallback Support**: Graceful fallback to static prompts if DSPy fails
- ✅ **Error Handling**: Comprehensive error handling and logging

## Installation

The OpenRouter DSPy integration is included with data4ai. Make sure you have the required dependencies:

```bash
pip install data4ai[all]
```

## Configuration

### Environment Variables

Set your OpenRouter API key:

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-api-key-here"
```

### Optional Configuration

You can also configure additional settings:

```bash
export OPENROUTER_MODEL="openai/gpt-4o-mini:free"
export SITE_URL="https://www.zysec.ai"
export SITE_NAME="Data4AI"
```

## Usage

### Basic Usage

```python
from data4ai.integrations.openrouter_dspy import (
    OpenRouterDSPyClient,
    configure_dspy_with_openrouter,
    OpenRouterPromptOptimizer,
    create_openrouter_prompt_generator,
)

# Method 1: Direct client usage
client = OpenRouterDSPyClient(
    api_key="your-api-key",
    model="openai/gpt-4o-mini:free"
)

response = client("Hello! Can you help me create a dataset?")
print(response[0])  # First response

# Method 2: Configure DSPy globally
configure_dspy_with_openrouter(
    model="openai/gpt-4o-mini:free",
    api_key="your-api-key"
)

# Method 3: Use the prompt optimizer
optimizer = OpenRouterPromptOptimizer(
    model="openai/gpt-4o-mini:free",
    api_key="your-api-key"
)

prompt = optimizer.generate_dynamic_prompt(
    description="Create a dataset for teaching basic math",
    schema_name="alpaca",
    count=5
)

# Method 4: Factory function
generator = create_openrouter_prompt_generator(
    model="openai/gpt-4o-mini:free",
    api_key="your-api-key"
)
```

### Integration with Data4AI Generator

The OpenRouter DSPy integration is automatically used when you enable DSPy in the main generator:

```python
from data4ai.generator import DatasetGenerator

# This will automatically use OpenRouter DSPy if available
generator = DatasetGenerator(
    api_key="your-openrouter-api-key",
    model="openai/gpt-4o-mini:free"
)

# The generator will use OpenRouter DSPy for prompt generation
```

### CLI Usage

Enable DSPy with the CLI:

```bash
# Generate dataset with DSPy (uses OpenRouter if available)
data4ai prompt --use-dspy --description "Create math problems" --count 10

# Run with DSPy enabled
data4ai run --use-dspy input.xlsx
```

## API Reference

### OpenRouterDSPyClient

The main client class that implements DSPy's LM interface.

```python
class OpenRouterDSPyClient(dspy.LM):
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "openai/gpt-4o-mini:free",
        extra_headers: Optional[dict[str, str]] = None,
        site_url: str = "https://www.zysec.ai",
        site_name: str = "Data4AI",
        **kwargs,
    ):
        """Initialize OpenRouter DSPy client."""
```

**Parameters:**
- `api_key`: Your OpenRouter API key (or set OPENROUTER_API_KEY env var)
- `base_url`: OpenRouter API base URL
- `model`: Model to use (default: openai/gpt-4o-mini:free)
- `extra_headers`: Additional headers to send with requests
- `site_url`: Your site URL for attribution
- `site_name`: Your site name for attribution

### OpenRouterPromptOptimizer

A prompt optimizer that uses OpenRouter with DSPy.

```python
class OpenRouterPromptOptimizer:
    def __init__(
        self,
        model: str = "openai/gpt-4o-mini:free",
        api_key: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the prompt optimizer."""
```

**Methods:**
- `generate_dynamic_prompt()`: Generate prompts using DSPy
- `generate_schema_prompt()`: Generate schema-aware prompts
- `generate_adaptive_prompt()`: Generate adaptive prompts with examples
- `_fallback_prompt()`: Fallback to static prompts

### Factory Functions

```python
def configure_dspy_with_openrouter(
    model: str = "openai/gpt-4o-mini:free",
    api_key: Optional[str] = None,
    site_url: str = "https://www.zysec.ai",
    site_name: str = "Data4AI",
    **kwargs,
) -> None:
    """Configure DSPy to use OpenRouter."""

def create_openrouter_prompt_generator(
    model: str = "openai/gpt-4o-mini:free",
    api_key: Optional[str] = None,
    **kwargs,
) -> OpenRouterPromptOptimizer:
    """Create an OpenRouter-based prompt generator."""
```

## Rate Limiting

The integration includes built-in rate limiting:

- **Default**: 40 calls per 60 seconds
- **Configurable**: You can adjust these limits
- **Automatic**: Handles rate limit errors gracefully

## Error Handling

The integration includes comprehensive error handling:

- **API Errors**: Handles OpenRouter API errors
- **Network Errors**: Handles network timeouts and connection issues
- **DSPy Errors**: Falls back to static prompts if DSPy fails
- **Rate Limiting**: Automatically handles rate limit responses

## Examples

See `examples/openrouter_dspy_integration.py` for complete examples.

## Troubleshooting

### Common Issues

1. **API Key Not Set**
   ```
   ValueError: OpenRouter API key is required
   ```
   Solution: Set your `OPENROUTER_API_KEY` environment variable.

2. **Rate Limit Exceeded**
   ```
   RateLimitExceeded: Rate limit exceeded
   ```
   Solution: Wait for the rate limit window to reset or reduce request frequency.

3. **DSPy Import Error**
   ```
   ImportError: No module named 'dspy'
   ```
   Solution: Install DSPy: `pip install dspy-ai`

4. **Model Not Found**
   ```
   HTTPError: 404 Not Found
   ```
   Solution: Check that the model name is correct and available on OpenRouter.

### Debug Mode

Enable debug logging to see detailed API requests:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

The OpenRouter DSPy integration is based on the workaround from:
https://gist.githubusercontent.com/yash98/15753a7f2df1368a2e53825d37cb434b/raw/54e8e17e461dae7b389070f0f6493a2a989e542f/openrouter_dspy.py

Feel free to contribute improvements and bug fixes!
