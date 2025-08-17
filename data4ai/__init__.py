"""Data4AI - AI-powered dataset generation for instruction tuning."""

try:
    from importlib.metadata import version

    __version__ = version("data4ai")
except Exception:
    # Fallback for development or when package is not installed
    __version__ = "0.1.1"

__author__ = "ZySec AI"

import os
from pathlib import Path
from typing import Any, Optional

from data4ai.config import settings
from data4ai.csv_handler import CSVHandler
from data4ai.excel_handler import ExcelHandler
from data4ai.generator import DatasetGenerator
from data4ai.publisher import HuggingFacePublisher
from data4ai.schemas import AlpacaSchema, DollySchema, ShareGPTSchema
from data4ai.utils import calculate_metrics, read_jsonl


# High-level convenience functions for Python API
def generate_from_description(
    description: str,
    repo: str,
    dataset: str = "alpaca",
    count: int = 100,
    model: Optional[str] = None,
    temperature: float = 0.7,
    seed: Optional[int] = None,
    batch_size: int = 10,
    push_to_hf: bool = False,
    private: bool = False,
    hf_token: Optional[str] = None,
) -> dict[str, Any]:
    """Generate dataset from natural language description.

    Args:
        description: Natural language description of the dataset to generate
        repo: Repository/output directory name
        dataset: Dataset schema (alpaca, dolly, sharegpt)
        count: Number of examples to generate
        model: Model to use (defaults to env var)
        temperature: Sampling temperature (0.0-2.0)
        seed: Random seed for reproducibility
        batch_size: Batch size for generation
        push_to_hf: Whether to push to HuggingFace Hub
        private: Make HF dataset private
        hf_token: HuggingFace token (defaults to env var)

    Returns:
        Dictionary with generation results including:
        - row_count: Number of rows generated
        - output_path: Path to output directory
        - jsonl_path: Path to JSONL file
        - schema: Dataset schema used
        - model: Model used
        - params: Generation parameters
    """
    generator = DatasetGenerator(
        model=model,
        temperature=temperature,
        seed=seed,
    )

    output_dir = settings.output_dir / repo
    result = generator.generate_from_prompt_sync(
        description=description,
        output_dir=output_dir,
        schema_name=dataset,
        count=count,
        batch_size=batch_size,
    )

    # Add convenience fields
    result["jsonl_path"] = output_dir / "data.jsonl"
    result["schema"] = dataset
    result["model"] = model or settings.openrouter_model
    result["params"] = {
        "temperature": temperature,
        "seed": seed,
        "batch_size": batch_size,
    }

    # Push to HuggingFace if requested
    if push_to_hf:
        token = hf_token or settings.hf_token
        publisher = HuggingFacePublisher(token=token)
        url = publisher.push_dataset(
            dataset_dir=output_dir,
            repo_name=repo,
            private=private,
            description=description,
        )
        result["huggingface_url"] = url

    return result


def generate_from_excel(
    excel_path: str,
    repo: str,
    dataset: str = "alpaca",
    max_rows: Optional[int] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    seed: Optional[int] = None,
    batch_size: int = 10,
    push_to_hf: bool = False,
    private: bool = False,
) -> dict[str, Any]:
    """Generate dataset from Excel file with AI completion.

    Args:
        excel_path: Path to Excel file
        repo: Repository/output directory name
        dataset: Dataset schema (alpaca, dolly, sharegpt)
        max_rows: Maximum rows to generate
        model: Model to use (defaults to env var)
        temperature: Sampling temperature (0.0-2.0)
        seed: Random seed for reproducibility
        batch_size: Batch size for generation
        push_to_hf: Whether to push to HuggingFace Hub
        private: Make HF dataset private

    Returns:
        Dictionary with generation results
    """
    generator = DatasetGenerator(
        model=model,
        temperature=temperature,
        seed=seed,
    )

    output_dir = settings.output_dir / repo
    result = generator.generate_from_excel_sync(
        excel_path=Path(excel_path),
        output_dir=output_dir,
        schema_name=dataset,
        max_rows=max_rows,
        batch_size=batch_size,
    )

    # Add convenience fields
    result["jsonl_path"] = output_dir / "data.jsonl"
    result["schema"] = dataset
    result["model"] = model or settings.openrouter_model
    result["params"] = {
        "temperature": temperature,
        "seed": seed,
        "batch_size": batch_size,
        "max_rows": max_rows,
    }

    # Push to HuggingFace if requested
    if push_to_hf:
        publisher = HuggingFacePublisher(token=settings.hf_token)
        url = publisher.push_dataset(
            dataset_dir=output_dir,
            repo_name=repo,
            private=private,
        )
        result["huggingface_url"] = url

    return result


def create_sample_excel(path: str, dataset: str = "alpaca") -> None:
    """Create an Excel template file for the specified dataset schema.

    Args:
        path: Path where to save the Excel template
        dataset: Dataset schema (alpaca, dolly, sharegpt)
    """
    ExcelHandler.create_template(Path(path), dataset)


def create_sample_csv(path: str, dataset: str = "alpaca") -> None:
    """Create a CSV template file for the specified dataset schema.

    Args:
        path: Path where to save the CSV template
        dataset: Dataset schema (alpaca, dolly, sharegpt)
    """
    CSVHandler.create_template(Path(path), dataset)


def validate_dataset(repo: str, dataset: str = "alpaca") -> dict[str, Any]:
    """Validate dataset quality and schema compliance.

    Args:
        repo: Repository/directory name containing the dataset
        dataset: Expected dataset schema

    Returns:
        Dictionary with validation results including:
        - is_valid: Whether all examples are valid
        - total_rows: Total number of examples
        - valid_count: Number of valid examples
        - invalid_count: Number of invalid examples
        - invalid_indices: List of invalid example indices
        - quality_score: Overall quality score (0-1)
        - metrics: Dataset metrics
    """
    from data4ai.schemas import SchemaRegistry

    dataset_dir = settings.output_dir / repo
    jsonl_path = dataset_dir / "data.jsonl"

    if not jsonl_path.exists():
        raise FileNotFoundError(f"Dataset not found: {jsonl_path}")

    dataset_data = list(read_jsonl(jsonl_path))

    # Validate schema
    schema_registry = SchemaRegistry()
    valid_count = 0
    invalid_indices = []

    for i, entry in enumerate(dataset_data):
        if schema_registry.validate(entry, dataset):
            valid_count += 1
        else:
            invalid_indices.append(i)

    # Calculate metrics
    metrics = calculate_metrics(dataset_data, dataset)

    # Calculate quality score
    invalid_count = len(invalid_indices)
    quality_score = valid_count / max(len(dataset_data), 1)

    return {
        "is_valid": invalid_count == 0,
        "total_rows": len(dataset_data),
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "invalid_indices": invalid_indices[:100],  # Limit to first 100
        "quality_score": quality_score,
        "metrics": metrics,
    }


def get_dataset_stats(repo: str) -> dict[str, Any]:
    """Get statistics and metrics for a dataset.

    Args:
        repo: Repository/directory name containing the dataset

    Returns:
        Dictionary with dataset statistics including:
        - total_rows: Total number of examples
        - file_size: Size in bytes
        - schema: Detected schema type
        - metrics: Detailed metrics
    """
    dataset_dir = settings.output_dir / repo
    jsonl_path = dataset_dir / "data.jsonl"

    if not jsonl_path.exists():
        raise FileNotFoundError(f"Dataset not found: {jsonl_path}")

    dataset_data = list(read_jsonl(jsonl_path))

    # Detect schema
    schema = "alpaca"  # Default
    if dataset_data and "conversations" in dataset_data[0]:
        schema = "sharegpt"
    elif dataset_data and "response" in dataset_data[0]:
        schema = "dolly"

    # Calculate metrics
    metrics = calculate_metrics(dataset_data, schema)

    # Get file size
    file_size = jsonl_path.stat().st_size

    return {
        "total_rows": len(dataset_data),
        "file_size": file_size,
        "schema": schema,
        "metrics": metrics,
        "avg_instruction_length": metrics.get("avg_instruction_length", 0),
        "avg_output_length": metrics.get("avg_output_length", 0),
    }


class Data4AI:
    """High-level Data4AI API wrapper class for object-oriented usage."""

    def __init__(
        self,
        openrouter_api_key: Optional[str] = None,
        openrouter_model: Optional[str] = None,
        temperature: float = 0.7,
        hf_token: Optional[str] = None,
        hf_org: Optional[str] = None,
    ):
        """Initialize Data4AI with configuration.

        Args:
            openrouter_api_key: OpenRouter API key (defaults to env var)
            openrouter_model: Default model to use
            temperature: Default sampling temperature
            hf_token: HuggingFace token for publishing
            hf_org: HuggingFace organization
        """
        self.api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = openrouter_model or settings.openrouter_model
        self.temperature = temperature
        self.hf_token = hf_token or settings.hf_token
        self.hf_org = hf_org or settings.hf_organization

        # Store in environment for underlying components
        if self.api_key:
            os.environ["OPENROUTER_API_KEY"] = self.api_key
        if self.hf_token:
            os.environ["HF_TOKEN"] = self.hf_token

    def generate_from_description(
        self,
        description: str,
        repo: str,
        dataset: str = "alpaca",
        count: int = 100,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate dataset from description. See module-level function for details."""
        return generate_from_description(
            description=description,
            repo=repo,
            dataset=dataset,
            count=count,
            model=kwargs.get("model", self.model),
            temperature=kwargs.get("temperature", self.temperature),
            **{k: v for k, v in kwargs.items() if k not in ["model", "temperature"]},
        )

    def generate_from_excel(
        self, excel_path: str, repo: str, dataset: str = "alpaca", **kwargs
    ) -> dict[str, Any]:
        """Generate dataset from Excel. See module-level function for details."""
        return generate_from_excel(
            excel_path=excel_path,
            repo=repo,
            dataset=dataset,
            model=kwargs.get("model", self.model),
            temperature=kwargs.get("temperature", self.temperature),
            **{k: v for k, v in kwargs.items() if k not in ["model", "temperature"]},
        )

    def create_sample_excel(self, path: str, dataset: str = "alpaca") -> None:
        """Create Excel template. See module-level function for details."""
        return create_sample_excel(path, dataset)

    def validate_dataset(self, repo: str, dataset: str = "alpaca") -> dict[str, Any]:
        """Validate dataset. See module-level function for details."""
        return validate_dataset(repo, dataset)

    def get_dataset_stats(self, repo: str) -> dict[str, Any]:
        """Get dataset statistics. See module-level function for details."""
        return get_dataset_stats(repo)


__all__ = [
    # Core classes
    "DatasetGenerator",
    "AlpacaSchema",
    "DollySchema",
    "ShareGPTSchema",
    "Data4AI",
    # High-level functions
    "generate_from_description",
    "generate_from_excel",
    "create_sample_excel",
    "create_sample_csv",
    "validate_dataset",
    "get_dataset_stats",
    # Version
    "__version__",
]
