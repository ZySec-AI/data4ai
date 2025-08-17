# 🔧 Environment Setup Guide

Data4AI uses environment variables for configuration. This guide covers all setup methods and best practices.

## 📋 Required Environment Variables

| Variable | Required | Description | How to Get |
|----------|----------|-------------|------------|
| `OPENROUTER_API_KEY` | ✅ Yes | API key for accessing AI models | [OpenRouter Keys](https://openrouter.ai/keys) |
| `OPENROUTER_MODEL` | ❌ No | Model to use (default: `openai/gpt-4o-mini`) | [Model List](https://openrouter.ai/models) |
| `HF_TOKEN` | ❌ No | HuggingFace token for publishing datasets | [HF Tokens](https://huggingface.co/settings/tokens) |

## 🚀 Setup Methods

### Method 1: Quick Setup (Testing/Development)

Set variables for your current terminal session:

```bash
# Set your API key
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Optional: Choose a specific model
export OPENROUTER_MODEL="openai/gpt-4o-mini"

# Optional: Set HuggingFace token for publishing
export HF_TOKEN="hf_your-token-here"

# Verify setup
data4ai env --check
```

⚠️ **Note:** These variables are only set for your current terminal session. They will be lost when you close the terminal.

### Method 2: Interactive Setup

Use our interactive setup script for guided configuration:

```bash
# Run the setup script
source setup_env.sh

# Follow the prompts to enter your keys
# The script will show you how to make them permanent
```

### Method 3: Permanent Setup

Add variables to your shell configuration file:

#### For Bash (Linux/WSL)
```bash
# Add to ~/.bashrc
echo 'export OPENROUTER_API_KEY="sk-or-v1-your-key-here"' >> ~/.bashrc
echo 'export HF_TOKEN="hf_your-token-here"' >> ~/.bashrc

# Reload configuration
source ~/.bashrc
```

#### For Zsh (macOS/Modern Linux)
```bash
# Add to ~/.zshrc
echo 'export OPENROUTER_API_KEY="sk-or-v1-your-key-here"' >> ~/.zshrc
echo 'export HF_TOKEN="hf_your-token-here"' >> ~/.zshrc

# Reload configuration
source ~/.zshrc
```

#### For Fish Shell
```fish
# Add to ~/.config/fish/config.fish
set -x OPENROUTER_API_KEY "sk-or-v1-your-key-here"
set -x HF_TOKEN "hf_your-token-here"

# Reload configuration
source ~/.config/fish/config.fish
```

## 🔍 Checking Your Environment

### Check Current Status
```bash
# Show environment status with table
data4ai env --check
```

Example output when configured:
```
                 Environment Status                 
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Variable           ┃ Status ┃ Value               ┃ Required ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ OPENROUTER_API_KEY │ ✅     │ ***                 │ Yes      │
│ OPENROUTER_MODEL   │ ✅     │ openai/gpt-4o-mini  │ No       │
│ HF_TOKEN           │ ✅     │ ***                 │ No       │
└────────────────────┴────────┴─────────────────────┴──────────┘

✅ All environment variables are configured!
🔒 Your API keys are properly set in this terminal session
```

### Show Export Commands
```bash
# Display export commands for missing variables
data4ai env --export
```

## 🔒 Security Best Practices

### DO ✅
- Store API keys in environment variables
- Use different keys for development and production
- Add API keys to your shell config file (with proper permissions)
- Keep your shell config files private (`chmod 600 ~/.bashrc`)

### DON'T ❌
- Commit API keys to version control
- Share your API keys in documentation
- Use API keys in command arguments (they appear in shell history)
- Store keys in plain text files in your project

## 🧪 Testing Your Setup

### Test API Key
```bash
# Dry run to test configuration
data4ai prompt --repo test --description "test" --count 1 --dry-run
```

### Test Model Access
```bash
# List available models (requires valid API key)
data4ai list-models
```

### Test HuggingFace Token
```bash
# Only needed if you plan to publish datasets
# This will fail gracefully if token is not set
data4ai push --repo test-dataset --private
```

## 🔄 Switching Between Configurations

### Using Different Models
```bash
# Temporarily use a different model
OPENROUTER_MODEL="anthropic/claude-3-5-sonnet" data4ai prompt --repo test --description "test" --count 1

# Or export for the session
export OPENROUTER_MODEL="anthropic/claude-3-5-sonnet"
```

### Using Different API Keys
```bash
# For different projects or environments
export OPENROUTER_API_KEY="sk-or-v1-project-specific-key"
```

## 🐳 Docker/Container Setup

When using Data4AI in containers:

```dockerfile
# Dockerfile
FROM python:3.9

# Install data4ai
RUN pip install data4ai[all]

# Set environment variables (use build args for security)
ARG OPENROUTER_API_KEY
ENV OPENROUTER_API_KEY=$OPENROUTER_API_KEY
```

Build with:
```bash
docker build --build-arg OPENROUTER_API_KEY="$OPENROUTER_API_KEY" -t data4ai .
```

## 🔧 CI/CD Setup

### GitHub Actions
```yaml
- name: Generate Dataset
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    HF_TOKEN: ${{ secrets.HF_TOKEN }}
  run: |
    pip install data4ai[all]
    data4ai prompt --repo dataset --description "..." --count 100
```

### GitLab CI
```yaml
generate-dataset:
  script:
    - pip install data4ai[all]
    - data4ai prompt --repo dataset --description "..." --count 100
  variables:
    OPENROUTER_API_KEY: $OPENROUTER_API_KEY
    HF_TOKEN: $HF_TOKEN
```

## ❓ Troubleshooting

### "Missing environment variables detected"
```bash
# Check which variables are missing
data4ai env --check

# Show commands to set them
data4ai env --export
```

### "API key not configured"
```bash
# Verify the variable is set
echo $OPENROUTER_API_KEY

# If empty, set it
export OPENROUTER_API_KEY="your-key-here"
```

### Variables not persisting
```bash
# Make sure you're editing the right file
echo $SHELL  # Shows your shell

# Add to the correct config file
# ~/.bashrc for bash
# ~/.zshrc for zsh
# ~/.profile for general
```

### Permission denied errors
```bash
# Check file permissions
ls -la ~/.bashrc

# Fix permissions if needed
chmod 644 ~/.bashrc
```

## 📚 Additional Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Environment Variables Guide](https://www.gnu.org/software/bash/manual/html_node/Environment.html)
- [Shell Configuration Files](https://www.gnu.org/software/bash/manual/html_node/Bash-Startup-Files.html)