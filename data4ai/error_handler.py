"""Comprehensive error handling for Data4AI."""

import logging
import os
import sys
from functools import wraps
from typing import Any, Callable, Optional

import httpx
import typer
from rich.console import Console

from data4ai.exceptions import ConfigurationError, GenerationError, ValidationError

logger = logging.getLogger("data4ai")
console = Console()
# Create a separate console for error messages that goes to stderr
err_console = Console(stderr=True)


class ErrorHandler:
    """Centralized error handling with user-friendly messages."""

    ERROR_MESSAGES = {
        # API Errors
        "api_key_missing": '❌ OpenRouter API key not configured.\n\n📋 To set it in your terminal, run:\nexport OPENROUTER_API_KEY="your-api-key-here"\n\n💡 Get your API key from: https://openrouter.ai/keys\n⚠️  Remember: This needs to be set in each new terminal session\n   For permanent setup, add it to your ~/.bashrc or ~/.zshrc file',
        "api_key_invalid": "❌ Invalid OpenRouter API key. Please check your credentials.",
        "rate_limit": "⚠️ Rate limit exceeded. Waiting before retrying...",
        "model_not_found": "❌ Model '{model}' not found. Use 'data4ai list-models' to see available models.",
        "api_timeout": "⏱️ API request timed out. Try reducing batch size or increasing timeout.",
        "api_connection": "🌐 Cannot connect to OpenRouter API. Check your internet connection.",
        # File Errors
        "file_not_found": "❌ File not found: {path}",
        "file_permission": "❌ Permission denied accessing file: {path}",
        "invalid_format": "❌ Invalid file format. Expected {expected}, got {actual}.",
        "empty_file": "❌ File is empty: {path}",
        "corrupted_file": "❌ File appears to be corrupted: {path}",
        # Schema Errors
        "schema_not_found": "❌ Unknown schema: {schema}. Available: chatml, alpaca",
        "schema_mismatch": "❌ Data doesn't match {schema} schema. Missing columns: {columns}",
        "invalid_data": "❌ Invalid data in row {row}: {error}",
        # Document Processing Errors
        "document_parse_error": "❌ Failed to parse document: {error}",
        "unsupported_format": "❌ Unsupported document format: {format}",
        # Generation Errors
        "generation_failed": "❌ Failed to generate dataset: {error}",
        "parsing_failed": "⚠️ Failed to parse AI response for {count} items.",
        "batch_failed": "⚠️ Batch {batch} failed: {error}",
        # Configuration Errors
        "config_invalid": "❌ Invalid configuration: {error}",
        "config_missing": "❌ Missing required configuration: {field}",
        # HuggingFace Errors
        "hf_token_missing": '❌ HuggingFace token not configured.\n\n📋 To set it in your terminal, run:\nexport HF_TOKEN="your-huggingface-token-here"\n\n💡 Get your token from: https://huggingface.co/settings/tokens\n⚠️  Remember: This needs to be set in each new terminal session\n   For permanent setup, add it to your ~/.bashrc or ~/.zshrc file',
        "hf_push_failed": "❌ Failed to push to HuggingFace: {error}",
        "hf_repo_exists": "⚠️ Repository already exists. Use --overwrite to replace.",
        # General Errors
        "unexpected_error": "❌ An unexpected error occurred: {error}",
        "invalid_input": "❌ Invalid input: {error}",
        "operation_cancelled": "⚠️ Operation cancelled by user.",
    }

    @staticmethod
    def get_message(error_key: str, **kwargs) -> str:
        """Get formatted error message."""
        template = ErrorHandler.ERROR_MESSAGES.get(
            error_key, ErrorHandler.ERROR_MESSAGES["unexpected_error"]
        )
        return template.format(**kwargs)

    @staticmethod
    def handle_api_error(error: Exception) -> None:
        """Handle API-related errors with user-friendly messages."""
        if isinstance(error, httpx.HTTPStatusError):
            status = error.response.status_code

            if status == 401:
                err_console.print(
                    ErrorHandler.get_message("api_key_invalid"), style="red"
                )
            elif status == 404:
                # Try to extract model name from error
                err_console.print(
                    ErrorHandler.get_message("model_not_found", model="unknown"),
                    style="red",
                )
            elif status == 429:
                err_console.print(
                    ErrorHandler.get_message("rate_limit"), style="yellow"
                )
            elif status >= 500:
                err_console.print(
                    f"❌ OpenRouter API error (status {status}). Please try again later.",
                    style="red",
                )
            else:
                err_console.print(
                    f"❌ API error (status {status}): {error}", style="red"
                )

        elif isinstance(error, httpx.TimeoutException):
            err_console.print(ErrorHandler.get_message("api_timeout"), style="red")

        elif isinstance(error, httpx.ConnectError):
            err_console.print(ErrorHandler.get_message("api_connection"), style="red")

        else:
            err_console.print(
                ErrorHandler.get_message("unexpected_error", error=str(error)),
                style="red",
            )

    @staticmethod
    def handle_file_error(error: Exception, path: Optional[str] = None) -> None:
        """Handle file-related errors."""
        if isinstance(error, FileNotFoundError):
            err_console.print(
                ErrorHandler.get_message("file_not_found", path=path or "unknown"),
                style="red",
            )
        elif isinstance(error, PermissionError):
            err_console.print(
                ErrorHandler.get_message("file_permission", path=path or "unknown"),
                style="red",
            )
        else:
            err_console.print(f"❌ File error: {error}", style="red")

    @staticmethod
    def handle_validation_error(error: ValidationError) -> None:
        """Handle validation errors."""
        err_console.print(f"❌ Validation error: {error}", style="red")

    @staticmethod
    def handle_generation_error(error: GenerationError) -> None:
        """Handle generation errors."""
        # The GenerationError already has a user-friendly message, just print it
        err_console.print(f"❌ {str(error)}", style="red")

    @staticmethod
    def handle_configuration_error(error: ConfigurationError) -> None:
        """Handle configuration errors."""
        err_console.print(
            ErrorHandler.get_message("config_invalid", error=str(error)), style="red"
        )


def error_handler(func: Callable) -> Callable:
    """Decorator for comprehensive error handling."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            err_console.print(
                "\n" + ErrorHandler.get_message("operation_cancelled"), style="yellow"
            )
            sys.exit(130)  # Standard exit code for SIGINT
        except ConfigurationError as e:
            ErrorHandler.handle_configuration_error(e)
            sys.exit(1)
        except ValidationError as e:
            ErrorHandler.handle_validation_error(e)
            sys.exit(1)
        except GenerationError as e:
            ErrorHandler.handle_generation_error(e)
            sys.exit(1)
        except (httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError) as e:
            ErrorHandler.handle_api_error(e)
            sys.exit(1)
        except (FileNotFoundError, PermissionError) as e:
            ErrorHandler.handle_file_error(e)
            sys.exit(1)
        except typer.Exit:
            # Re-raise typer.Exit without additional handling
            raise
        except Exception as e:
            logger.exception("Unexpected error")
            err_console.print(
                ErrorHandler.get_message("unexpected_error", error=str(e)), style="red"
            )
            err_console.print(
                "\n💡 For more details, run with --verbose flag", style="dim"
            )
            sys.exit(1)

    return wrapper


def async_error_handler(func: Callable) -> Callable:
    """Decorator for async functions with comprehensive error handling."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except KeyboardInterrupt:
            err_console.print(
                "\n" + ErrorHandler.get_message("operation_cancelled"), style="yellow"
            )
            sys.exit(130)
        except ConfigurationError as e:
            ErrorHandler.handle_configuration_error(e)
            raise
        except ValidationError as e:
            ErrorHandler.handle_validation_error(e)
            raise
        except GenerationError as e:
            ErrorHandler.handle_generation_error(e)
            raise
        except (httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError) as e:
            ErrorHandler.handle_api_error(e)
            raise
        except (FileNotFoundError, PermissionError) as e:
            ErrorHandler.handle_file_error(e)
            raise
        except Exception as e:
            logger.exception("Unexpected error")
            err_console.print(
                ErrorHandler.get_message("unexpected_error", error=str(e)), style="red"
            )
            raise

    return wrapper


class UserFriendlyError(Exception):
    """Base class for exceptions with user-friendly messages."""

    def __init__(self, message: str, error_key: Optional[str] = None, **kwargs):
        """Initialize with message and optional error key."""
        self.error_key = error_key
        self.kwargs = kwargs

        if error_key:
            user_message = ErrorHandler.get_message(error_key, **kwargs)
            super().__init__(user_message)
        else:
            super().__init__(message)

    def display(self) -> None:
        """Display the error message to user."""
        err_console.print(str(self), style="red")


def check_environment_variables(
    required_for_operation: Optional[list[str]] = None,
) -> dict[str, bool]:
    """Check environment variables and provide helpful export commands.

    Args:
        required_for_operation: List of required env vars for the current operation

    Returns:
        Dict mapping variable names to whether they're set
    """
    import sys

    env_vars = {
        "OPENROUTER_API_KEY": {
            "set": bool(os.getenv("OPENROUTER_API_KEY")),
            "example": 'export OPENROUTER_API_KEY="sk-or-v1-your-api-key-here"',
            "help_url": "https://openrouter.ai/keys",
            "description": "OpenRouter API key for model access",
        },
        "OPENROUTER_MODEL": {
            "set": bool(os.getenv("OPENROUTER_MODEL")),
            "example": 'export OPENROUTER_MODEL="openai/gpt-4o-mini"',
            "help_url": "https://openrouter.ai/models",
            "description": "Model to use for generation (optional, defaults to openai/gpt-4o-mini)",
        },
        "HF_TOKEN": {
            "set": bool(os.getenv("HF_TOKEN")),
            "example": 'export HF_TOKEN="hf_your-token-here"',
            "help_url": "https://huggingface.co/settings/tokens",
            "description": "HuggingFace token for dataset publishing (optional)",
        },
    }

    missing_vars = []
    for var_name, var_info in env_vars.items():
        if not var_info["set"] and (
            required_for_operation is None or var_name in (required_for_operation or [])
        ):
            missing_vars.append((var_name, var_info))

    if missing_vars:
        # Use sys.stderr.write directly for better compatibility with uv run
        sys.stderr.write("\n📦 Missing environment variables detected:\n\n")
        sys.stderr.write("📋 Run these commands in your terminal to set them:\n\n")

        for _var_name, var_info in missing_vars:
            sys.stderr.write(f"# {var_info['description']}\n")
            sys.stderr.write(f"{var_info['example']}\n")
            sys.stderr.write(f"# Get your key from: {var_info['help_url']}\n\n")

        sys.stderr.write(
            "⚠️  Important: Environment variables set with 'export' are temporary\n"
        )
        sys.stderr.write("   They will be lost when you close your terminal\n\n")
        sys.stderr.write("💡 For permanent setup, add these exports to:\n")
        sys.stderr.write("   - ~/.bashrc (for Bash)\n")
        sys.stderr.write("   - ~/.zshrc (for Zsh/macOS)\n")
        sys.stderr.write("   - ~/.profile (for general shell)\n\n")

        # Force flush to ensure output is visible before exit
        sys.stderr.flush()

        return {var: info["set"] for var, info in env_vars.items()}

    return {var: info["set"] for var, info in env_vars.items()}
