# 🔧 Troubleshooting Guide

Common issues and solutions for Data4AI.

## 🔑 Environment Variable Issues

### Problem: "OpenRouter API key not configured"

**Symptoms:**
```
❌ OpenRouter API key not configured.

📋 To set it in your terminal, run:
export OPENROUTER_API_KEY="your-api-key-here"
```

**Solutions:**

1. **Quick Fix (Current Session)**
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-your-actual-key"
   data4ai env --check  # Verify it's set
   ```

2. **Permanent Fix**
   ```bash
   # Add to your shell config
   echo 'export OPENROUTER_API_KEY="sk-or-v1-your-actual-key"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Interactive Setup**
   ```bash
   source setup_env.sh
   ```

### Problem: "HuggingFace token not configured"

**Symptoms:**
```
❌ HuggingFace token not configured.

📋 To set it in your terminal, run:
export HF_TOKEN="your-huggingface-token-here"
```

**Solutions:**
```bash
# Only needed for publishing to HuggingFace
export HF_TOKEN="hf_your-actual-token"

# Get token from: https://huggingface.co/settings/tokens
```

### Problem: Environment variables not persisting

**Symptoms:**
- Variables work in one terminal but not in new terminals
- Variables lost after reboot

**Solutions:**

1. **Check your shell type:**
   ```bash
   echo $SHELL
   # Output: /bin/bash, /bin/zsh, etc.
   ```

2. **Add to correct config file:**
   - Bash: `~/.bashrc` or `~/.bash_profile`
   - Zsh: `~/.zshrc`
   - Fish: `~/.config/fish/config.fish`

3. **Verify it's saved:**
   ```bash
   grep OPENROUTER ~/.bashrc  # or ~/.zshrc
   ```

### Problem: Different shell showing different variables

**Solutions:**
```bash
# Make variables available to all shells
# Add to ~/.profile (works for most shells)
echo 'export OPENROUTER_API_KEY="your-key"' >> ~/.profile

# Or set system-wide (requires sudo)
echo 'OPENROUTER_API_KEY="your-key"' | sudo tee -a /etc/environment
```

## 🚫 API Errors

### Problem: "Invalid OpenRouter API key"

**Symptoms:**
```
❌ Invalid OpenRouter API key. Please check your credentials.
```

**Solutions:**

1. **Verify key format:**
   ```bash
   # Should start with sk-or-v1-
   echo $OPENROUTER_API_KEY
   ```

2. **Test with curl:**
   ```bash
   curl https://openrouter.ai/api/v1/models \
     -H "Authorization: Bearer $OPENROUTER_API_KEY"
   ```

3. **Get a new key:**
   - Visit [OpenRouter Keys](https://openrouter.ai/keys)
   - Generate a new key
   - Update your environment

### Problem: "Rate limit exceeded"

**Symptoms:**
```
⚠️ Rate limit exceeded. Waiting before retrying...
```

**Solutions:**

1. **Reduce batch size:**
   ```bash
   data4ai prompt --repo test --batch-size 5  # Smaller batches
   ```

2. **Add delays:**
   ```bash
   # The tool handles this automatically, but you can control it
   data4ai prompt --repo test --count 10 --batch-size 1
   ```

3. **Use a different model:**
   ```bash
   # Some models have higher rate limits
   export OPENROUTER_MODEL="openai/gpt-4o-mini"
   ```

### Problem: "Model not found"

**Symptoms:**
```
❌ Model 'unknown-model' not found. Use 'data4ai list-models' to see available models.
```

**Solutions:**

1. **List available models:**
   ```bash
   data4ai list-models
   ```

2. **Use a known model:**
   ```bash
   export OPENROUTER_MODEL="openai/gpt-4o-mini"
   # Or specify in command
   data4ai prompt --model "openai/gpt-4o-mini" ...
   ```

## 📁 File and Data Issues

### Problem: "File not found"

**Solutions:**

1. **Check file path:**
   ```bash
   ls -la template.xlsx
   pwd  # Check current directory
   ```

2. **Use absolute path:**
   ```bash
   data4ai run /full/path/to/file.xlsx --repo test
   ```

### Problem: "Schema mismatch"

**Symptoms:**
```
❌ Data doesn't match alpaca schema. Missing columns: instruction, output
```

**Solutions:**

1. **Create correct template:**
   ```bash
   data4ai create-sample template.xlsx --dataset alpaca
   ```

2. **Check schema requirements:**
   - Alpaca: instruction, input, output
   - Dolly: instruction, context, response
   - ShareGPT: conversations

### Problem: Empty or corrupted output

**Solutions:**

1. **Check the output:**
   ```bash
   cat outputs/my-dataset/data.jsonl | head
   data4ai validate --repo my-dataset
   ```

2. **Regenerate with verbose mode:**
   ```bash
   data4ai prompt --repo test --description "..." --count 10 --verbose
   ```

## 🐍 Python API Issues

### Problem: Import errors

**Symptoms:**
```python
ImportError: cannot import name 'generate_from_description' from 'data4ai'
```

**Solutions:**

1. **Reinstall package:**
   ```bash
   pip uninstall data4ai
   pip install data4ai[all]
   ```

2. **Check Python path:**
   ```python
   import sys
   print(sys.path)
   import data4ai
   print(data4ai.__file__)
   ```

### Problem: Async/await issues

**Solutions:**

```python
# Wrong way
result = generate_from_description(...)  # In async context

# Right way (for async)
result = await generate_from_description_async(...)

# Or use sync version
result = generate_from_description(...)  # In sync context
```

## 🔄 Generation Issues

### Problem: Generation interrupted

**Solutions:**

1. **Resume from checkpoint:**
   ```bash
   # Checkpoints are automatic
   # Just re-run the same command
   data4ai prompt --repo my-dataset --description "..." --count 1000
   ```

2. **Check checkpoint files:**
   ```bash
   ls -la .data4ai_checkpoint/
   ```

### Problem: Poor quality outputs

**Solutions:**

1. **Adjust temperature:**
   ```bash
   # Lower = more focused (0.3-0.5)
   data4ai prompt --temperature 0.3 ...
   
   # Higher = more creative (0.8-1.0)
   data4ai prompt --temperature 0.9 ...
   ```

2. **Use better model:**
   ```bash
   export OPENROUTER_MODEL="openai/gpt-4o"
   # or
   export OPENROUTER_MODEL="anthropic/claude-3-5-sonnet"
   ```

3. **Improve description:**
   ```bash
   # Be specific and detailed
   data4ai prompt --description "Create advanced Python programming questions with detailed explanations and working code examples"
   ```

## 🖥️ System Issues

### Problem: Permission denied

**Solutions:**

1. **Check directory permissions:**
   ```bash
   ls -la outputs/
   chmod 755 outputs/
   ```

2. **Use different output directory:**
   ```bash
   export DATA4AI_OUTPUT_DIR=/tmp/data4ai_outputs
   ```

### Problem: Out of memory

**Solutions:**

1. **Reduce batch size:**
   ```bash
   data4ai run file.xlsx --batch-size 1
   ```

2. **Process in chunks:**
   ```bash
   data4ai run file.xlsx --max-rows 100
   ```

## 🆘 Getting Help

### Check your setup
```bash
# Full environment check
data4ai env --check

# Show version
data4ai version

# Verbose mode for debugging
data4ai prompt --verbose ...
```

### Report issues
- GitHub Issues: [data4ai/issues](https://github.com/ZySec-AI/data4ai/issues)
- Include:
  - Error message
  - Command used
  - Environment (OS, Python version)
  - Output of `data4ai env --check`

### Community support
- Discussions: [GitHub Discussions](https://github.com/ZySec-AI/data4ai/discussions)
- Examples: Check `examples/` directory
- Documentation: Read `docs/` folder