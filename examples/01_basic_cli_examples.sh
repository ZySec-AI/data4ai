#!/bin/bash
# Basic CLI Examples for Data4AI
# These examples demonstrate core functionality using the command-line interface

echo "🚀 Data4AI Basic CLI Examples"
echo "=============================="

# Check environment setup
echo "📋 Checking environment..."
data4ai env

echo ""
echo "🎯 Basic Generation Examples"
echo "----------------------------"

# Example 1: Simple prompt-based generation
echo "Example 1: Generate 10 cooking recipes"
data4ai prompt \
  --repo cooking-recipes \
  --description "Create 10 detailed cooking recipes with ingredients and instructions" \
  --count 10 \
  --dry-run

# Example 2: Use specific model
echo "Example 2: Generate math problems with specific model"
data4ai prompt \
  --repo math-problems \
  --description "Create grade school math word problems" \
  --model "openai/gpt-4o-mini" \
  --count 25 \
  --dry-run

# Example 3: Generate with high creativity
echo "Example 3: Creative story generation"
data4ai prompt \
  --repo creative-stories \
  --description "Create short fantasy adventure stories" \
  --temperature 0.9 \
  --count 15 \
  --dry-run

# Example 4: Reproducible results with seed
echo "Example 4: Reproducible programming questions"
data4ai prompt \
  --repo programming-qa \
  --description "Create Python programming interview questions" \
  --seed 42 \
  --count 50 \
  --dry-run

echo ""
echo "🎓 Taxonomy Examples"
echo "-------------------"

# Example 5: Basic level (Remember & Understand)
echo "Example 5: Basic level questions"
data4ai prompt \
  --repo python-basics \
  --description "Basic Python concepts for beginners" \
  --taxonomy basic \
  --count 30 \
  --dry-run

# Example 6: Advanced level (Analyze, Evaluate & Create)
echo "Example 6: Advanced level questions"
data4ai prompt \
  --repo architecture-advanced \
  --description "Advanced software architecture patterns" \
  --taxonomy advanced \
  --count 30 \
  --dry-run

# Example 7: Balanced distribution
echo "Example 7: Balanced taxonomy distribution"
data4ai prompt \
  --repo complete-curriculum \
  --description "Complete programming curriculum" \
  --taxonomy balanced \
  --count 100 \
  --dry-run

echo ""
echo "📊 Schema Examples"
echo "-----------------"

# Example 8: Alpaca format (default)
echo "Example 8: Alpaca format (instruction-following)"
data4ai prompt \
  --repo python-tutorials \
  --description "Python programming tutorials and examples" \
  --dataset alpaca \
  --count 25 \
  --dry-run

# Example 9: ChatML format (conversations)
echo "Example 9: ChatML format (conversations)"
data4ai prompt \
  --repo customer-support \
  --description "Customer support conversations" \
  --dataset chatml \
  --count 25 \
  --dry-run

echo ""
echo "⚙️ Advanced Options"
echo "------------------"

# Example 10: Custom batch processing
echo "Example 10: Large dataset with batch processing"
data4ai prompt \
  --repo large-dataset \
  --description "Programming tutorials and examples" \
  --count 500 \
  --batch-size 5 \
  --dry-run

# Example 11: Disable DSPy for faster generation
echo "Example 11: Static generation without DSPy optimization"
data4ai prompt \
  --repo static-dataset \
  --description "Quick programming questions" \
  --count 50 \
  --no-use-dspy \
  --dry-run

echo ""
echo "✅ Examples completed!"
echo "💡 To run these examples for real, remove the --dry-run flag"
echo "📁 Generated datasets will be saved in the 'data/' directory"
echo "🔧 Use 'data4ai push --repo <repo-name>' to publish to HuggingFace"