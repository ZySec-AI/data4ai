"""Pytest configuration and fixtures."""

import json
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_excel(temp_dir):
    """Create a sample Excel file for testing."""
    excel_path = temp_dir / "test.xlsx"

    data = {
        "instruction": ["What is Python?", "Explain AI", ""],
        "input": ["", "In simple terms", ""],
        "output": ["Python is a programming language", "", ""],
    }

    df = pd.DataFrame(data)
    df.to_excel(excel_path, index=False)

    return excel_path


@pytest.fixture
def sample_jsonl(temp_dir):
    """Create a sample JSONL file."""
    jsonl_path = temp_dir / "data.jsonl"

    data = [
        {
            "instruction": "What is Python?",
            "input": "",
            "output": "Python is a programming language",
        },
        {
            "instruction": "Explain AI",
            "input": "In simple terms",
            "output": "AI is artificial intelligence",
        },
    ]

    with open(jsonl_path, "w") as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")

    return jsonl_path


@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        [
                            {
                                "instruction": "Test instruction",
                                "input": "",
                                "output": "Test output",
                            }
                        ]
                    )
                }
            }
        ],
        "usage": {
            "total_tokens": 100,
        },
    }


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return "sk-test-key-123"


@pytest.fixture
def sample_alpaca_data() -> list[dict[str, Any]]:
    """Sample Alpaca format data."""
    return [
        {
            "instruction": "What is machine learning?",
            "input": "",
            "output": "Machine learning is a subset of AI...",
        },
        {
            "instruction": "Translate to French",
            "input": "Hello",
            "output": "Bonjour",
        },
    ]


@pytest.fixture
def sample_dolly_data() -> list[dict[str, Any]]:
    """Sample Dolly format data."""
    return [
        {
            "instruction": "Explain quantum computing",
            "context": "For beginners",
            "response": "Quantum computing is...",
            "category": "education",
        },
    ]


@pytest.fixture
def sample_sharegpt_data() -> list[dict[str, Any]]:
    """Sample ShareGPT format data."""
    return [
        {
            "conversations": [
                {"from": "human", "value": "Hello"},
                {"from": "gpt", "value": "Hi there!"},
            ]
        },
    ]
