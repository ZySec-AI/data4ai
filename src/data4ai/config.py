"""Configuration management using Pydantic Settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_prefix="DATA4AI_",
        env_file=None,  # Disabled - only use environment variables from terminal
        case_sensitive=False,
        extra="ignore",
    )

    # OpenRouter configuration
    openrouter_api_key: str = Field(
        default="",
        alias="OPENROUTER_API_KEY",
        description="OpenRouter API key for model access",
    )
    openrouter_model: str = Field(
        default="openai/gpt-4o-mini",
        alias="OPENROUTER_MODEL",
        description="Default model to use for generation",
    )

    # Site attribution for analytics
    site_url: str = Field(
        default="https://github.com/zysec-ai/data4ai",
        description="Project website URL for attribution",
    )
    site_name: str = Field(
        default="Data4AI",
        description="Project name for attribution",
    )

    # HuggingFace configuration
    hf_token: Optional[str] = Field(
        default=None,
        alias="HF_TOKEN",
        description="HuggingFace token for dataset publishing",
    )
    hf_organization: str = Field(
        default="data4ai",
        alias="HF_ORG",
        description="HuggingFace organization name",
    )

    # Generation parameters
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for generation",
    )
    max_rows: int = Field(
        default=1000,
        gt=0,
        description="Maximum number of rows to generate",
    )
    batch_size: int = Field(
        default=10,
        gt=0,
        le=100,
        description="Batch size for API calls",
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility",
    )

    # Default schema
    default_schema: str = Field(
        default="chatml",
        description="Default dataset schema",
    )

    # DSPy configuration
    use_dspy: bool = Field(
        default=True,
        description="Use DSPy for dynamic prompt generation",
    )

    # Paths
    output_dir: Path = Field(
        default=Path("outputs"),
        description="Default output directory",
    )

    @field_validator("openrouter_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate OpenRouter API key format."""
        if not v:
            # Allow empty for commands that don't need API
            return v
        if not v.startswith(("sk-", "or-")):
            # Be lenient - just warn, don't fail
            return v
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @field_validator("default_schema")
    @classmethod
    def validate_schema(cls, v: str) -> str:
        """Validate schema is supported."""
        valid_schemas = ["chatml", "alpaca"]
        if v.lower() not in valid_schemas:
            raise ValueError(
                f"Invalid schema '{v}'. Must be one of: {', '.join(valid_schemas)}"
            )
        return v.lower()

    def get_config_path(self) -> Path:
        """Get path to configuration file."""
        return Path.home() / ".data4ai" / "config.yaml"

    def load_from_yaml(self, path: Optional[Path] = None) -> None:
        """Load configuration from YAML file."""
        import yaml

        config_path = path or self.get_config_path()
        if config_path.exists():
            with open(config_path) as f:
                config_data = yaml.safe_load(f)

            # Update settings with YAML data
            if config_data:
                # Handle nested configuration
                if "openrouter" in config_data:
                    for key, value in config_data["openrouter"].items():
                        if key == "site_url":
                            self.site_url = value
                        elif key == "site_name":
                            self.site_name = value
                        elif hasattr(self, f"openrouter_{key}"):
                            setattr(self, f"openrouter_{key}", value)

                # Handle other top-level keys
                for key, value in config_data.items():
                    if key not in ["openrouter", "huggingface", "defaults"] and hasattr(
                        self, key
                    ):
                        setattr(self, key, value)

    def save_to_yaml(self, path: Optional[Path] = None) -> None:
        """Save current configuration to YAML file."""
        import yaml

        config_path = path or self.get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            "openrouter": {
                "api_key": self.openrouter_api_key,
                "model": self.openrouter_model,
                "temperature": self.temperature,
                "site_url": self.site_url,
                "site_name": self.site_name,
            },
            "huggingface": {
                "token": self.hf_token,
                "organization": self.hf_organization,
            },
            "defaults": {
                "schema": self.default_schema,
                "max_rows": self.max_rows,
                "batch_size": self.batch_size,
                "seed": self.seed,
            },
        }

        with open(config_path, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False)


# Singleton instance
settings = Settings()
