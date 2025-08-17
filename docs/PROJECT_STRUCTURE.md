# Project Structure

## Default Directory Layout

When you run Data4AI commands, files are organized as follows:

```
data4ai/
├── setup_env.sh            # Interactive environment setup script
├── .env.example            # Example environment variables (reference only)
├── outputs/                # Default output directory (gitignored)
│   ├── my-dataset/         # Each dataset in its own folder
│   │   ├── data.jsonl      # Generated dataset
│   │   └── metadata.json   # Generation metadata
│   └── another-dataset/
│       ├── data.jsonl
│       └── metadata.json
└── .data4ai_checkpoint/    # Checkpoint files for resume (gitignored)
    └── checkpoint_*.json
```

## Output Directory

By default, all generated datasets are saved to `outputs/` which is:
- Created automatically when you run commands
- Ignored by git (in .gitignore)
- Can be changed via `DATA4AI_OUTPUT_DIR` environment variable

## Examples

```bash
# This command:
data4ai prompt --repo my-dataset --description "..." --count 10

# Creates:
outputs/
└── my-dataset/
    ├── data.jsonl      # Your generated dataset
    └── metadata.json   # Generation details
```

## Environment Configuration

Data4AI uses environment variables from your terminal session:

```bash
# Method 1: Direct export in terminal
export OPENROUTER_API_KEY="your_key_here"
export HF_TOKEN="your_huggingface_token"  # Optional

# Method 2: Use the interactive setup script
source setup_env.sh

# Method 3: Add to your shell config for persistence
echo 'export OPENROUTER_API_KEY="your_key_here"' >> ~/.bashrc
source ~/.bashrc

# Verify your setup
data4ai env --check
```

**Important:** Data4AI reads environment variables directly from your terminal.
No .env files are used - this is more secure and follows best practices.

## Checkpoint System

When generating large datasets, checkpoints are automatically saved:
- Location: `.data4ai_checkpoint/`
- Format: `checkpoint_<session-id>.json`
- Automatically cleaned up after successful completion
- Allows resuming interrupted generations

## File Types

- **`.jsonl`** - Dataset files in JSON Lines format
- **`.xlsx`** - Excel templates for data input
- **`.csv`** - CSV templates for data input
- **`.json`** - Metadata and checkpoint files

All output files are gitignored by default to prevent accidental commits of generated data.