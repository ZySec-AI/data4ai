"""Tests for Excel handler functionality."""

from pathlib import Path

import pandas as pd
import pytest

from data4ai.excel_handler import ExcelHandler
from data4ai.exceptions import ExcelError


class TestCreateTemplate:
    """Test Excel template creation functionality."""

    def test_create_template_alpaca(self):
        """Test creating Alpaca schema Excel template."""
        test_file = Path("/tmp/test_alpaca.xlsx")

        try:
            ExcelHandler.create_template(test_file, schema_name="alpaca")

            assert test_file.exists()

            # Read the created file
            df = pd.read_excel(test_file)

            # Check columns
            expected_columns = ["instruction", "input", "output"]
            assert list(df.columns) == expected_columns

            # Check that it has example rows
            assert len(df) > 0

            # Check that example rows have content
            assert df.iloc[0]["instruction"] != ""
            assert df.iloc[0]["output"] != ""

        finally:
            test_file.unlink(missing_ok=True)

    def test_create_template_dolly(self):
        """Test creating Dolly schema Excel template."""
        test_file = Path("/tmp/test_dolly.xlsx")

        try:
            ExcelHandler.create_template(test_file, schema_name="dolly")

            assert test_file.exists()

            # Read the created file
            df = pd.read_excel(test_file)

            # Check columns
            expected_columns = ["instruction", "context", "response", "category"]
            assert list(df.columns) == expected_columns

            # Check that it has example rows
            assert len(df) > 0

        finally:
            test_file.unlink(missing_ok=True)

    def test_create_template_sharegpt(self):
        """Test creating ShareGPT schema Excel template."""
        test_file = Path("/tmp/test_sharegpt.xlsx")

        try:
            ExcelHandler.create_template(test_file, schema_name="sharegpt")

            assert test_file.exists()

            # Read the created file
            df = pd.read_excel(test_file)

            # Check columns
            expected_columns = [
                "human_message",
                "assistant_response",
                "conversation_continues",
            ]
            assert list(df.columns) == expected_columns

            # Check that it has example rows
            assert len(df) > 0

        finally:
            test_file.unlink(missing_ok=True)

    def test_create_template_invalid_schema(self):
        """Test creating Excel template with invalid schema."""
        test_file = Path("/tmp/test_invalid.xlsx")

        with pytest.raises(ExcelError):
            ExcelHandler.create_template(test_file, schema_name="invalid_schema")

        assert not test_file.exists()

    def test_create_template_with_custom_examples(self):
        """Test creating Excel template with custom examples."""
        test_file = Path("/tmp/test_custom.xlsx")

        custom_examples = [
            {
                "instruction": "Custom instruction 1",
                "input": "Custom input 1",
                "output": "Custom output 1",
            },
            {
                "instruction": "Custom instruction 2",
                "input": "Custom input 2",
                "output": "Custom output 2",
            },
        ]

        try:
            ExcelHandler.create_template(
                test_file, schema_name="alpaca", examples=custom_examples
            )

            assert test_file.exists()

            # Read the created file
            df = pd.read_excel(test_file)

            # Check that custom examples are included
            assert len(df) >= len(custom_examples)
            assert df.iloc[0]["instruction"] == "Custom instruction 1"
            assert df.iloc[1]["instruction"] == "Custom instruction 2"

        finally:
            test_file.unlink(missing_ok=True)


class TestReadData:
    """Test Excel file reading functionality."""

    def test_read_data_success(self):
        """Test successful Excel file reading."""
        # Create a test Excel file
        test_file = Path("/tmp/test_read.xlsx")

        test_data = pd.DataFrame(
            {
                "instruction": ["Test instruction 1", "Test instruction 2"],
                "input": ["", "Test input"],
                "output": ["Test output 1", "Test output 2"],
            }
        )

        test_data.to_excel(test_file, index=False)

        try:
            result = ExcelHandler.read_data(test_file)

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2
            assert list(result.columns) == ["instruction", "input", "output"]
            assert result.iloc[0]["instruction"] == "Test instruction 1"
            assert result.iloc[1]["output"] == "Test output 2"

        finally:
            test_file.unlink(missing_ok=True)

    def test_read_data_not_found(self):
        """Test reading non-existent Excel file."""
        test_file = Path("/tmp/nonexistent.xlsx")

        with pytest.raises(ExcelError, match="Failed to read Excel file"):
            ExcelHandler.read_data(test_file)

    def test_read_data_empty(self):
        """Test reading empty Excel file."""
        test_file = Path("/tmp/test_empty.xlsx")

        # Create empty DataFrame
        empty_df = pd.DataFrame()
        empty_df.to_excel(test_file, index=False)

        try:
            with pytest.raises(ExcelError):
                ExcelHandler.read_data(test_file)
        finally:
            test_file.unlink(missing_ok=True)


class TestDetectPartialRows:
    """Test partial row detection functionality."""

    def test_detect_partial_rows_with_partial_data(self):
        """Test detecting partial rows."""
        test_data = pd.DataFrame(
            {
                "instruction": ["Complete instruction", "", "Partial instruction"],
                "input": ["", "Complete input", ""],
                "output": ["Complete output", "Complete output", ""],
            }
        )

        partial_rows = ExcelHandler.detect_partial_rows(test_data)

        # Should detect rows 0 and 2 as partial (have some content but also empty fields)
        assert 0 in partial_rows
        assert 2 in partial_rows
        # Row 1 has content but empty input field, so it's considered partial
        assert 1 in partial_rows  # Row 1 is partial due to empty input

    def test_detect_partial_rows_all_complete(self):
        """Test detecting partial rows when all are complete."""
        test_data = pd.DataFrame(
            {
                "instruction": ["Complete instruction 1", "Complete instruction 2"],
                "input": ["Complete input 1", "Complete input 2"],
                "output": ["Complete output 1", "Complete output 2"],
            }
        )

        partial_rows = ExcelHandler.detect_partial_rows(test_data)

        assert len(partial_rows) == 0

    def test_detect_partial_rows_all_empty(self):
        """Test detecting partial rows when all are empty."""
        test_data = pd.DataFrame(
            {"instruction": ["", ""], "input": ["", ""], "output": ["", ""]}
        )

        partial_rows = ExcelHandler.detect_partial_rows(test_data)

        assert len(partial_rows) == 0  # No partial rows if all empty


class TestConvertToDataset:
    """Test DataFrame to dataset conversion functionality."""

    def test_convert_to_dataset_alpaca(self):
        """Test converting DataFrame to Alpaca dataset."""
        test_data = pd.DataFrame(
            {
                "instruction": ["Write a function", "Create a class"],
                "input": ["", "Input context"],
                "output": ["def func(): pass", "class MyClass: pass"],
            }
        )

        dataset = ExcelHandler.convert_to_dataset(test_data, "alpaca")

        assert len(dataset) == 2
        assert dataset[0]["instruction"] == "Write a function"
        assert dataset[0]["input"] == ""
        assert dataset[0]["output"] == "def func(): pass"

    def test_convert_to_dataset_dolly(self):
        """Test converting DataFrame to Dolly dataset."""
        test_data = pd.DataFrame(
            {
                "instruction": ["Explain quantum computing"],
                "context": ["For beginners"],
                "response": ["Quantum computing is..."],
            }
        )

        dataset = ExcelHandler.convert_to_dataset(test_data, "dolly")

        assert len(dataset) == 1
        assert dataset[0]["instruction"] == "Explain quantum computing"
        assert dataset[0]["context"] == "For beginners"

    def test_convert_to_dataset_sharegpt(self):
        """Test converting DataFrame to ShareGPT dataset."""
        test_data = pd.DataFrame(
            {
                "human_message": ["Hello, how are you?"],
                "assistant_response": ["I'm doing well, thank you!"],
                "conversation_continues": ["no"],
            }
        )

        dataset = ExcelHandler.convert_to_dataset(test_data, "sharegpt")

        assert len(dataset) == 1
        assert "conversations" in dataset[0]
        assert len(dataset[0]["conversations"]) == 2


class TestValidateSchemaCompatibility:
    """Test schema compatibility validation."""

    def test_validate_schema_compatibility_alpaca_valid(self):
        """Test valid Alpaca schema compatibility."""
        test_data = pd.DataFrame(
            {
                "instruction": ["Test instruction"],
                "input": [""],
                "output": ["Test output"],
            }
        )

        is_compatible, missing = ExcelHandler.validate_schema_compatibility(
            test_data, "alpaca"
        )

        assert is_compatible
        assert len(missing) == 0

    def test_validate_schema_compatibility_alpaca_invalid(self):
        """Test invalid Alpaca schema compatibility."""
        test_data = pd.DataFrame(
            {
                "instruction": ["Test instruction"],
                "input": [""],
                # Missing "output" column
            }
        )

        is_compatible, missing = ExcelHandler.validate_schema_compatibility(
            test_data, "alpaca"
        )

        assert not is_compatible
        assert "output" in missing

    def test_validate_schema_compatibility_dolly_valid(self):
        """Test valid Dolly schema compatibility."""
        test_data = pd.DataFrame(
            {"instruction": ["Test instruction"], "response": ["Test response"]}
        )

        is_compatible, missing = ExcelHandler.validate_schema_compatibility(
            test_data, "dolly"
        )

        assert is_compatible
        assert len(missing) == 0


class TestWriteCompletedData:
    """Test writing completed data functionality."""

    def test_write_completed_data_success(self):
        """Test successful writing of completed data."""
        test_file = Path("/tmp/test_write.xlsx")

        test_data = pd.DataFrame(
            {
                "instruction": ["Write a function", "Create a class"],
                "input": ["", "Input context"],
                "output": ["", ""],  # Empty outputs to be completed
            }
        )

        completed_data = {
            0: {"output": "def func(): pass"},
            1: {"output": "class MyClass: pass"},
        }

        try:
            ExcelHandler.write_completed_data(test_data, completed_data, test_file)

            assert test_file.exists()

            # Read back and verify
            result = pd.read_excel(test_file)
            assert len(result) == 2
            assert result.iloc[0]["output"] == "def func(): pass"
            assert result.iloc[1]["output"] == "class MyClass: pass"

        finally:
            test_file.unlink(missing_ok=True)


class TestExcelHandlerIntegration:
    """Integration tests for Excel handler."""

    def test_complete_excel_workflow(self):
        """Test complete Excel workflow: create, read, detect, convert."""
        test_file = Path("/tmp/test_workflow.xlsx")

        try:
            # 1. Create template
            ExcelHandler.create_template(test_file, schema_name="alpaca")
            assert test_file.exists()

            # 2. Read the file
            df = ExcelHandler.read_data(test_file)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0

            # 3. Detect partial rows
            partial_rows = ExcelHandler.detect_partial_rows(df)
            assert isinstance(partial_rows, list)

            # 4. Convert to dataset
            dataset = ExcelHandler.convert_to_dataset(df, "alpaca")
            assert isinstance(dataset, list)
            assert len(dataset) > 0

        finally:
            test_file.unlink(missing_ok=True)

    def test_excel_handler_with_different_schemas(self):
        """Test Excel handler with different schemas."""
        schemas = ["alpaca", "dolly", "sharegpt"]

        for schema in schemas:
            test_file = Path(f"/tmp/test_{schema}.xlsx")

            try:
                # Create template for each schema
                ExcelHandler.create_template(test_file, schema_name=schema)
                assert test_file.exists()

                # Read and verify
                df = ExcelHandler.read_data(test_file)
                assert isinstance(df, pd.DataFrame)
                assert len(df) > 0

                # Validate compatibility
                is_compatible, missing = ExcelHandler.validate_schema_compatibility(
                    df, schema
                )
                assert is_compatible
                assert len(missing) == 0

            finally:
                test_file.unlink(missing_ok=True)


class TestExcelHandlerErrorHandling:
    """Test Excel handler error handling."""

    def test_create_template_permission_error(self):
        """Test creating template with permission error."""
        # Try to create in a directory that doesn't exist
        test_file = Path("/nonexistent/directory/test.xlsx")

        with pytest.raises(ExcelError, match="Failed to create template"):
            ExcelHandler.create_template(test_file, schema_name="alpaca")

    def test_read_data_corrupted(self):
        """Test reading corrupted Excel file."""
        test_file = Path("/tmp/test_corrupted.xlsx")

        # Create a file that's not a valid Excel file
        test_file.write_text("This is not an Excel file")

        try:
            with pytest.raises(ExcelError):
                ExcelHandler.read_data(test_file)
        finally:
            test_file.unlink(missing_ok=True)

    def test_write_completed_data_permission_error(self):
        """Test writing completed data with permission error."""
        test_data = pd.DataFrame({"col": ["value"]})
        completed_data = {0: {"col": "new_value"}}

        # Try to write to a directory that doesn't exist
        test_file = Path("/nonexistent/directory/test.xlsx")

        with pytest.raises(ExcelError, match="Failed to write Excel file"):
            ExcelHandler.write_completed_data(test_data, completed_data, test_file)
