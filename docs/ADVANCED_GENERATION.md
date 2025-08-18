# Advanced Generation with Budget-Based Planning

## Overview

The `doc-plan-generate` command uses an advanced AI pipeline that creates better quality datasets through intelligent planning and budget-based allocation.

## Key Differences from Traditional Generation

### Traditional (`doc-to-dataset`)
- Fixed count: You specify exactly N examples
- Chunk-based: Processes document in fixed-size chunks
- Even distribution: Same number of examples per chunk
- Static prompts: Uses predefined prompt templates

### New Advanced Pipeline (`doc-plan-generate`)
- Budget-based: Token budget drives example count
- Document-level: Analyzes entire document context
- Smart allocation: More examples for important sections
- Dynamic prompts: AI optimizes prompts for each document

## Usage

### Basic Command

```bash
data4ai doc-plan-generate document.pdf \
  --repo my-dataset \
  --token-budget 10000
```

### With Quality Options

```bash
data4ai doc-plan-generate document.pdf \
  --repo my-dataset \
  --token-budget 10000 \
  --min-examples 20 \
  --max-examples 100 \
  --taxonomy balanced \
  --difficulty balanced
```

## Parameters

### Required
- `input_path`: Document or folder to process
- `--repo`: Output directory name
- `--token-budget`: Total tokens to spend on generation

### Optional
- `--min-examples`: Soft minimum examples (default: 10)
- `--max-examples`: Soft maximum examples (default: 100)
- `--taxonomy`: Bloom's taxonomy distribution
  - `balanced`: All cognitive levels
  - `basic`: Focus on Remember/Understand
  - `advanced`: Focus on Analyze/Evaluate/Create
- `--difficulty`: Difficulty distribution
  - `balanced`: Mix of easy/medium/hard
  - `easy`: Simpler examples
  - `hard`: Challenging examples
- `--dataset`: Schema format (default: chatml)
- `--advanced`: Use advanced text extraction
- `--dry-run`: Preview without generating

## How It Works

### 1. Planning Phase
The system analyzes your document and creates a generation plan:
- Identifies key sections and concepts
- Allocates examples based on section importance
- Plans taxonomy distribution across sections
- Estimates token usage

### 2. Generation Phase
Following the plan, it generates examples:
- Uses full document context (not chunks)
- Dynamically adjusts counts within budget
- Maintains taxonomy and difficulty targets
- Ensures grounding in document content

### 3. Output
Creates a dataset with:
- `data.jsonl`: The generated examples
- `metadata.json`: Plan, metrics, and configuration

## Example Workflow

```bash
# 1. Preview with dry-run
data4ai doc-plan-generate research_paper.pdf \
  --repo research-qa \
  --token-budget 5000 \
  --dry-run

# 2. Generate with balanced taxonomy
data4ai doc-plan-generate research_paper.pdf \
  --repo research-qa \
  --token-budget 5000 \
  --taxonomy balanced

# 3. Check results
data4ai stats --repo research-qa
```

## Token Budget Guidelines

- **Small document (1-5 pages)**: 5,000-10,000 tokens
- **Medium document (5-20 pages)**: 10,000-20,000 tokens
- **Large document (20+ pages)**: 20,000-50,000 tokens
- **Folder of documents**: 50,000+ tokens

## Quality Features

### Bloom's Revised Taxonomy
Ensures cognitive diversity in questions:
- **Remember**: Basic recall (What, When, Who)
- **Understand**: Comprehension (Explain, Summarize)
- **Apply**: Using knowledge (How would you)
- **Analyze**: Breaking down (Compare, Contrast)
- **Evaluate**: Judging (Critique, Justify)
- **Create**: Synthesizing (Design, Propose)

### Dynamic Allocation
The plan allocates more examples to:
- Sections with rich content
- Areas with key concepts
- Parts matching your taxonomy goals

## Tips for Best Results

1. **Start with dry-run** to preview the plan
2. **Use appropriate budgets** - more tokens = better quality
3. **Set taxonomy goals** for educational datasets
4. **Process similar documents together** for consistency
5. **Review the metadata.json** to understand allocations

## Comparison with Legacy Command

| Feature | `doc-to-dataset` | `doc-plan-generate` |
|---------|-----------------|-------------------|
| Control | Fixed count | Token budget |
| Context | Chunks | Full document |
| Planning | None | Intelligent plan |
| Allocation | Even | Dynamic |
| Taxonomy | Optional | Built-in |
| AI Optimization | Optional | Always enabled |
| Best for | Quick generation | Quality datasets |

## Troubleshooting

### "API key required"
Set your OpenRouter API key:
```bash
export OPENROUTER_API_KEY="your-key-here"
```

### "Budget too small"
Increase `--token-budget` or reduce `--max-examples`

### "Plan failed"
The document might be too short or unclear. Try:
- Using `--advanced` extraction
- Adjusting min/max examples
- Checking document format

## Next Steps

- Monitor costs with token budgets
- Experiment with taxonomy settings
- Use metadata for quality analysis
- Combine with verification (`--verify` coming soon)