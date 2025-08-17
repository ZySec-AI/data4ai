"""Unit tests for environment variable handling."""

import os
from unittest.mock import patch

import pytest

from data4ai.error_handler import check_environment_variables


class TestEnvironmentVariables:
    """Test environment variable checking and messaging."""

    def test_check_with_all_variables_set(self):
        """Test check when all variables are set."""
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "test-key",
                "OPENROUTER_MODEL": "test-model",
                "HF_TOKEN": "test-token",
            },
        ):
            result = check_environment_variables()

            assert result["OPENROUTER_API_KEY"] is True
            assert result["OPENROUTER_MODEL"] is True
            assert result["HF_TOKEN"] is True

    def test_check_with_missing_variables(self):
        """Test check when variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = check_environment_variables()

            # Should not raise but return status
            assert result["OPENROUTER_API_KEY"] is False
            assert result["OPENROUTER_MODEL"] is False
            assert result["HF_TOKEN"] is False

    @patch("sys.stderr")
    def test_missing_variables_output(self, mock_stderr):
        """Test that missing variables produce helpful output."""
        with patch.dict(os.environ, {}, clear=True):
            check_environment_variables(["OPENROUTER_API_KEY"])

            # Verify stderr output was called
            assert mock_stderr.write.called

            # Check that helpful messages were printed
            calls_str = str(mock_stderr.write.call_args_list)
            assert "Missing environment variables" in calls_str
            assert "export OPENROUTER_API_KEY" in calls_str
            assert "https://openrouter.ai/keys" in calls_str

    @patch("sys.stderr")
    def test_terminal_specific_guidance(self, mock_stderr):
        """Test that terminal-specific guidance is provided."""
        with patch.dict(os.environ, {}, clear=True):
            check_environment_variables(["OPENROUTER_API_KEY", "HF_TOKEN"])

            calls_str = str(mock_stderr.write.call_args_list)
            # Check for terminal-specific messages
            assert (
                "Important: Environment variables" in calls_str
                or "temporary" in calls_str
            )
            assert "~/.bashrc" in calls_str or "~/.zshrc" in calls_str

    def test_required_for_operation_filter(self):
        """Test that only required variables are checked when specified."""
        with patch.dict(os.environ, {}, clear=True), patch("sys.stderr") as mock_stderr:
            # Only check for HF_TOKEN
            check_environment_variables(["HF_TOKEN"])

            calls_str = str(mock_stderr.write.call_args_list)
            # Should only show HF_TOKEN, not OPENROUTER_API_KEY
            assert "export HF_TOKEN" in calls_str
            assert "export OPENROUTER_API_KEY" not in calls_str

    def test_no_output_when_all_set(self):
        """Test that no missing variable output when all are set."""
        with (
            patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "test-key",
                    "OPENROUTER_MODEL": "test-model",
                    "HF_TOKEN": "test-token",
                },
            ),
            patch("sys.stderr") as mock_stderr,
        ):
            check_environment_variables()

            # Should not print missing variables message
            mock_stderr.write.assert_not_called()


class TestEnvironmentIntegration:
    """Test environment variable integration with other components."""

    @patch("data4ai.config.settings")
    def test_generator_checks_environment(self, mock_settings):
        """Test that DatasetGenerator checks environment on init."""
        from data4ai.exceptions import ConfigurationError

        mock_settings.openrouter_api_key = ""

        with patch("data4ai.generator.check_environment_variables") as mock_check:
            with pytest.raises(ConfigurationError):
                from data4ai.generator import DatasetGenerator

                DatasetGenerator()

            # Verify environment check was called
            mock_check.assert_called_once_with(
                required_for_operation=["OPENROUTER_API_KEY"]
            )

    @patch("data4ai.config.settings")
    def test_publisher_checks_environment(self, mock_settings):
        """Test that HuggingFacePublisher checks environment when publishing."""
        from pathlib import Path

        from data4ai.exceptions import PublishingError
        from data4ai.publisher import HuggingFacePublisher

        publisher = HuggingFacePublisher(token=None)

        with patch("data4ai.publisher.check_environment_variables") as mock_check:
            with pytest.raises(PublishingError):
                publisher.push_dataset(Path("test"), "test-repo")

            # Verify environment check was called
            mock_check.assert_called_once_with(required_for_operation=["HF_TOKEN"])


class TestNoEnvFileReading:
    """Test that .env files are not read."""

    def test_env_file_ignored(self, tmp_path):
        """Test that .env files are completely ignored."""
        # Create a .env file
        env_file = tmp_path / ".env"
        env_file.write_text('OPENROUTER_API_KEY="from-env-file"\n')

        # Change to that directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Clear environment
            with patch.dict(os.environ, {}, clear=True):
                from data4ai.config import Settings

                # Create new settings instance
                settings = Settings()

                # Should NOT read from .env file
                assert settings.openrouter_api_key == ""
                assert settings.openrouter_api_key != "from-env-file"
        finally:
            os.chdir(original_cwd)

    def test_only_reads_environment_variables(self):
        """Test that only actual environment variables are read."""
        test_value = "from-environment-variable"

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": test_value}):
            from data4ai.config import Settings

            settings = Settings()
            assert settings.openrouter_api_key == test_value


class TestErrorMessages:
    """Test that error messages are terminal-focused."""

    def test_api_key_missing_message(self):
        """Test the API key missing error message."""
        from data4ai.error_handler import ErrorHandler

        msg = ErrorHandler.get_message("api_key_missing")

        # Check for terminal-specific content
        assert "export OPENROUTER_API_KEY" in msg
        assert "terminal" in msg.lower()
        assert "https://openrouter.ai/keys" in msg
        assert "bashrc" in msg.lower() or "zshrc" in msg.lower()

    def test_hf_token_missing_message(self):
        """Test the HuggingFace token missing error message."""
        from data4ai.error_handler import ErrorHandler

        msg = ErrorHandler.get_message("hf_token_missing")

        # Check for terminal-specific content
        assert "export HF_TOKEN" in msg
        assert "terminal" in msg.lower()
        assert "https://huggingface.co/settings/tokens" in msg
        assert "bashrc" in msg.lower() or "zshrc" in msg.lower()
