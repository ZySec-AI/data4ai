"""Tests for utility functions."""

from data4ai.utils import (
    _get_schema_description,
    _get_size_category,
    batch_items,
    calculate_metrics,
    compute_taxonomy_by_document,
    compute_taxonomy_coverage,
    create_progress_bar,
    extract_json_from_text,
    format_file_size,
    generate_dataset_card,
    read_jsonl,
    safe_json_parse,
    save_metadata,
    truncate_text,
    validate_path,
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
    assert format_file_size(1024**4) == "1.00 TB"


def test_jsonl_invalid_lines_are_skipped(temp_dir):
    path = temp_dir / "mixed.jsonl"
    path.write_text('{"valid": true}\ninvalid\n\n', encoding="utf-8")
    assert list(read_jsonl(path)) == [{"valid": True}]


def test_metadata_progress_and_path_helpers(temp_dir):
    metadata_path = save_metadata(
        temp_dir, "alpaca", "model", 2, {"temperature": 0.1}, {"valid": 2}
    )
    assert metadata_path.exists()
    assert '"row_count": 2' in metadata_path.read_text(encoding="utf-8")
    assert create_progress_bar().__class__.__name__ == "Progress"
    assert validate_path(temp_dir, must_exist=True) == temp_dir.resolve()
    missing = temp_dir / "missing"
    assert validate_path(missing) == missing.resolve()
    try:
        validate_path(missing, must_exist=True)
    except FileNotFoundError as error:
        assert "missing" in str(error)
    else:
        raise AssertionError("missing path should fail validation")


def test_metrics_for_empty_and_chatml_data():
    empty = calculate_metrics([], "alpaca")
    assert empty["total_rows"] == 0
    messages = [
        {"messages": [{"role": "user", "content": "hello"}]},
        {"messages": []},
    ]
    metrics = calculate_metrics(messages, "chatml")
    assert metrics["empty_rows"] == 1
    assert metrics["min_instruction_length"] is None
    assert metrics["min_output_length"] is None


def test_dataset_card_schema_and_size_variants():
    tags = ["custom"]
    card = generate_dataset_card(
        "example-dataset", "chatml", 1500, "test/model", "Description", tags
    )
    assert "Description" in card
    assert "1K<n<10K" in card
    assert "ZySecAI" in tags and "Data4AI" in tags
    assert '"messages"' in _get_schema_description("chatml")
    assert '"instruction"' in _get_schema_description("alpaca")
    assert _get_schema_description("custom") == "Custom schema format"
    assert [
        _get_size_category(value) for value in (1, 1000, 10000, 100000, 1000000)
    ] == [
        "n<1K",
        "1K<n<10K",
        "10K<n<100K",
        "100K<n<1M",
        "n>1M",
    ]


def test_json_recovery_and_taxonomy_helpers():
    assert safe_json_parse('{"ok": true}') == {"ok": True}
    assert safe_json_parse(None) is None
    assert extract_json_from_text('```json\n[{"a": 1}]\n```') == [{"a": 1}]
    assert extract_json_from_text('[{"a": 1}, {"a": 2') == [{"a": 1}]
    assert extract_json_from_text('prefix {"a": 1} suffix') == {"a": 1}

    rows = [
        {"taxonomy_level": "Remember", "source_document": "one"},
        {"taxonomy_level": "unknown", "source_document": "one"},
        {"taxonomy_level": "apply"},
    ]
    coverage = compute_taxonomy_coverage(rows)
    assert coverage["remember"] == 1
    assert coverage["unspecified"] == 1
    grouped = compute_taxonomy_by_document(rows)
    assert grouped["one"]["remember"] == 1
    assert grouped["unknown"]["apply"] == 1
