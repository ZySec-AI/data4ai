"""Excel file operations for Data4AI."""

import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from data4ai.exceptions import ExcelError, ValidationError
from data4ai.schemas import SchemaRegistry

# Check if openpyxl is available
try:
    import importlib.util

    OPENPYXL_AVAILABLE = importlib.util.find_spec("openpyxl") is not None
except ImportError:
    OPENPYXL_AVAILABLE = False


logger = logging.getLogger("data4ai")


class ExcelHandler:
    """Handle Excel file operations."""

    @staticmethod
    def create_template(
        path: Path,
        schema_name: str,
        examples: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        """Create Excel template for specific schema."""
        if not OPENPYXL_AVAILABLE:
            raise ExcelError(
                "Excel support not available. Please install with: pip install data4ai[excel] "
                "or pip install openpyxl"
            )
        try:
            schema_class = SchemaRegistry.get(schema_name)
            columns = schema_class.get_columns()

            if examples:
                df = pd.DataFrame(examples)
                # Ensure all columns are present
                for col in columns:
                    if col not in df.columns:
                        df[col] = ""
                df = df[columns]  # Reorder columns
            else:
                # Create template with example data
                example_data = ExcelHandler._get_example_data(schema_name)
                df = pd.DataFrame([example_data])

                # Add empty rows for user to fill
                empty_rows = pd.DataFrame(
                    [[""] * len(columns) for _ in range(4)],
                    columns=columns,
                )
                df = pd.concat([df, empty_rows], ignore_index=True)

            # Write to Excel with formatting
            path.parent.mkdir(parents=True, exist_ok=True)

            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Data", index=False)

                # Add formatting
                worksheet = writer.sheets["Data"]

                # Set column widths
                for i, _col in enumerate(columns, 1):
                    worksheet.column_dimensions[chr(64 + i)].width = 30

                # Add instructions in a separate sheet
                instructions = ExcelHandler._get_instructions(schema_name)
                instructions_df = pd.DataFrame({"Instructions": [instructions]})
                instructions_df.to_excel(writer, sheet_name="Instructions", index=False)

            logger.info(f"Created Excel template at {path}")

        except Exception as e:
            raise ExcelError(f"Failed to create template: {str(e)}") from e

    @staticmethod
    def read_data(path: Path) -> pd.DataFrame:
        """Read data from Excel file."""
        if not OPENPYXL_AVAILABLE:
            raise ExcelError(
                "Excel support not available. Please install with: pip install data4ai[excel] "
                "or pip install openpyxl"
            )
        try:
            if not path.exists():
                raise FileNotFoundError(f"Excel file not found: {path}")

            df = pd.read_excel(path, sheet_name=0, engine="openpyxl")

            if df.empty:
                raise ValidationError("Excel file is empty")

            logger.info(f"Read {len(df)} rows from {path}")
            return df

        except Exception as e:
            raise ExcelError(f"Failed to read Excel file: {str(e)}") from e

    @staticmethod
    def detect_partial_rows(df: pd.DataFrame) -> list[int]:
        """Detect rows with missing data that need completion."""
        partial_rows = []

        for idx, row in df.iterrows():
            # Check for NaN or empty string values
            has_empty = False
            has_content = False

            for value in row.values:
                if pd.isna(value) or (isinstance(value, str) and not value.strip()):
                    has_empty = True
                else:
                    has_content = True

            # Row is partial if it has some content but also empty fields
            if has_content and has_empty:
                partial_rows.append(idx)

        return partial_rows

    @staticmethod
    def convert_to_dataset(
        df: pd.DataFrame,
        schema_name: str,
    ) -> list[dict[str, Any]]:
        """Convert DataFrame to dataset format."""
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
                    row_dict = ExcelHandler._convert_sharegpt_row(row_dict)

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
    ) -> None:
        """Write completed data back to Excel."""
        try:
            # Update DataFrame with completed data
            for idx, data in completed_data.items():
                for key, value in data.items():
                    if key in df.columns:
                        df.at[idx, key] = value

            # Write to new Excel file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_excel(output_path, index=False, engine="openpyxl")

            logger.info(f"Wrote completed data to {output_path}")

        except Exception as e:
            raise ExcelError(f"Failed to write Excel file: {str(e)}") from e

    @staticmethod
    def validate_schema_compatibility(
        df: pd.DataFrame,
        schema_name: str,
    ) -> tuple[bool, list[str]]:
        """Check if DataFrame columns are compatible with schema."""
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
    def _get_instructions(schema_name: str) -> str:
        """Get instructions for filling the template."""
        instructions = {
            "alpaca": """Alpaca Format Instructions:

1. instruction: The task, question, or prompt (required)
2. input: Additional context or input data (optional)
3. output: The expected response or answer (required)

Tips:
- Leave 'input' empty if not needed
- Keep instructions clear and specific
- Outputs should be complete and helpful
- You can leave some rows partially filled for AI completion""",
            "dolly": """Dolly Format Instructions:

1. instruction: The task or question (required)
2. context: Background information or constraints (optional)
3. response: The expected answer (required)
4. category: Type of task (optional, e.g., 'qa', 'summarization')

Tips:
- Context helps provide more specific responses
- Categories help organize your dataset
- Leave fields empty for AI to complete""",
            "sharegpt": """ShareGPT Format Instructions:

1. human_message: The user's message
2. assistant_response: The assistant's reply
3. conversation_continues: 'yes' if conversation has more turns

Tips:
- Each row represents one exchange
- For multi-turn conversations, set 'conversation_continues' to 'yes'
- Keep conversations natural and helpful""",
        }
        return instructions.get(schema_name, "Fill in the data as needed.")

    @staticmethod
    def _convert_sharegpt_row(row_dict: dict[str, Any]) -> dict[str, Any]:
        """Convert simplified ShareGPT Excel format to conversation format."""
        conversations = []

        if "human_message" in row_dict and row_dict["human_message"]:
            conversations.append({"from": "human", "value": row_dict["human_message"]})

        if "assistant_response" in row_dict and row_dict["assistant_response"]:
            conversations.append(
                {"from": "gpt", "value": row_dict["assistant_response"]}
            )

        return {"conversations": conversations}
