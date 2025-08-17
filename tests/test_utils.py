"""Tests for utility functions."""

from data4ai.utils import (
    batch_items,
    calculate_metrics,
    extract_json_from_text,
    format_file_size,
    read_jsonl,
    truncate_text,
    write_jsonl,
)


def test_read_write_jsonl(temp_dir):
    """Test JSONL read/write operations."""
    data = [
        {"instruction": "Test 1", "output": "Output 1"},
        {"instruction": "Test 2", "output": "Output 2"},
    ]

    file_path = temp_dir / "test.jsonl"

    # Write data
    count = write_jsonl(data, file_path)
    assert count == 2
    assert file_path.exists()

    # Read data
    read_data = list(read_jsonl(file_path))
    assert len(read_data) == 2
    assert read_data[0]["instruction"] == "Test 1"


def test_calculate_metrics():
    """Test metrics calculation."""
    data = [
        {"instruction": "Short", "output": "A longer output here"},
        {"instruction": "A much longer instruction", "output": "Short"},
        {"instruction": "", "output": ""},  # Empty
    ]

    metrics = calculate_metrics(data, "alpaca")

    assert metrics["total_rows"] == 3
    assert metrics["empty_rows"] == 1
    assert metrics["completion_rate"] == 2 / 3
    assert metrics["avg_instruction_length"] > 0


def test_truncate_text():
    """Test text truncation."""
    text = "This is a very long text that needs to be truncated"

    truncated = truncate_text(text, max_length=20)
    assert len(truncated) <= 20
    assert truncated.endswith("...")

    short = truncate_text("Short", max_length=20)
    assert short == "Short"


def test_extract_json_from_text():
    """Test JSON extraction from text."""
    # Plain JSON
    text = '{"key": "value"}'
    result = extract_json_from_text(text)
    assert result == {"key": "value"}

    # JSON in text
    text = 'Here is some JSON: [{"item": 1}, {"item": 2}] and more text'
    result = extract_json_from_text(text)
    assert isinstance(result, list)
    assert len(result) == 2

    # Invalid JSON
    text = "No JSON here"
    result = extract_json_from_text(text)
    assert result is None


def test_batch_items():
    """Test batching items."""
    items = list(range(10))

    batches = list(batch_items(items, batch_size=3))
    assert len(batches) == 4
    assert batches[0] == [0, 1, 2]
    assert batches[-1] == [9]


def test_format_file_size():
    """Test file size formatting."""
    assert format_file_size(100) == "100.00 B"
    assert format_file_size(1024) == "1.00 KB"
    assert format_file_size(1024 * 1024) == "1.00 MB"
    assert format_file_size(1024 * 1024 * 1024) == "1.00 GB"
