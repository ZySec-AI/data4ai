"""Data schemas for different dataset formats."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class BaseSchema(BaseModel, ABC):
    """Base class for all dataset schemas."""

    @abstractmethod
    def to_jsonl_entry(self) -> dict[str, Any]:
        """Convert to JSONL format."""
        pass

    @abstractmethod
    def validate_content(self) -> bool:
        """Validate content requirements."""
        pass

    @classmethod
    @abstractmethod
    def get_columns(cls) -> list[str]:
        """Get column names for Excel template."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseSchema":
        """Create instance from dictionary."""
        pass


class AlpacaSchema(BaseSchema):
    """Alpaca instruction-tuning format."""

    instruction: str = Field(..., min_length=1, description="The instruction/prompt")
    input: str = Field(default="", description="Optional input context")
    output: str = Field(..., min_length=1, description="The expected output/response")

    @field_validator("instruction", "output")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure instruction and output are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()

    def to_jsonl_entry(self) -> dict[str, Any]:
        """Convert to JSONL format."""
        return {
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output,
        }

    def validate_content(self) -> bool:
        """Validate content requirements."""
        return bool(self.instruction and self.output)

    @classmethod
    def get_columns(cls) -> list[str]:
        """Get column names for Excel template."""
        return ["instruction", "input", "output"]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlpacaSchema":
        """Create instance from dictionary."""
        return cls(
            instruction=data.get("instruction", ""),
            input=data.get("input", ""),
            output=data.get("output", ""),
        )


class DollySchema(BaseSchema):
    """Dolly instruction-tuning format."""

    instruction: str = Field(..., min_length=1, description="The instruction/prompt")
    context: str = Field(default="", description="Context or background information")
    response: str = Field(
        ..., min_length=1, description="The response to the instruction"
    )
    category: Optional[str] = Field(default=None, description="Optional category/type")

    @field_validator("instruction", "response")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure required fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()

    def to_jsonl_entry(self) -> dict[str, Any]:
        """Convert to JSONL format."""
        entry = {
            "instruction": self.instruction,
            "context": self.context,
            "response": self.response,
        }
        if self.category:
            entry["category"] = self.category
        return entry

    def validate_content(self) -> bool:
        """Validate content requirements."""
        return bool(self.instruction and self.response)

    @classmethod
    def get_columns(cls) -> list[str]:
        """Get column names for Excel template."""
        return ["instruction", "context", "response", "category"]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DollySchema":
        """Create instance from dictionary."""
        return cls(
            instruction=data.get("instruction", ""),
            context=data.get("context", ""),
            response=data.get("response", ""),
            category=data.get("category"),
        )


class ConversationTurn(BaseModel):
    """Single conversation turn for ShareGPT format."""

    from_: str = Field(..., alias="from", description="Speaker role (human/gpt)")
    value: str = Field(..., min_length=1, description="Message content")

    @field_validator("from_")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate speaker role."""
        valid_roles = ["human", "gpt", "system", "assistant", "user"]
        if v.lower() not in valid_roles:
            raise ValueError(
                f"Invalid role '{v}'. Must be one of: {', '.join(valid_roles)}"
            )
        return v.lower()

    class Config:
        populate_by_name = True


class ShareGPTSchema(BaseSchema):
    """ShareGPT conversation format."""

    conversations: list[ConversationTurn] = Field(
        ..., min_length=2, description="List of conversation turns"
    )

    @field_validator("conversations")
    @classmethod
    def validate_conversations(
        cls, v: list[ConversationTurn]
    ) -> list[ConversationTurn]:
        """Validate conversation structure."""
        if len(v) < 2:
            raise ValueError("Conversations must have at least 2 turns")

        # Ensure alternating roles
        for i in range(1, len(v)):
            if v[i].from_ == v[i - 1].from_:
                raise ValueError(f"Consecutive messages from same role at position {i}")

        return v

    def to_jsonl_entry(self) -> dict[str, Any]:
        """Convert to JSONL format."""
        return {
            "conversations": [
                {"from": turn.from_, "value": turn.value} for turn in self.conversations
            ]
        }

    def validate_content(self) -> bool:
        """Validate content requirements."""
        return len(self.conversations) >= 2 and all(
            turn.value.strip() for turn in self.conversations
        )

    @classmethod
    def get_columns(cls) -> list[str]:
        """Get column names for Excel template."""
        # For Excel, we'll use a simplified format
        return ["human_message", "assistant_response", "conversation_continues"]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ShareGPTSchema":
        """Create instance from dictionary."""
        if "conversations" in data:
            conversations = [
                ConversationTurn(from_=turn["from"], value=turn["value"])
                for turn in data["conversations"]
            ]
        else:
            # Build from simplified Excel format
            conversations = []
            if data.get("human_message"):
                conversations.append(
                    ConversationTurn(from_="human", value=data["human_message"])
                )
            if data.get("assistant_response"):
                conversations.append(
                    ConversationTurn(from_="gpt", value=data["assistant_response"])
                )

        return cls(conversations=conversations)


class SchemaRegistry:
    """Registry for managing dataset schemas."""

    _schemas: dict[str, type[BaseSchema]] = {
        "alpaca": AlpacaSchema,
        "dolly": DollySchema,
        "sharegpt": ShareGPTSchema,
    }

    @classmethod
    def get(cls, name: str) -> type[BaseSchema]:
        """Get schema class by name."""
        schema_name = name.lower()
        if schema_name not in cls._schemas:
            available = ", ".join(cls._schemas.keys())
            raise ValueError(f"Unknown schema '{name}'. Available: {available}")
        return cls._schemas[schema_name]

    @classmethod
    def register(cls, name: str, schema_class: type[BaseSchema]) -> None:
        """Register a new schema."""
        cls._schemas[name.lower()] = schema_class

    @classmethod
    def list_schemas(cls) -> list[str]:
        """List all available schemas."""
        return list(cls._schemas.keys())

    @classmethod
    def validate(cls, data: dict[str, Any], schema_name: str) -> bool:
        """Validate data against a schema."""
        try:
            schema_class = cls.get(schema_name)
            instance = schema_class.from_dict(data)
            return instance.validate_content()
        except Exception:
            return False
