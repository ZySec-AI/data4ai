"""Unit tests for CSV handler module."""

import csv
from pathlib import Path

import pandas as pd
import pytest

from data4ai.csv_handler import CSVHandler
from data4ai.exceptions import ValidationError


class TestCSVHandler:
    """Test CSV handler functionality."""

    def test_detect_dialect(self, temp_dir):
        """Test CSV dialect detection."""
        # Create CSV with semicolon delimiter
        csv_path = temp_dir / "test.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["col1", "col2", "col3"])
            writer.writerow(["val1", "val2", "val3"])

        dialect, has_header = CSVHandler.detect_dialect(csv_path)

        assert dialect.delimiter == ";"
        assert has_header is True

    def test_read_data_basic(self, temp_dir):
        """Test basic CSV reading."""
        csv_path = temp_dir / "test.csv"

        # Create test CSV
        data = {
            "instruction": ["What is AI?", "Explain ML"],
            "input": ["", "In simple terms"],
            "output": ["AI is...", "ML is..."],
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        # Read CSV
        result = CSVHandler.read_data(csv_path)

        assert len(result) == 2
        assert list(result.columns) == ["instruction", "input", "output"]
        assert result.iloc[0]["instruction"] == "What is AI?"

    def test_read_data_auto_delimiter(self, temp_dir):
        """Test reading CSV with auto-detected delimiter."""
        csv_path = temp_dir / "test.csv"

        # Create CSV with tab delimiter
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["col1", "col2"])
            writer.writerow(["val1", "val2"])

        df = CSVHandler.read_data(csv_path)

        assert len(df) == 1
        assert list(df.columns) == ["col1", "col2"]

    def test_read_streaming(self, temp_dir):
        """Test streaming CSV read."""
        csv_path = temp_dir / "large.csv"

        # Create larger CSV
        data = {"id": range(100), "value": [f"val{i}" for i in range(100)]}
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        # Read in chunks
        chunks = list(CSVHandler.read_streaming(csv_path, chunksize=25))

        assert len(chunks) == 4  # 100 rows / 25 per chunk
        assert len(chunks[0]) == 25
        assert chunks[0].iloc[0]["id"] == 0
        assert chunks[-1].iloc[-1]["id"] == 99

    def test_detect_partial_rows(self, temp_dir):
        """Test detection of rows with missing data."""
        data = pd.DataFrame(
            {
                "instruction": ["What is AI?", "Explain ML", ""],
                "input": ["", "Context", "Input text"],
                "output": ["AI is...", "", "Output text"],
            }
        )

        partial_rows = CSVHandler.detect_partial_rows(data)

        # Row 1 has missing output, Row 2 has missing instruction
        assert len(partial_rows) == 2
        assert 1 in partial_rows  # Row with missing output
        assert 2 in partial_rows  # Row with missing instruction

    def test_create_template(self, temp_dir):
        """Test CSV template creation."""
        csv_path = temp_dir / "template.csv"

        CSVHandler.create_template(csv_path, "alpaca")

        assert csv_path.exists()

        # Check template content
        df = pd.read_csv(csv_path)
        assert "instruction" in df.columns
        assert "input" in df.columns
        assert "output" in df.columns
        assert len(df) >= 1  # Should have at least example row

    def test_convert_to_dataset_alpaca(self):
        """Test converting DataFrame to Alpaca dataset."""
        df = pd.DataFrame(
            {
                "instruction": ["What is AI?", "Explain ML"],
                "input": ["", "In simple terms"],
                "output": ["AI is artificial intelligence", "ML is machine learning"],
            }
        )

        dataset = CSVHandler.convert_to_dataset(df, "alpaca")

        assert len(dataset) == 2
        assert dataset[0]["instruction"] == "What is AI?"
        assert dataset[0]["output"] == "AI is artificial intelligence"
        assert dataset[1]["input"] == "In simple terms"

    def test_convert_to_dataset_sharegpt(self):
        """Test converting DataFrame to ShareGPT format."""
        df = pd.DataFrame(
            {
                "human_message": ["Hello", "What is Python?"],
                "assistant_response": ["Hi there!", "Python is a programming language"],
            }
        )

        dataset = CSVHandler.convert_to_dataset(df, "sharegpt")

        assert len(dataset) == 2
        assert "conversations" in dataset[0]
        assert len(dataset[0]["conversations"]) == 2
        assert dataset[0]["conversations"][0]["from"] == "human"
        assert dataset[0]["conversations"][0]["value"] == "Hello"

    def test_validate_schema_compatibility(self):
        """Test schema compatibility validation."""
        # Valid Alpaca DataFrame
        df_valid = pd.DataFrame(
            {"instruction": ["test"], "input": [""], "output": ["result"]}
        )

        is_valid, missing = CSVHandler.validate_schema_compatibility(df_valid, "alpaca")
        assert is_valid is True
        assert len(missing) == 0

        # Invalid Alpaca DataFrame (missing required column)
        df_invalid = pd.DataFrame(
            {
                "instruction": ["test"],
                "input": [""],
                # Missing 'output' column
            }
        )

        is_valid, missing = CSVHandler.validate_schema_compatibility(
            df_invalid, "alpaca"
        )
        assert is_valid is False
        assert "output" in missing

    def test_write_completed_data(self, temp_dir):
        """Test writing completed data back to CSV."""
        df = pd.DataFrame(
            {
                "instruction": ["What is AI?", "Explain ML"],
                "input": ["", ""],
                "output": ["", ""],  # Empty outputs to be completed
            }
        )

        completed_data = {
            0: {"output": "AI is artificial intelligence"},
            1: {"output": "ML is machine learning"},
        }

        output_path = temp_dir / "completed.csv"
        CSVHandler.write_completed_data(df, completed_data, output_path)

        assert output_path.exists()

        # Read and verify
        result = pd.read_csv(output_path)
        assert result.iloc[0]["output"] == "AI is artificial intelligence"
        assert result.iloc[1]["output"] == "ML is machine learning"

    def test_empty_csv_error(self, temp_dir):
        """Test that empty CSV raises appropriate error."""
        csv_path = temp_dir / "empty.csv"

        # Create empty CSV (headers only)
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["col1", "col2"])

        with pytest.raises(ValidationError, match="CSV file is empty"):
            CSVHandler.read_data(csv_path)

    def test_file_not_found_error(self):
        """Test handling of non-existent file."""
        with pytest.raises(ValidationError, match="Failed to read CSV"):
            CSVHandler.read_data(Path("nonexistent.csv"))
