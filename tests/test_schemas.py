"""Tests for schema definitions."""

import pytest
from pydantic import ValidationError

from data4ai.schemas import (
    AlpacaSchema,
    ConversationTurn,
    DollySchema,
    SchemaRegistry,
    ShareGPTSchema,
)


class TestAlpacaSchema:
    """Test Alpaca schema."""

    def test_valid_alpaca(self):
        """Test valid Alpaca format."""
        data = AlpacaSchema(
            instruction="What is Python?",
            input="",
            output="Python is a programming language",
        )

        assert data.instruction == "What is Python?"
        assert data.input == ""
        assert data.output == "Python is a programming language"
        assert data.validate_content()

    def test_alpaca_to_jsonl(self):
        """Test JSONL conversion."""
        data = AlpacaSchema(
            instruction="Test",
            input="Input",
            output="Output",
        )

        jsonl = data.to_jsonl_entry()
        assert jsonl["instruction"] == "Test"
        assert jsonl["input"] == "Input"
        assert jsonl["output"] == "Output"

    def test_alpaca_validation(self):
        """Test validation requirements."""
        with pytest.raises(ValidationError):
            AlpacaSchema(instruction="", input="", output="Test")

        with pytest.raises(ValidationError):
            AlpacaSchema(instruction="Test", input="", output="")


class TestDollySchema:
    """Test Dolly schema."""

    def test_valid_dolly(self):
        """Test valid Dolly format."""
        data = DollySchema(
            instruction="Explain AI",
            context="For beginners",
            response="AI is...",
            category="education",
        )

        assert data.instruction == "Explain AI"
        assert data.context == "For beginners"
        assert data.response == "AI is..."
        assert data.category == "education"
        assert data.validate_content()

    def test_dolly_optional_fields(self):
        """Test optional fields."""
        data = DollySchema(
            instruction="Test",
            context="",
            response="Response",
        )

        assert data.category is None
        jsonl = data.to_jsonl_entry()
        assert "category" not in jsonl


class TestShareGPTSchema:
    """Test ShareGPT schema."""

    def test_valid_sharegpt(self):
        """Test valid ShareGPT format."""
        data = ShareGPTSchema(
            conversations=[
                ConversationTurn(from_="human", value="Hello"),
                ConversationTurn(from_="gpt", value="Hi!"),
            ]
        )

        assert len(data.conversations) == 2
        assert data.conversations[0].from_ == "human"
        assert data.validate_content()

    def test_sharegpt_validation(self):
        """Test conversation validation."""
        # Too few turns
        with pytest.raises(ValidationError):
            ShareGPTSchema(
                conversations=[
                    ConversationTurn(from_="human", value="Hello"),
                ]
            )

        # Same role consecutively
        with pytest.raises(ValidationError):
            ShareGPTSchema(
                conversations=[
                    ConversationTurn(from_="human", value="Hello"),
                    ConversationTurn(from_="human", value="Again"),
                ]
            )


class TestSchemaRegistry:
    """Test schema registry."""

    def test_get_schema(self):
        """Test getting schema by name."""
        assert SchemaRegistry.get("alpaca") == AlpacaSchema
        assert SchemaRegistry.get("dolly") == DollySchema
        assert SchemaRegistry.get("sharegpt") == ShareGPTSchema

    def test_unknown_schema(self):
        """Test unknown schema handling."""
        with pytest.raises(ValueError, match="Unknown schema"):
            SchemaRegistry.get("unknown")

    def test_list_schemas(self):
        """Test listing available schemas."""
        schemas = SchemaRegistry.list_schemas()
        assert "alpaca" in schemas
        assert "dolly" in schemas
        assert "sharegpt" in schemas
