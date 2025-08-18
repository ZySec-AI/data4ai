"""Data schemas for different dataset formats."""

from abc import ABC, abstractmethod
from typing import Any

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
    def from_dict(cls, data: dict[str, Any]) -> "AlpacaSchema":
        """Create instance from dictionary."""
        return cls(
            instruction=data.get("instruction", ""),
            input=data.get("input", ""),
            output=data.get("output", ""),
        )


class ConversationTurn(BaseModel):
    """Single conversation turn for conversation formats."""

    from_: str = Field(
        ..., alias="from", description="Speaker role (user/assistant/system)"
    )
    value: str = Field(..., min_length=1, description="Message content")

    @field_validator("from_")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate speaker role."""
        valid_roles = ["system", "assistant", "user"]
        if v.lower() not in valid_roles:
            raise ValueError(
                f"Invalid role '{v}'. Must be one of: {', '.join(valid_roles)}"
            )
        return v.lower()

    class Config:
        populate_by_name = True


class ChatMLSchema(BaseSchema):
    """ChatML conversation format."""

    messages: list[ConversationTurn] = Field(
        ..., min_length=1, description="List of conversation messages"
    )

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v: list[ConversationTurn]) -> list[ConversationTurn]:
        """Validate message structure."""
        if len(v) < 1:
            raise ValueError("Messages must have at least 1 turn")

        # Ensure no consecutive messages from same role (except system messages)
        for i in range(1, len(v)):
            if v[i].from_ == v[i - 1].from_ and v[i].from_ != "system":
                raise ValueError(f"Consecutive messages from same role at position {i}")

        return v

    def to_jsonl_entry(self) -> dict[str, Any]:
        """Convert to JSONL format."""
        return {
            "messages": [
                {"role": turn.from_, "content": turn.value} for turn in self.messages
            ]
        }

    def validate_content(self) -> bool:
        """Validate content requirements."""
        return len(self.messages) >= 1 and all(
            turn.value.strip() for turn in self.messages
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatMLSchema":
        """Create instance from dictionary."""
        if "messages" in data:
            messages = [
                ConversationTurn(from_=msg["role"], value=msg["content"])
                for msg in data["messages"]
            ]
            # Validate that we have actual messages
            if not messages:
                raise ValueError("Messages array cannot be empty")
        else:
            # Build from simplified Excel format
            messages = []
            if data.get("system_message"):
                messages.append(
                    ConversationTurn(from_="system", value=data["system_message"])
                )
            if data.get("user_message"):
                messages.append(
                    ConversationTurn(from_="user", value=data["user_message"])
                )
            if data.get("assistant_response"):
                messages.append(
                    ConversationTurn(
                        from_="assistant", value=data["assistant_response"]
                    )
                )

        return cls(messages=messages)


class SchemaRegistry:
    """Registry for managing dataset schemas."""

    _schemas: dict[str, type[BaseSchema]] = {
        "chatml": ChatMLSchema,
        "alpaca": AlpacaSchema,
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
