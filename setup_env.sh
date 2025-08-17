#!/bin/bash
# Data4AI Environment Setup Script
# Source this file to set up your environment variables for Data4AI
# Usage: source setup_env.sh

echo "🚀 Data4AI Environment Setup"
echo "============================"
echo ""

# Function to prompt for a value with a description
prompt_for_value() {
    local var_name=$1
    local description=$2
    local help_url=$3
    local current_value="${!var_name}"
    
    if [ -n "$current_value" ]; then
        echo "✅ $var_name is already set"
        return 0
    fi
    
    echo "📝 $description"
    echo "   Get your key from: $help_url"
    echo -n "   Enter your $var_name: "
    read -r value
    
    if [ -n "$value" ]; then
        export "$var_name=$value"
        echo "   ✅ $var_name has been set for this session"
    else
        echo "   ⚠️  Skipped $var_name"
    fi
    echo ""
}

# Check and prompt for OpenRouter API Key
prompt_for_value "OPENROUTER_API_KEY" \
    "OpenRouter API key for model access (required)" \
    "https://openrouter.ai/keys"

# Check and prompt for OpenRouter Model (optional)
if [ -z "$OPENROUTER_MODEL" ]; then
    echo "📝 OpenRouter Model (optional, press Enter to use default)"
    echo "   Default: openai/gpt-4o-mini"
    echo "   Popular options: openai/gpt-4o-mini, anthropic/claude-3-5-sonnet"
    echo -n "   Enter your OPENROUTER_MODEL: "
    read -r model
    
    if [ -n "$model" ]; then
        export OPENROUTER_MODEL="$model"
        echo "   ✅ OPENROUTER_MODEL has been set to: $model"
    else
        echo "   ℹ️  Using default model: openai/gpt-4o-mini"
    fi
    echo ""
else
    echo "✅ OPENROUTER_MODEL is already set to: $OPENROUTER_MODEL"
    echo ""
fi

# Check and prompt for HuggingFace Token (optional)
echo "📝 HuggingFace Token (optional, needed for publishing datasets)"
echo "   Press Enter to skip if you don't plan to publish to HuggingFace"
prompt_for_value "HF_TOKEN" \
    "HuggingFace token for dataset publishing" \
    "https://huggingface.co/settings/tokens"

# Summary
echo "📊 Environment Status:"
echo "----------------------"
[ -n "$OPENROUTER_API_KEY" ] && echo "✅ OPENROUTER_API_KEY is set" || echo "❌ OPENROUTER_API_KEY is not set"
[ -n "$OPENROUTER_MODEL" ] && echo "✅ OPENROUTER_MODEL is set to: $OPENROUTER_MODEL" || echo "ℹ️  OPENROUTER_MODEL will use default"
[ -n "$HF_TOKEN" ] && echo "✅ HF_TOKEN is set" || echo "ℹ️  HF_TOKEN is not set (publishing disabled)"

echo ""
echo "⚠️  Note: These environment variables are only set for this terminal session."
echo ""
echo "💡 To make them permanent, add these lines to your ~/.bashrc or ~/.zshrc:"
echo ""
[ -n "$OPENROUTER_API_KEY" ] && echo "export OPENROUTER_API_KEY=\"$OPENROUTER_API_KEY\""
[ -n "$OPENROUTER_MODEL" ] && echo "export OPENROUTER_MODEL=\"$OPENROUTER_MODEL\""
[ -n "$HF_TOKEN" ] && echo "export HF_TOKEN=\"$HF_TOKEN\""
echo ""
echo "✨ Setup complete! You can now use data4ai commands."
echo "   Try: data4ai env --check"