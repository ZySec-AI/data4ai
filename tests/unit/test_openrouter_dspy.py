"""Tests for OpenRouter DSPy integration."""

from unittest.mock import Mock, patch

import pytest

from data4ai.integrations.openrouter_dspy import (
    OpenRouterDSPyClient,
    OpenRouterPromptOptimizer,
    configure_dspy_with_openrouter,
    create_openrouter_prompt_generator,
)


class TestOpenRouterDSPyClient:
    """Test OpenRouter DSPy client."""

    def test_client_initialization(self):
        """Test client initialization with required parameters."""
        client = OpenRouterDSPyClient(api_key="test-key")

        assert client.api_key == "test-key"
        assert client.base_url == "https://openrouter.ai/api/v1"
        assert client.model == "openai/gpt-4o-mini"
        assert client.provider == "openai"
        assert client.history == []

    def test_client_initialization_with_env_var(self):
        """Test client initialization with environment variable."""
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "env-key"}):
            client = OpenRouterDSPyClient()
            assert client.api_key == "env-key"

    def test_client_initialization_missing_api_key(self):
        """Test client initialization fails without API key."""
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ValueError, match="OpenRouter API key is required"),
        ):
            OpenRouterDSPyClient()

    def test_get_headers(self):
        """Test header generation with attribution."""
        client = OpenRouterDSPyClient(api_key="test-key")
        headers = client._get_headers()

        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"
        assert headers["HTTP-Referer"] == "https://github.com/zysec-ai/data4ai"
        assert headers["X-Title"] == "Data4AI"

    @patch("httpx.Client")
    def test_basic_request_success(self, mock_client):
        """Test successful API request."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_response.raise_for_status.return_value = None

        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        client = OpenRouterDSPyClient(api_key="test-key")
        result = client.basic_request("test prompt")

        assert result == {"choices": [{"message": {"content": "Test response"}}]}
        assert len(client.history) == 1

    @patch("httpx.Client")
    def test_basic_request_failure(self, mock_client):
        """Test API request failure."""
        mock_client_instance = Mock()
        mock_client_instance.post.side_effect = Exception("API Error")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        client = OpenRouterDSPyClient(api_key="test-key")

        with pytest.raises(Exception, match="API Error"):
            client.basic_request("test prompt")

    @patch.object(OpenRouterDSPyClient, "basic_request")
    def test_call_method(self, mock_basic_request):
        """Test DSPy LM interface call method."""
        mock_basic_request.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }

        client = OpenRouterDSPyClient(api_key="test-key")
        result = client("test prompt")

        assert result == ["Test response"]
        mock_basic_request.assert_called_once_with("test prompt")


class TestConfigureDSPyWithOpenRouter:
    """Test DSPy configuration with OpenRouter."""

    @patch("data4ai.integrations.openrouter_dspy.dspy")
    def test_configure_dspy_with_openrouter(self, mock_dspy):
        """Test DSPy configuration."""
        configure_dspy_with_openrouter(model="test-model", api_key="test-key")

        # Verify DSPy was configured
        mock_dspy.configure.assert_called_once()


class TestOpenRouterPromptOptimizer:
    """Test OpenRouter prompt optimizer."""

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    def test_optimizer_initialization(self, mock_configure):
        """Test optimizer initialization."""
        optimizer = OpenRouterPromptOptimizer(model="test-model", api_key="test-key")

        assert optimizer.model == "test-model"
        assert optimizer.api_key == "test-key"
        mock_configure.assert_called_once()

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    @patch("data4ai.integrations.openrouter_dspy.dspy")
    def test_generate_dynamic_prompt_success(self, mock_dspy, mock_configure):
        """Test successful dynamic prompt generation."""
        # Mock DSPy predictor
        mock_predictor = Mock()
        mock_result = Mock()
        mock_result.examples = "Generated examples"
        mock_predictor.return_value = mock_result
        mock_dspy.Predict.return_value = mock_predictor

        optimizer = OpenRouterPromptOptimizer(model="test-model", api_key="test-key")

        result = optimizer.generate_dynamic_prompt(
            description="test description", schema_name="alpaca", count=5
        )

        # Should now return enhanced prompt with DSPy insights
        assert isinstance(result, str)
        assert "You are a dataset generator" in result
        assert "test description" in result
        assert "alpaca" in result
        assert (
            "DSPY OPTIMIZATION INSIGHT" in result
            or "DSPy prompt generation failed" in result
        )

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    @patch("data4ai.integrations.openrouter_dspy.dspy")
    def test_generate_dynamic_prompt_fallback(self, mock_dspy, mock_configure):
        """Test fallback to static prompt on DSPy failure."""
        # Mock DSPy predictor to raise exception
        mock_predictor = Mock()
        mock_predictor.side_effect = Exception("DSPy error")
        mock_dspy.Predict.return_value = mock_predictor

        optimizer = OpenRouterPromptOptimizer(model="test-model", api_key="test-key")

        result = optimizer.generate_dynamic_prompt(
            description="test description", schema_name="alpaca", count=5
        )

        # Should return fallback prompt
        assert "You are a dataset generator" in result
        assert "alpaca" in result

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    def test_fallback_prompt_alpaca(self, mock_configure):
        """Test fallback prompt for alpaca schema."""
        optimizer = OpenRouterPromptOptimizer(model="test-model", api_key="test-key")

        result = optimizer._fallback_prompt(
            description="test description", schema_name="alpaca", count=3
        )

        assert "You are a dataset generator" in result
        assert "instruction: The task or question" in result
        assert "input: Additional context" in result
        assert "output: The expected response" in result

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    def test_fallback_prompt_chatml(self, mock_configure):
        """Test fallback prompt for chatml schema."""
        optimizer = OpenRouterPromptOptimizer(model="test-model", api_key="test-key")

        result = optimizer._fallback_prompt(
            description="test description", schema_name="chatml", count=3
        )

        assert "You are a dataset generator" in result
        assert "messages: List of messages with role and content" in result
        assert "role" in result
        assert "content" in result


class TestCreateOpenRouterPromptGenerator:
    """Test factory function for creating OpenRouter prompt generators."""

    def test_create_openrouter_prompt_generator(self):
        """Test factory function."""
        with patch(
            "data4ai.integrations.openrouter_dspy.OpenRouterPromptOptimizer"
        ) as mock_optimizer_class:
            mock_optimizer = Mock()
            mock_optimizer_class.return_value = mock_optimizer

            result = create_openrouter_prompt_generator(
                model="test-model", api_key="test-key"
            )

            assert result == mock_optimizer
            mock_optimizer_class.assert_called_once_with(
                model="test-model", api_key="test-key"
            )
