"""Tests for schema definitions."""

import pytest
from pydantic import ValidationError

from data4ai.schemas import AlpacaSchema, ChatMLSchema, ConversationTurn, SchemaRegistry


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


class TestChatMLSchema:
    """Test ChatML schema."""

    def test_valid_chatml(self):
        """Test valid ChatML format."""
        data = ChatMLSchema(
            messages=[
                ConversationTurn(from_="user", value="Hello"),
                ConversationTurn(from_="assistant", value="Hi!"),
            ]
        )

        assert len(data.messages) == 2
        assert data.messages[0].from_ == "user"
        assert data.validate_content()

    def test_chatml_to_jsonl(self):
        """Test JSONL conversion."""
        data = ChatMLSchema(
            messages=[
                ConversationTurn(from_="user", value="Test"),
                ConversationTurn(from_="assistant", value="Response"),
            ]
        )

        jsonl = data.to_jsonl_entry()
        assert jsonl["messages"][0]["role"] == "user"
        assert jsonl["messages"][0]["content"] == "Test"
        assert jsonl["messages"][1]["role"] == "assistant"
        assert jsonl["messages"][1]["content"] == "Response"

    def test_chatml_validation(self):
        """Test message validation."""
        # Empty messages
        with pytest.raises(ValidationError):
            ChatMLSchema(messages=[])

        # Same role consecutively (except system)
        with pytest.raises(ValidationError):
            ChatMLSchema(
                messages=[
                    ConversationTurn(from_="user", value="Hello"),
                    ConversationTurn(from_="user", value="Again"),
                ]
            )

        # System messages can be consecutive
        data = ChatMLSchema(
            messages=[
                ConversationTurn(from_="system", value="System 1"),
                ConversationTurn(from_="system", value="System 2"),
                ConversationTurn(from_="user", value="Hello"),
                ConversationTurn(from_="assistant", value="Hi"),
            ]
        )
        assert data.validate_content()


class TestSchemaRegistry:
    """Test schema registry."""

    def test_get_schema(self):
        """Test getting schema by name."""
        assert SchemaRegistry.get("alpaca") == AlpacaSchema
        assert SchemaRegistry.get("chatml") == ChatMLSchema

    def test_unknown_schema(self):
        """Test unknown schema handling."""
        with pytest.raises(ValueError, match="Unknown schema"):
            SchemaRegistry.get("unknown")

    def test_list_schemas(self):
        """Test listing available schemas."""
        schemas = SchemaRegistry.list_schemas()
        assert "alpaca" in schemas
        assert "chatml" in schemas
        assert len(schemas) == 2  # Only 2 schemas now
