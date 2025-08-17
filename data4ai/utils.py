"""Shared utilities for Data4AI."""

import json
import logging
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

console = Console()


def setup_logging(
    level: str = "INFO", log_file: Optional[Path] = None
) -> logging.Logger:
    """Set up application logging with Rich handler."""
    logger = logging.getLogger("data4ai")
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with Rich
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
    )
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)

    return logger


def read_jsonl(file_path: Path) -> Generator[dict[str, Any], None, None]:
    """Read JSONL file and yield each entry."""
    with open(file_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logger = logging.getLogger("data4ai")
                logger.warning(f"Skipping invalid JSON at line {line_num}: {e}")


def write_jsonl(
    data: list[dict[str, Any]], file_path: Path, append: bool = False
) -> int:
    """Write data to JSONL file (now using atomic writes)."""
    from data4ai.atomic_writer import AtomicWriter

    return AtomicWriter.write_jsonl(data, file_path, append=append)


def save_metadata(
    output_dir: Path,
    schema: str,
    model: str,
    row_count: int,
    parameters: dict[str, Any],
    metrics: Optional[dict[str, Any]] = None,
) -> Path:
    """Save generation metadata to JSON file (atomically)."""
    from datetime import datetime, timezone

    from data4ai import __version__
    from data4ai.atomic_writer import AtomicWriter

    metadata = {
        "version": __version__,
        "schema": schema,
        "model": model,
        "row_count": row_count,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "parameters": parameters,
        "metrics": metrics or {},
    }

    metadata_path = output_dir / "metadata.json"
    AtomicWriter.write_json(metadata, metadata_path)

    return metadata_path


def calculate_metrics(data: list[dict[str, Any]], schema: str) -> dict[str, Any]:
    """Calculate quality metrics for generated dataset."""
    metrics = {
        "total_rows": len(data),
        "empty_rows": 0,
        "avg_instruction_length": 0,
        "avg_output_length": 0,
        "min_instruction_length": float("inf"),
        "max_instruction_length": 0,
        "min_output_length": float("inf"),
        "max_output_length": 0,
    }

    if not data:
        return metrics

    instruction_lengths = []
    output_lengths = []

    for entry in data:
        # Get instruction field based on schema
        instruction_field = "instruction" if schema != "sharegpt" else None
        output_field = {
            "alpaca": "output",
            "dolly": "response",
            "sharegpt": None,
        }.get(schema)

        if instruction_field and instruction_field in entry:
            length = len(entry[instruction_field])
            instruction_lengths.append(length)
            metrics["min_instruction_length"] = min(
                metrics["min_instruction_length"], length
            )
            metrics["max_instruction_length"] = max(
                metrics["max_instruction_length"], length
            )

        if output_field and output_field in entry:
            length = len(entry[output_field])
            output_lengths.append(length)
            metrics["min_output_length"] = min(metrics["min_output_length"], length)
            metrics["max_output_length"] = max(metrics["max_output_length"], length)

        # Check for empty entries
        if schema == "sharegpt":
            if not entry.get("conversations"):
                metrics["empty_rows"] += 1
        else:
            if not entry.get(instruction_field) or not entry.get(output_field):
                metrics["empty_rows"] += 1

    # Calculate averages
    if instruction_lengths:
        metrics["avg_instruction_length"] = sum(instruction_lengths) / len(
            instruction_lengths
        )
    if output_lengths:
        metrics["avg_output_length"] = sum(output_lengths) / len(output_lengths)

    # Fix infinity values
    if metrics["min_instruction_length"] == float("inf"):
        metrics["min_instruction_length"] = 0
    if metrics["min_output_length"] == float("inf"):
        metrics["min_output_length"] = 0

    metrics["completion_rate"] = (metrics["total_rows"] - metrics["empty_rows"]) / max(
        metrics["total_rows"], 1
    )

    return metrics


def create_progress_bar(description: str = "Processing") -> Progress:
    """Create a Rich progress bar."""
    _ = description  # Reserved for future use
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True,
    )


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def validate_path(path: Path, must_exist: bool = False) -> Path:
    """Validate and resolve a file path."""
    resolved_path = path.resolve()

    if must_exist and not resolved_path.exists():
        raise FileNotFoundError(f"Path does not exist: {resolved_path}")

    return resolved_path


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def generate_dataset_card(
    dataset_name: str,
    schema: str,
    row_count: int,
    model: str,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> str:
    """Generate a README card for the dataset."""
    # Add tags section if provided
    tags_section = ""
    if tags:
        tags_section = f"""
---
tags:
{chr(10).join(f"  - {tag}" for tag in tags)}
"""

    return f"""# {dataset_name}

## Dataset Description

This dataset was generated using Data4AI with the {schema} schema format.

{description or "An AI-generated instruction-tuning dataset."}

## Dataset Statistics

- **Format**: {schema}
- **Size**: {row_count} examples
- **Model**: {model}
- **Generated**: {datetime.now(timezone.utc).strftime("%Y-%m-%d")}{tags_section}

## Schema Format

The dataset follows the **{schema}** format with the following structure:

{_get_schema_description(schema)}

## Usage

```python
from datasets import load_dataset

dataset = load_dataset("{dataset_name}")
```

## Generation Details

This dataset was generated using [Data4AI](https://github.com/data4ai/data4ai),
an AI-powered tool for creating high-quality instruction-tuning datasets.

## License

Please refer to the model's license for usage restrictions.

## Citation

If you use this dataset, please cite:

```bibtex
@misc{{{dataset_name},
  title={{{dataset_name}}},
  author={{Data4AI Project}},
  year={{2024}},
  publisher={{HuggingFace}}
}}
```
"""


def _get_schema_description(schema: str) -> str:
    """Get schema description for dataset card."""
    descriptions = {
        "alpaca": """```json
{
  "instruction": "The task or question",
  "input": "Optional context or input",
  "output": "The expected response"
}
```""",
        "dolly": """```json
{
  "instruction": "The task or question",
  "context": "Background information",
  "response": "The expected response",
  "category": "Optional category"
}
```""",
        "sharegpt": """```json
{
  "conversations": [
    {"from": "human", "value": "User message"},
    {"from": "gpt", "value": "Assistant response"}
  ]
}
```""",
    }
    return descriptions.get(schema, "Custom schema format")


def batch_items(items: list[Any], batch_size: int) -> Generator[list[Any], None, None]:
    """Yield batches of items."""
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def safe_json_parse(text: str) -> Optional[Any]:
    """Safely parse JSON string."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def extract_json_from_text(text: str) -> Optional[Any]:
    """Extract JSON from text that might contain other content."""
    import logging
    import re

    logger = logging.getLogger(__name__)

    # Clean the text - remove common prefixes/suffixes
    text = text.strip()

    # Try to find JSON array first (most common for datasets)
    array_match = re.search(r"\[.*\]", text, re.DOTALL)
    if array_match:
        try:
            result = safe_json_parse(array_match.group())
            if result is not None:
                logger.debug(
                    f"Successfully extracted JSON array with {len(result)} items"
                )
                return result
        except Exception as e:
            logger.debug(f"Failed to parse JSON array: {e}")

    # Look for JSON object
    object_match = re.search(r"\{.*\}", text, re.DOTALL)
    if object_match:
        try:
            result = safe_json_parse(object_match.group())
            if result is not None:
                logger.debug("Successfully extracted JSON object")
                return result
        except Exception as e:
            logger.debug(f"Failed to parse JSON object: {e}")

    # Try parsing the whole text
    try:
        result = safe_json_parse(text)
        if result is not None:
            logger.debug("Successfully parsed entire text as JSON")
            return result
    except Exception as e:
        logger.debug(f"Failed to parse entire text as JSON: {e}")

    # Log preview of failed parsing
    preview = text[:200] + "..." if len(text) > 200 else text
    logger.warning(f"Could not extract JSON from text. Preview: {preview}")

    return None
