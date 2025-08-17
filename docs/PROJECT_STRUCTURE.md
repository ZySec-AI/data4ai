# Project Structure

## Default Directory Layout

When you run Data4AI commands, files are organized as follows:

```
data4ai/
├── .env                    # Your API keys (gitignored)
├── .env.example            # Template for environment variables
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

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your API keys
```

The `.env` file is gitignored for security.

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