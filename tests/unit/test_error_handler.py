"""Unit tests for error handler module."""

from unittest.mock import Mock, patch

import httpx
import pytest

from data4ai.error_handler import (
    ErrorHandler,
    UserFriendlyError,
    async_error_handler,
    error_handler,
)
from data4ai.exceptions import ConfigurationError, GenerationError, ValidationError


class TestErrorHandler:
    """Test error handler functionality."""

    def test_get_message_known_error(self):
        """Test getting message for known error."""
        msg = ErrorHandler.get_message("api_key_missing")
        assert "OpenRouter API key not configured" in msg

        msg = ErrorHandler.get_message("file_not_found", path="/test/file.txt")
        assert "/test/file.txt" in msg

    def test_get_message_unknown_error(self):
        """Test fallback for unknown error."""
        msg = ErrorHandler.get_message("unknown_error_key", error="Something bad")
        assert "unexpected error" in msg.lower()
        assert "Something bad" in msg

    @patch("data4ai.error_handler.err_console")
    def test_handle_api_error_401(self, mock_console):
        """Test handling 401 authentication error."""
        response = Mock(status_code=401)
        error = httpx.HTTPStatusError("", request=Mock(), response=response)

        ErrorHandler.handle_api_error(error)

        mock_console.print.assert_called()
        call_args = str(mock_console.print.call_args)
        assert "Invalid OpenRouter API key" in call_args

    @patch("data4ai.error_handler.err_console")
    def test_handle_api_error_429(self, mock_console):
        """Test handling 429 rate limit error."""
        response = Mock(status_code=429)
        error = httpx.HTTPStatusError("", request=Mock(), response=response)

        ErrorHandler.handle_api_error(error)

        mock_console.print.assert_called()
        call_args = str(mock_console.print.call_args)
        assert "Rate limit" in call_args

    @patch("data4ai.error_handler.err_console")
    def test_handle_api_error_timeout(self, mock_console):
        """Test handling timeout error."""
        error = httpx.TimeoutException("Timeout")

        ErrorHandler.handle_api_error(error)

        mock_console.print.assert_called()
        call_args = str(mock_console.print.call_args)
        assert "timeout" in call_args.lower()

    @patch("data4ai.error_handler.err_console")
    def test_handle_file_error_not_found(self, mock_console):
        """Test handling file not found error."""
        error = FileNotFoundError("File not found")

        ErrorHandler.handle_file_error(error, path="/test.txt")

        mock_console.print.assert_called()
        call_args = str(mock_console.print.call_args)
        assert "File not found" in call_args
        assert "/test.txt" in call_args

    @patch("data4ai.error_handler.err_console")
    def test_handle_validation_error(self, mock_console):
        """Test handling validation error."""
        error = ValidationError("Invalid data format")

        ErrorHandler.handle_validation_error(error)

        mock_console.print.assert_called()
        call_args = str(mock_console.print.call_args)
        assert "Validation error" in call_args
        assert "Invalid data format" in call_args

    @patch("data4ai.error_handler.err_console")
    def test_handle_generation_error(self, mock_console):
        """Test handling generation error."""
        error = GenerationError("Failed to generate")

        ErrorHandler.handle_generation_error(error)

        mock_console.print.assert_called()
        call_args = str(mock_console.print.call_args)
        assert "Failed to generate" in call_args


class TestErrorDecorator:
    """Test error handler decorator."""

    @patch("data4ai.error_handler.err_console")
    def test_decorator_catches_configuration_error(self, mock_console):
        """Test decorator catches configuration errors."""

        @error_handler
        def failing_function():
            raise ConfigurationError("Bad config")

        with pytest.raises(SystemExit) as exc_info:
            failing_function()

        assert exc_info.value.code == 1
        mock_console.print.assert_called()

    @patch("data4ai.error_handler.err_console")
    def test_decorator_catches_keyboard_interrupt(self, mock_console):
        """Test decorator handles keyboard interrupt."""

        @error_handler
        def interrupted_function():
            raise KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            interrupted_function()

        assert exc_info.value.code == 130  # Standard SIGINT exit code
        mock_console.print.assert_called()
        call_args = str(mock_console.print.call_args)
        assert "cancelled" in call_args.lower()

    @patch("data4ai.error_handler.err_console")
    def test_decorator_catches_file_error(self, mock_console):
        """Test decorator catches file errors."""

        @error_handler
        def file_function():
            raise FileNotFoundError("Missing file")

        with pytest.raises(SystemExit) as exc_info:
            file_function()

        assert exc_info.value.code == 1
        mock_console.print.assert_called()

    def test_decorator_allows_success(self):
        """Test decorator doesn't interfere with successful execution."""

        @error_handler
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"


class TestAsyncErrorDecorator:
    """Test async error handler decorator."""

    @pytest.mark.asyncio
    @patch("data4ai.error_handler.err_console")
    async def test_async_decorator_catches_errors(self, mock_console):
        """Test async decorator catches errors."""

        @async_error_handler
        async def async_failing_function():
            raise ValidationError("Async validation error")

        with pytest.raises(ValidationError):
            await async_failing_function()

        mock_console.print.assert_called()

    @pytest.mark.asyncio
    async def test_async_decorator_allows_success(self):
        """Test async decorator doesn't interfere with success."""

        @async_error_handler
        async def async_successful_function():
            return "async success"

        result = await async_successful_function()
        assert result == "async success"


class TestUserFriendlyError:
    """Test user-friendly exception class."""

    def test_basic_message(self):
        """Test basic exception message."""
        exc = UserFriendlyError("Something went wrong")
        assert str(exc) == "Something went wrong"

    def test_error_key_message(self):
        """Test exception with error key."""
        exc = UserFriendlyError("Fallback message", error_key="api_key_missing")
        assert "OpenRouter API key" in str(exc)

    def test_formatted_message(self):
        """Test exception with formatted message."""
        exc = UserFriendlyError(
            "Fallback", error_key="file_not_found", path="/test.txt"
        )
        assert "/test.txt" in str(exc)

    @patch("data4ai.error_handler.err_console")
    def test_display_method(self, mock_console):
        """Test display method."""
        exc = UserFriendlyError("Display this error")
        exc.display()

        mock_console.print.assert_called_with("Display this error", style="red")
