#!/bin/bash
# Document Processing Examples for Data4AI
# These examples demonstrate how to generate datasets from various document types

echo "📄 Data4AI Document Processing Examples"
echo "======================================="

# Check environment setup
echo "📋 Checking environment..."
data4ai env

echo ""
echo "📝 Supported Document Types"
echo "--------------------------"
echo "• PDF files (.pdf)"
echo "• Microsoft Word documents (.docx)"
echo "• Markdown files (.md)"
echo "• Plain text files (.txt)"
echo "• Directories containing multiple documents"

echo ""
echo "📖 Single Document Examples"
echo "---------------------------"

# Create sample documents for demonstration
echo "Creating sample documents..."

# Sample markdown document
cat > sample_tutorial.md << 'EOF'
# Python Programming Tutorial

## Introduction
Python is a versatile programming language known for its simplicity and readability.

## Variables and Data Types
```python
name = "Alice"
age = 30
height = 5.6
is_student = True
```

## Functions
```python
def greet(name):
    return f"Hello, {name}!"

result = greet("World")
print(result)
```

## Classes
```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def introduce(self):
        return f"I'm {self.name}, {self.age} years old"
```

## Best Practices
- Use meaningful variable names
- Write clear comments
- Follow PEP 8 style guidelines
- Test your code regularly
EOF

# Sample text document
cat > research_notes.txt << 'EOF'
Machine Learning Research Notes

1. Supervised Learning
   - Uses labeled training data
   - Examples: classification, regression
   - Algorithms: linear regression, decision trees, neural networks

2. Unsupervised Learning
   - Works with unlabeled data
   - Examples: clustering, dimensionality reduction
   - Algorithms: k-means, PCA, autoencoders

3. Reinforcement Learning
   - Learns through interaction with environment
   - Uses reward/punishment system
   - Applications: game playing, robotics, autonomous vehicles

4. Deep Learning
   - Subset of machine learning using neural networks
   - Excellent for image recognition, natural language processing
   - Requires large amounts of data and computational power
EOF

echo "Sample documents created!"

echo ""
echo "📄 Example 1: Generate from Markdown Tutorial"
data4ai doc sample_tutorial.md \
  --repo python-tutorial-qa \
  --description "Python programming Q&A from tutorial content" \
  --count 50 \
  --dry-run

echo ""
echo "📄 Example 2: Generate Conversations from Text Notes"
data4ai doc research_notes.txt \
  --repo ml-research-chat \
  --description "Machine learning research discussions" \
  --dataset chatml \
  --count 30 \
  --dry-run

echo ""
echo "🎓 Example 3: Basic Level Questions from Tutorial"
data4ai doc sample_tutorial.md \
  --repo python-basics \
  --description "Basic Python programming concepts" \
  --taxonomy basic \
  --count 40 \
  --dry-run

echo ""
echo "🧠 Example 4: Advanced Analysis from Research Notes"
data4ai doc research_notes.txt \
  --repo ml-advanced \
  --description "Advanced machine learning concepts and analysis" \
  --taxonomy advanced \
  --count 35 \
  --dry-run

echo ""
echo "📁 Multiple Document Examples"
echo "-----------------------------"

# Create a documents directory with multiple files
mkdir -p sample_docs

# Create additional sample documents
cat > sample_docs/intro_to_ai.md << 'EOF'
# Introduction to Artificial Intelligence

AI is the simulation of human intelligence in machines that are programmed to think and learn.

## Types of AI
- Narrow AI: Designed for specific tasks
- General AI: Human-level intelligence across domains
- Superintelligence: Exceeds human intelligence

## Applications
- Natural Language Processing
- Computer Vision
- Robotics
- Expert Systems
EOF

cat > sample_docs/data_structures.txt << 'EOF'
Data Structures Overview

Arrays: Fixed-size sequential collections
- Fast random access
- Limited flexibility

Linked Lists: Dynamic sequential collections
- Flexible size
- Sequential access only

Trees: Hierarchical structures
- Binary trees, AVL trees, B-trees
- Efficient searching and sorting

Hash Tables: Key-value mappings
- Average O(1) access time
- Potential for collisions
EOF

cat > sample_docs/algorithms.md << 'EOF'
# Common Algorithms

## Sorting Algorithms
- **Bubble Sort**: O(n²) time complexity
- **Quick Sort**: O(n log n) average case
- **Merge Sort**: O(n log n) guaranteed

## Search Algorithms
- **Linear Search**: O(n) time complexity
- **Binary Search**: O(log n) for sorted arrays

## Graph Algorithms
- **BFS**: Breadth-first search
- **DFS**: Depth-first search
- **Dijkstra**: Shortest path algorithm
EOF

echo "Sample document collection created!"

echo ""
echo "📁 Example 5: Generate from Document Directory"
data4ai doc sample_docs/ \
  --repo computer-science-qa \
  --description "Computer science concepts Q&A" \
  --count 100 \
  --dry-run

echo ""
echo "📁 Example 6: Balanced Taxonomy from Multiple Documents"
data4ai doc sample_docs/ \
  --repo cs-balanced \
  --description "Comprehensive computer science curriculum" \
  --taxonomy balanced \
  --count 150 \
  --dry-run

echo ""
echo "📁 Example 7: Conversation Format from Documentation"
data4ai doc sample_docs/ \
  --repo cs-discussions \
  --description "Computer science concept discussions" \
  --dataset chatml \
  --count 80 \
  --dry-run

echo ""
echo "⚙️ Advanced Processing Examples"
echo "------------------------------"

echo ""
echo "📄 Example 8: Custom Model and Temperature"
data4ai doc sample_tutorial.md \
  --repo creative-python \
  --description "Creative Python programming examples and explanations" \
  --model "anthropic/claude-3-5-sonnet" \
  --temperature 0.8 \
  --count 40 \
  --dry-run

echo ""
echo "📄 Example 9: Large-scale Processing with Batching"
data4ai doc sample_docs/ \
  --repo large-cs-dataset \
  --description "Comprehensive computer science knowledge base" \
  --count 500 \
  --batch-size 10 \
  --dry-run

echo ""
echo "📄 Example 10: Document Processing with Specific Schema"
data4ai doc research_notes.txt \
  --repo ml-instructions \
  --description "Machine learning instruction dataset" \
  --dataset alpaca \
  --count 60 \
  --dry-run

echo ""
echo "🔍 Filtering Examples"
echo "--------------------"

echo ""
echo "📄 Example 11: Process Only Markdown Files"
# Note: This would typically use glob patterns or file filtering
# For demonstration, showing the concept
echo "# Process only .md files from a directory:"
echo "data4ai doc sample_docs/*.md --repo markdown-only --count 50"

echo ""
echo "📄 Example 12: Process Specific File Types"
echo "# Process only .txt files:"
echo "data4ai doc sample_docs/*.txt --repo text-only --count 30"

echo ""
echo "📊 Output Examples"
echo "-----------------"

echo ""
echo "Sample outputs for different schemas:"
echo ""
echo "ALPACA format example:"
echo "{"
echo '  "instruction": "Explain what a Python function is",'
echo '  "input": "",'
echo '  "output": "A Python function is a reusable block of code..."'
echo "}"
echo ""
echo "CHATML format example:"
echo "{"
echo '  "messages": ['
echo '    {"role": "user", "content": "What is a Python function?"},'
echo '    {"role": "assistant", "content": "A Python function is..."}'
echo '  ]'
echo "}"

echo ""
echo "💡 Document Processing Tips"
echo "--------------------------"
echo "1. Use --dry-run to preview generation without creating files"
echo "2. Start with small --count values for testing"
echo "3. Choose taxonomy level based on target audience:"
echo "   • basic: Remember & Understand (beginners)"
echo "   • balanced: All cognitive levels (general use)"
echo "   • advanced: Analyze, Evaluate & Create (experts)"
echo "4. Use chatml for conversational AI training"
echo "5. Use alpaca for instruction-following models"
echo "6. Larger documents may need higher --batch-size"
echo "7. Check document encoding if you encounter errors"

echo ""
echo "🧹 Cleanup"
echo "----------"
echo "Removing sample documents..."
rm -f sample_tutorial.md research_notes.txt
rm -rf sample_docs/

echo ""
echo "✅ Document processing examples completed!"
echo "💡 To run real generation:"
echo "   1. Remove --dry-run flag"
echo "   2. Ensure your documents are ready"
echo "   3. Set appropriate count and batch-size"
echo "📤 Use 'data4ai push --repo <repo-name>' to publish results"