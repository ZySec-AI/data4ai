"""CSV file operations for Data4AI."""

import csv
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from data4ai.exceptions import ValidationError
from data4ai.schemas import SchemaRegistry

logger = logging.getLogger("data4ai")


class CSVHandler:
    """Handle CSV file operations with streaming support."""

    @staticmethod
    def detect_dialect(
        file_path: Path, encoding: str = "utf-8"
    ) -> tuple[csv.Dialect, bool]:
        """Auto-detect CSV dialect (delimiter, quote char, etc.).

        Args:
            file_path: Path to CSV file
            encoding: File encoding

        Returns:
            Tuple of (detected CSV dialect, has_header)
        """
        try:
            with open(file_path, encoding=encoding) as f:
                # Read sample for detection
                sample = f.read(8192)
                sniffer = csv.Sniffer()

                # Try to detect dialect
                try:
                    dialect = sniffer.sniff(sample)
                except csv.Error:
                    # Fallback to common delimiters
                    for delimiter in [",", ";", "\t", "|"]:
                        if delimiter in sample:
                            dialect = csv.excel
                            dialect.delimiter = delimiter
                            break
                    else:
                        # Default to comma
                        dialect = csv.excel
                        dialect.delimiter = ","

                # Override delimiter detection for specific cases
                # If sample contains semicolon and we detected comma, prefer semicolon
                if ";" in sample and dialect.delimiter == ",":
                    dialect.delimiter = ";"
                # If sample contains tab and we detected comma, prefer tab
                elif "\t" in sample and dialect.delimiter == ",":
                    dialect.delimiter = "\t"

                # Check if has header - try to detect, but be more lenient
                try:
                    has_header = sniffer.has_header(sample)
                except csv.Error:
                    # If we can't detect, assume it has a header if first line looks like headers
                    lines = sample.strip().split("\n")
                    if lines:
                        first_line = lines[0]
                        # Simple heuristic: if first line has no numbers and looks like column names
                        if (
                            not any(char.isdigit() for char in first_line)
                            and len(first_line.split(dialect.delimiter)) > 1
                        ):
                            has_header = True
                        else:
                            has_header = False
                    else:
                        has_header = False

                # Override header detection for specific cases
                # If we have multiple lines and first line looks like column names, assume header
                lines = sample.strip().split("\n")
                if len(lines) >= 2:
                    first_line = lines[0]
                    lines[1]
                    # Better heuristic: if first line contains common column name patterns
                    first_line_lower = first_line.lower()
                    common_headers = [
                        "col",
                        "column",
                        "field",
                        "name",
                        "id",
                        "type",
                        "value",
                        "data",
                        "instruction",
                        "input",
                        "output",
                        "response",
                        "context",
                    ]
                    looks_like_header = any(
                        header in first_line_lower for header in common_headers
                    )

                    # If first line looks like headers and second line looks like data, assume header
                    if (
                        looks_like_header
                        and len(first_line.split(dialect.delimiter)) > 1
                    ):
                        has_header = True

                logger.info(
                    f"Detected CSV dialect: delimiter='{dialect.delimiter}', "
                    f"quotechar='{dialect.quotechar}', has_header={has_header}"
                )

                return dialect, has_header

        except Exception as e:
            logger.warning(f"Could not detect CSV dialect, using defaults: {e}")
            return csv.excel, True

    @staticmethod
    def read_streaming(
        file_path: Path,
        chunksize: int = 1000,
        delimiter: Optional[str] = None,
        encoding: str = "utf-8",
        has_header: Optional[bool] = None,
    ) -> Iterator[pd.DataFrame]:
        """Stream read CSV file in chunks to handle large files.

        Args:
            file_path: Path to CSV file
            chunksize: Number of rows per chunk
            delimiter: CSV delimiter (auto-detect if None)
            encoding: File encoding
            has_header: Whether file has header (auto-detect if None)

        Yields:
            DataFrame chunks
        """
        try:
            # Auto-detect if needed
            if delimiter is None or has_header is None:
                dialect, detected_header = CSVHandler.detect_dialect(
                    file_path, encoding
                )
                delimiter = delimiter or dialect.delimiter
                has_header = has_header if has_header is not None else detected_header

            # Stream read with pandas
            reader = pd.read_csv(
                file_path,
                chunksize=chunksize,
                delimiter=delimiter,
                encoding=encoding,
                header=0 if has_header else None,
                skip_blank_lines=True,
                on_bad_lines="warn",
            )

            for chunk_num, chunk in enumerate(reader):
                logger.debug(f"Read CSV chunk {chunk_num} with {len(chunk)} rows")
                yield chunk

        except Exception as e:
            logger.error(f"Failed to read CSV file: {e}")
            raise ValidationError(f"Failed to read CSV file: {str(e)}") from e

    @staticmethod
    def read_data(
        file_path: Path,
        delimiter: Optional[str] = None,
        encoding: str = "utf-8",
        has_header: Optional[bool] = None,
        max_rows: Optional[int] = None,
    ) -> pd.DataFrame:
        """Read entire CSV file into DataFrame.

        Args:
            file_path: Path to CSV file
            delimiter: CSV delimiter
            encoding: File encoding
            has_header: Whether file has header
            max_rows: Maximum rows to read

        Returns:
            DataFrame with CSV data
        """
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")

            # Auto-detect if needed
            if delimiter is None or has_header is None:
                dialect, detected_header = CSVHandler.detect_dialect(
                    file_path, encoding
                )
                delimiter = delimiter or dialect.delimiter
                has_header = has_header if has_header is not None else detected_header

            # Read CSV
            df = pd.read_csv(
                file_path,
                delimiter=delimiter,
                encoding=encoding,
                header=0 if has_header else None,
                nrows=max_rows,
                skip_blank_lines=True,
                on_bad_lines="warn",
            )

            if df.empty:
                raise ValidationError("CSV file is empty")

            logger.info(f"Read {len(df)} rows from CSV file")
            return df

        except Exception as e:
            logger.error(f"Failed to read CSV file: {e}")
            raise ValidationError(f"Failed to read CSV file: {str(e)}") from e

    @staticmethod
    def create_template(
        path: Path,
        schema_name: str,
        examples: Optional[list[dict[str, Any]]] = None,
        delimiter: str = ",",
        encoding: str = "utf-8",
    ) -> None:
        """Create CSV template for specific schema.

        Args:
            path: Output path for CSV file
            schema_name: Name of schema to use
            examples: Optional example data
            delimiter: CSV delimiter
            encoding: File encoding
        """
        try:
            schema_class = SchemaRegistry.get(schema_name)
            columns = schema_class.get_columns()

            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding=encoding, newline="") as f:
                writer = csv.DictWriter(f, fieldnames=columns, delimiter=delimiter)
                writer.writeheader()

                if examples:
                    for example in examples:
                        writer.writerow(example)
                else:
                    # Add example rows
                    example_data = CSVHandler._get_example_data(schema_name)
                    writer.writerow(example_data)

                    # Add empty rows for user to fill
                    for _ in range(4):
                        writer.writerow(dict.fromkeys(columns, ""))

            logger.info(f"Created CSV template at {path}")

        except Exception as e:
            raise ValidationError(f"Failed to create CSV template: {str(e)}") from e

    @staticmethod
    def detect_partial_rows(df: pd.DataFrame, schema_name: str = "alpaca") -> list[int]:
        """Detect rows with missing data that need completion.

        Args:
            df: DataFrame to check
            schema_name: Schema to check against (default: alpaca)

        Returns:
            List of row indices with partial data
        """
        partial_rows = []

        # Define required fields for each schema
        required_fields = {
            "alpaca": ["instruction", "output"],
            "dolly": ["instruction", "response"],
            "sharegpt": ["conversations"],
        }

        required = required_fields.get(schema_name, ["instruction", "output"])

        for idx, row in df.iterrows():
            # Check if required fields are missing
            missing_required = False

            for field in required:
                if field in row.index:
                    value = row[field]
                    if pd.isna(value) or (isinstance(value, str) and not value.strip()):
                        missing_required = True
                        break
                else:
                    # Field doesn't exist in DataFrame
                    missing_required = True
                    break

            # Row is partial if it's missing required fields
            if missing_required:
                partial_rows.append(idx)

        return partial_rows

    @staticmethod
    def convert_to_dataset(df: pd.DataFrame, schema_name: str) -> list[dict[str, Any]]:
        """Convert DataFrame to dataset format.

        Args:
            df: DataFrame to convert
            schema_name: Target schema name

        Returns:
            List of dataset entries
        """
        dataset = []
        schema_class = SchemaRegistry.get(schema_name)

        for _, row in df.iterrows():
            try:
                # Convert row to dict and remove NaN values
                row_dict = row.to_dict()
                row_dict = {
                    k: v
                    for k, v in row_dict.items()
                    if not (pd.isna(v) or (isinstance(v, str) and not v.strip()))
                }

                # Special handling for ShareGPT schema
                if schema_name == "sharegpt":
                    row_dict = CSVHandler._convert_sharegpt_row(row_dict)

                # Validate and create schema instance
                instance = schema_class.from_dict(row_dict)
                if instance.validate_content():
                    dataset.append(instance.to_jsonl_entry())

            except Exception as e:
                logger.warning(f"Skipping invalid row: {e}")
                continue

        return dataset

    @staticmethod
    def write_completed_data(
        df: pd.DataFrame,
        completed_data: dict[int, dict[str, Any]],
        output_path: Path,
        delimiter: str = ",",
        encoding: str = "utf-8",
    ) -> None:
        """Write completed data back to CSV.

        Args:
            df: Original DataFrame
            completed_data: Completed data by row index
            output_path: Output file path
            delimiter: CSV delimiter
            encoding: File encoding
        """
        try:
            # Update DataFrame with completed data
            for idx, data in completed_data.items():
                for key, value in data.items():
                    if key in df.columns:
                        df.at[idx, key] = value

            # Write to CSV
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False, sep=delimiter, encoding=encoding)

            logger.info(f"Wrote completed data to {output_path}")

        except Exception as e:
            raise ValidationError(f"Failed to write CSV file: {str(e)}") from e

    @staticmethod
    def validate_schema_compatibility(
        df: pd.DataFrame, schema_name: str
    ) -> tuple[bool, list[str]]:
        """Check if DataFrame columns are compatible with schema.

        Args:
            df: DataFrame to validate
            schema_name: Target schema name

        Returns:
            Tuple of (is_valid, missing_columns)
        """
        schema_class = SchemaRegistry.get(schema_name)
        expected_columns = schema_class.get_columns()
        actual_columns = list(df.columns)

        [col for col in expected_columns if col not in actual_columns]

        # For ShareGPT, we have a flexible format
        if schema_name == "sharegpt":
            # Check for either conversation columns or simplified format
            has_conversation_cols = any(
                "conversation" in col.lower()
                or "human" in col.lower()
                or "assistant" in col.lower()
                for col in actual_columns
            )
            if has_conversation_cols:
                return True, []

        # For other schemas, check required columns
        if schema_name == "alpaca":
            required = ["instruction", "output"]
        elif schema_name == "dolly":
            required = ["instruction", "response"]
        else:
            required = expected_columns[:2]  # At least first 2 columns

        missing_required = [col for col in required if col not in actual_columns]

        if missing_required:
            return False, missing_required

        return True, []

    @staticmethod
    def _get_example_data(schema_name: str) -> dict[str, str]:
        """Get example data for schema."""
        examples = {
            "alpaca": {
                "instruction": "What is machine learning?",
                "input": "",
                "output": "Machine learning is a subset of artificial intelligence...",
            },
            "dolly": {
                "instruction": "Explain quantum computing",
                "context": "For a beginner audience",
                "response": "Quantum computing is a revolutionary approach...",
                "category": "education",
            },
            "sharegpt": {
                "human_message": "Hello, how are you?",
                "assistant_response": "I'm doing well, thank you for asking!",
                "conversation_continues": "no",
            },
        }
        return examples.get(schema_name, {})

    @staticmethod
    def _convert_sharegpt_row(row_dict: dict[str, Any]) -> dict[str, Any]:
        """Convert simplified ShareGPT CSV format to conversation format."""
        conversations = []

        if "human_message" in row_dict and row_dict["human_message"]:
            conversations.append({"from": "human", "value": row_dict["human_message"]})

        if "assistant_response" in row_dict and row_dict["assistant_response"]:
            conversations.append(
                {"from": "gpt", "value": row_dict["assistant_response"]}
            )

        return {"conversations": conversations}
