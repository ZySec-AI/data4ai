"""Unit tests for CLI env command."""

import os
from unittest.mock import patch

from typer.testing import CliRunner

from data4ai.cli import app


class TestEnvCommand:
    """Test the env CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_env_check_all_set(self):
        """Test env --check when all variables are set."""
        with (
            patch.dict(
                os.environ, {"OPENROUTER_API_KEY": "test-key", "HF_TOKEN": "test-token"}
            ),
            patch("data4ai.config.settings") as mock_settings,
        ):
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_model = "default-model"
            mock_settings.hf_token = "test-token"

            result = self.runner.invoke(app, ["env", "--check"])
            assert result.exit_code == 0
            assert "All environment variables are configured" in result.output

    def test_env_check_missing_variables(self):
        """Test env --check when variables are missing."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("data4ai.config.settings") as mock_settings,
        ):
            mock_settings.openrouter_api_key = ""
            mock_settings.openrouter_model = "default-model"
            mock_settings.hf_token = None

            result = self.runner.invoke(app, ["env", "--check"])
            assert result.exit_code == 0
            assert "Missing environment variables" in result.output
            assert "Run 'data4ai env --export'" in result.output

    def test_env_export_shows_commands(self):
        """Test env --export shows export commands."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("data4ai.config.settings") as mock_settings,
        ):
            mock_settings.openrouter_api_key = ""
            mock_settings.openrouter_model = ""
            mock_settings.hf_token = None

            result = self.runner.invoke(app, ["env", "--export"])
            assert result.exit_code == 0
            assert "export OPENROUTER_API_KEY=" in result.output
            assert "export HF_TOKEN=" in result.output
            assert "sk-or-v1-your-api-key-here" in result.output
            assert "hf_your-token-here" in result.output

    def test_env_shows_table_with_check(self):
        """Test that env --check shows status table."""
        with (
            patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=True),
            patch("data4ai.config.settings") as mock_settings,
        ):
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_model = "default"
            mock_settings.hf_token = None

            result = self.runner.invoke(app, ["env", "--check"])
            assert result.exit_code == 0
            # Should show environment status table
            assert "Environment Status" in result.output
            assert "OPENROUTER_API_KEY" in result.output
            assert "✅" in result.output  # For set variable
            assert "❌" in result.output  # For unset variable

    def test_env_shell_specific_guidance(self):
        """Test that shell-specific guidance is provided."""
        with (
            patch.dict(
                os.environ,
                {"SHELL": "/bin/zsh", "OPENROUTER_API_KEY": "", "HF_TOKEN": ""},
                clear=True,
            ),
            patch("data4ai.config.settings") as mock_settings,
        ):
            mock_settings.openrouter_api_key = ""
            mock_settings.openrouter_model = ""
            mock_settings.hf_token = None

            result = self.runner.invoke(app, ["env", "--export"])
            assert result.exit_code == 0
            # Should show export commands when vars are missing
            assert "export" in result.output

    def test_env_bash_shell_guidance(self):
        """Test guidance for bash shell."""
        with (
            patch.dict(
                os.environ,
                {"SHELL": "/bin/bash", "OPENROUTER_API_KEY": "", "HF_TOKEN": ""},
                clear=True,
            ),
            patch("data4ai.config.settings") as mock_settings,
        ):
            mock_settings.openrouter_api_key = ""
            mock_settings.openrouter_model = ""
            mock_settings.hf_token = None

            result = self.runner.invoke(app, ["env", "--export"])
            assert result.exit_code == 0
            # Should show export commands when vars are missing
            assert "export" in result.output

    def test_env_shows_setup_script_option(self):
        """Test that env command mentions setup_env.sh script."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("data4ai.config.settings") as mock_settings,
        ):
            mock_settings.openrouter_api_key = ""
            mock_settings.openrouter_model = ""
            mock_settings.hf_token = None

            result = self.runner.invoke(app, ["env", "--export"])
            assert result.exit_code == 0
            assert "setup_env.sh" in result.output

    def test_env_shows_permanent_setup_instructions(self):
        """Test that permanent setup instructions are shown."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("data4ai.config.settings") as mock_settings,
        ):
            mock_settings.openrouter_api_key = ""
            mock_settings.openrouter_model = ""
            mock_settings.hf_token = None

            result = self.runner.invoke(app, ["env", "--export"])
            assert result.exit_code == 0
            # Should show how to make exports permanent
            assert "permanent" in result.output.lower()
            assert "echo" in result.output
            assert ">>" in result.output

    def test_env_masks_sensitive_values(self):
        """Test that sensitive values are masked."""
        with (
            patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "actual-secret-key-12345",
                    "HF_TOKEN": "actual-hf-token-67890",
                },
            ),
            patch("data4ai.config.settings") as mock_settings,
        ):
            mock_settings.openrouter_api_key = "actual-secret-key-12345"
            mock_settings.hf_token = "actual-hf-token-67890"
            mock_settings.openrouter_model = "test-model"

            result = self.runner.invoke(app, ["env", "--check"])
            assert result.exit_code == 0
            # Should not show actual keys
            assert "actual-secret-key-12345" not in result.output
            assert "actual-hf-token-67890" not in result.output
            # Should show masked values
            assert "***" in result.output

    def test_env_shows_model_value(self):
        """Test that model value is shown (not sensitive)."""
        with (
            patch.dict(os.environ, {"OPENROUTER_MODEL": "openai/gpt-4o-mini"}),
            patch("data4ai.config.settings") as mock_settings,
        ):
            mock_settings.openrouter_api_key = ""
            mock_settings.openrouter_model = "openai/gpt-4o-mini"
            mock_settings.hf_token = None

            result = self.runner.invoke(app, ["env", "--check"])
            assert result.exit_code == 0
            # Model name should be visible (not sensitive)
            assert "openai/gpt-4o-mini" in result.output


class TestEnvCommandIntegration:
    """Test env command integration with other commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_prompt_command_checks_env(self):
        """Test that prompt command checks environment."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("data4ai.config.settings") as mock_settings,
        ):
            mock_settings.openrouter_api_key = ""

            result = self.runner.invoke(
                app,
                ["prompt", "--repo", "test", "--description", "test", "--count", "1"],
            )
            # Should fail and show environment help
            assert result.exit_code != 0
            assert "Missing environment variables" in result.output

    def test_run_command_checks_env(self):
        """Test that run command checks environment."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("data4ai.config.settings") as mock_settings,
        ):
            mock_settings.openrouter_api_key = ""

            # Create a dummy file
            with self.runner.isolated_filesystem():
                with open("test.xlsx", "w") as f:
                    f.write("test")

                result = self.runner.invoke(app, ["run", "test.xlsx", "--repo", "test"])
                # Should fail and show environment help
                assert result.exit_code != 0
                assert "Missing environment variables" in result.output
