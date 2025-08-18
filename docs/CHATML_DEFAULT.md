# ChatML as Default Schema

## Overview
As of version 0.1.3+, Data4AI uses **ChatML** as the default dataset schema. ChatML is OpenAI's standard format for chat conversations, making it the most compatible format for modern LLMs.

## What Changed?
- **Before**: Alpaca was the default schema
- **Now**: ChatML is the default schema
- **Backward Compatibility**: All existing schemas still work

## ChatML Format

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is machine learning?"},
    {"role": "assistant", "content": "Machine learning is a subset of AI..."}
  ]
}
```

## Using ChatML

### Default Usage (ChatML)
```bash
# No need to specify --dataset, ChatML is default
data4ai prompt --repo my-dataset --description "Create Python questions" --count 100
data4ai doc document.pdf --repo doc-dataset --count 50
```

### Explicit ChatML
```bash
# You can still explicitly specify ChatML
data4ai prompt --repo my-dataset --dataset chatml --description "..." --count 100
```

### Using Other Schemas
```bash
# Specify other schemas when needed
data4ai prompt --repo my-dataset --dataset alpaca --description "..." --count 100
```

## Why ChatML?

1. **Industry Standard**: Used by OpenAI, Anthropic, and most modern LLMs
2. **Flexible**: Supports system prompts, multi-turn conversations, and function calling
3. **Future-Proof**: Aligned with the direction of LLM development
4. **Better Structure**: Clear role separation (system/user/assistant)

## Migration Guide

### For Existing Users
- **No action required** if you're happy with ChatML
- To keep using Alpaca, add `--dataset alpaca` to your commands
- Set default in environment: `export DEFAULT_SCHEMA=alpaca`

### For Scripts/Automation
```python
# Python API - specify schema explicitly if needed
from data4ai import generate_from_description

# Uses ChatML by default
result = generate_from_description(
    description="...",
    repo="...",
    count=100
)

# Explicit schema selection
result = generate_from_description(
    description="...",
    repo="...",
    count=100,
    schema="alpaca"
)
```

### Environment Configuration
```bash
# Set your preferred default schema
export DEFAULT_SCHEMA=chatml  # or alpaca

# Make it permanent
echo 'export DEFAULT_SCHEMA=chatml' >> ~/.bashrc
```

## Schema Comparison

| Feature | ChatML | Alpaca |
|---------|--------|--------|
| **System Prompts** | ✅ Yes | ❌ No |
| **Multi-turn** | ✅ Yes | ❌ No |
| **OpenAI Compatible** | ✅ Yes | ⚠️ Needs conversion |
| **Anthropic Compatible** | ✅ Yes | ⚠️ Needs conversion |
| **Best For** | Modern LLMs | Llama/Alpaca models |

## FAQ

**Q: Will my existing Alpaca datasets still work?**
A: Yes! All schemas are still supported. Only the default has changed.

**Q: How do I keep using Alpaca as default?**
A: Set `DEFAULT_SCHEMA=alpaca` in your environment or use `--dataset alpaca` flag.

**Q: Which schema should I use?**
A: Use ChatML unless you have a specific reason to use another format. It's the most versatile and widely supported.

**Q: Can I convert between schemas?**
A: Yes, you can read a dataset in one format and regenerate it in another using the Python API.

## Summary

ChatML is now the default schema in Data4AI, providing better compatibility with modern LLMs while maintaining full backward compatibility with all existing schemas. No changes are required for existing workflows - just be aware that new datasets will use ChatML format by default unless you specify otherwise.