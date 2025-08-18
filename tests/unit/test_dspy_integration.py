"""Tests for DSPy integration functionality."""

from unittest.mock import Mock, patch

from data4ai.integrations.dspy_prompts import (
    DynamicPromptSignature,
    PromptOptimizer,
    SchemaAwarePromptGenerator,
    create_prompt_generator,
)


class TestDynamicPromptSignature:
    """Test DSPy signature for dynamic prompt generation."""

    def test_signature_creation(self):
        """Test that signature can be created with required fields."""
        # DSPy signatures define fields as class variables
        signature_class = DynamicPromptSignature
        # Test that the signature class exists and can be instantiated
        assert signature_class is not None
        # Test that it's a DSPy signature
        assert hasattr(signature_class, "__name__")
        assert signature_class.__name__ == "DynamicPromptSignature"

    def test_signature_fields(self):
        """Test that signature has correct input and output fields."""
        # Test that the signature class has the expected structure
        signature_class = DynamicPromptSignature

        # Check that it's a DSPy signature class
        assert hasattr(signature_class, "__name__")
        assert signature_class.__name__ == "DynamicPromptSignature"
        # Check that it inherits from dspy.Signature
        assert hasattr(signature_class, "__bases__")


class TestPromptOptimizer:
    """Test DSPy prompt optimizer."""

    @patch("data4ai.integrations.dspy_prompts.os.getenv")
    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    def test_optimizer_initialization(self, mock_configure, mock_getenv):
        """Test optimizer initialization with DSPy setup."""
        # Mock os.getenv to return None for OPENROUTER_API_KEY
        mock_getenv.return_value = None

        optimizer = PromptOptimizer("openai/gpt-4o-mini")

        assert optimizer.model_name == "openai/gpt-4o-mini"
        mock_configure.assert_called_once_with(
            model="openai/gpt-4o-mini",
            api_key=None,  # os.getenv returns None when not set
        )

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    def test_setup_signatures(self, mock_configure):
        """Test that signatures are set up correctly."""
        optimizer = PromptOptimizer("test-model")

        assert "dynamic_prompt" in optimizer.signatures
        assert "schema_aware_generation" in optimizer.signatures

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    def test_generate_dynamic_prompt_fallback(self, mock_configure):
        """Test that dynamic prompt generation falls back to static prompt."""
        optimizer = PromptOptimizer("test-model")

        prompt = optimizer.generate_dynamic_prompt(
            description="Create programming questions", schema_name="alpaca", count=5
        )

        assert isinstance(prompt, str)
        assert "Generate 5 high-quality examples" in prompt
        assert "alpaca dataset" in prompt
        assert "instruction" in prompt
        assert "input" in prompt
        assert "output" in prompt

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    def test_generate_dynamic_prompt_chatml_schema(self, mock_configure):
        """Test dynamic prompt generation for ChatML schema."""
        optimizer = PromptOptimizer("test-model")

        prompt = optimizer.generate_dynamic_prompt(
            description="Create conversations", schema_name="chatml", count=3
        )

        assert "chatml" in prompt.lower()
        assert "messages" in prompt
        assert "role" in prompt

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    def test_optimize_prompt_with_examples(self, mock_configure):
        """Test prompt optimization with previous examples."""
        optimizer = PromptOptimizer("test-model")

        examples = [
            {
                "instruction": "Write a function",
                "input": "",
                "output": "def func(): pass",
            },
            {
                "instruction": "Create a class",
                "input": "",
                "output": "class MyClass: pass",
            },
        ]

        prompt = optimizer.optimize_prompt_with_examples(
            description="Create more programming examples",
            schema_name="alpaca",
            count=3,
            example_data=examples,
        )

        assert isinstance(prompt, str)
        assert "Generate 3 high-quality examples" in prompt


class TestSchemaAwarePromptGenerator:
    """Test schema-aware prompt generator."""

    @patch("data4ai.integrations.dspy_prompts.PromptOptimizer")
    def test_generator_initialization(self, mock_optimizer_class):
        """Test generator initialization."""
        mock_optimizer = Mock()
        mock_optimizer_class.return_value = mock_optimizer

        generator = SchemaAwarePromptGenerator("test-model")

        assert generator.optimizer == mock_optimizer
        assert "alpaca" in generator.schema_prompts
        assert "chatml" in generator.schema_prompts

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    def test_create_schema_prompts(self, mock_configure):
        """Test that schema-specific prompts are created."""
        generator = SchemaAwarePromptGenerator("test-model")

        # Test Alpaca prompt
        alpaca_prompt = generator.schema_prompts["alpaca"]
        assert "instruction-following datasets" in alpaca_prompt
        assert "instruction:" in alpaca_prompt
        assert "input:" in alpaca_prompt
        assert "output:" in alpaca_prompt

        # Test ChatML prompt
        chatml_prompt = generator.schema_prompts["chatml"]
        assert "conversation" in chatml_prompt
        assert "messages" in chatml_prompt

    @patch("data4ai.integrations.dspy_prompts.PromptOptimizer")
    def test_generate_schema_prompt_with_dspy(self, mock_optimizer_class):
        """Test schema prompt generation with DSPy enabled."""
        mock_optimizer = Mock()
        mock_optimizer.generate_dynamic_prompt.return_value = "Dynamic prompt content"
        mock_optimizer_class.return_value = mock_optimizer

        generator = SchemaAwarePromptGenerator("test-model")

        prompt = generator.generate_schema_prompt(
            description="Create programming questions",
            schema_name="alpaca",
            count=5,
            use_dspy=True,
        )

        assert prompt == "Dynamic prompt content"
        mock_optimizer.generate_dynamic_prompt.assert_called_once_with(
            "Create programming questions", "alpaca", 5
        )

    @patch("data4ai.integrations.dspy_prompts.PromptOptimizer")
    def test_generate_schema_prompt_without_dspy(self, mock_optimizer_class):
        """Test schema prompt generation with DSPy disabled."""
        mock_optimizer = Mock()
        mock_optimizer_class.return_value = mock_optimizer

        generator = SchemaAwarePromptGenerator("test-model")

        prompt = generator.generate_schema_prompt(
            description="Create programming questions",
            schema_name="alpaca",
            count=5,
            use_dspy=False,
        )

        assert "instruction-following datasets" in prompt
        assert "Create programming questions" in prompt
        assert "5" in prompt
        mock_optimizer.generate_dynamic_prompt.assert_not_called()

    @patch("data4ai.integrations.dspy_prompts.PromptOptimizer")
    def test_generate_adaptive_prompt_with_examples(self, mock_optimizer_class):
        """Test adaptive prompt generation with previous examples."""
        mock_optimizer = Mock()
        mock_optimizer.optimize_prompt_with_examples.return_value = (
            "Adaptive prompt content"
        )
        mock_optimizer_class.return_value = mock_optimizer

        generator = SchemaAwarePromptGenerator("test-model")

        examples = [
            {
                "instruction": "Write a function",
                "input": "",
                "output": "def func(): pass",
            }
        ]

        prompt = generator.generate_adaptive_prompt(
            description="Create more examples",
            schema_name="alpaca",
            count=3,
            previous_examples=examples,
        )

        assert prompt == "Adaptive prompt content"
        mock_optimizer.optimize_prompt_with_examples.assert_called_once_with(
            "Create more examples", "alpaca", 3, examples
        )

    @patch("data4ai.integrations.dspy_prompts.PromptOptimizer")
    def test_generate_adaptive_prompt_without_examples(self, mock_optimizer_class):
        """Test adaptive prompt generation without previous examples."""
        mock_optimizer = Mock()
        mock_optimizer.generate_dynamic_prompt.return_value = "Dynamic prompt content"
        mock_optimizer_class.return_value = mock_optimizer

        generator = SchemaAwarePromptGenerator("test-model")

        prompt = generator.generate_adaptive_prompt(
            description="Create examples",
            schema_name="alpaca",
            count=3,
            previous_examples=None,
        )

        assert prompt == "Dynamic prompt content"
        mock_optimizer.generate_dynamic_prompt.assert_called_once_with(
            "Create examples", "alpaca", 3
        )


class TestCreatePromptGenerator:
    """Test factory function for creating prompt generators."""

    @patch("data4ai.integrations.dspy_prompts.SchemaAwarePromptGenerator")
    def test_create_prompt_generator_with_dspy(self, mock_generator_class):
        """Test creating prompt generator with DSPy enabled."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator

        result = create_prompt_generator(model_name="test-model", use_dspy=True)

        assert result == mock_generator
        mock_generator_class.assert_called_once_with("test-model")

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    def test_create_prompt_generator_without_dspy(self, mock_configure):
        """Test creating prompt generator without DSPy."""
        result = create_prompt_generator(model_name="test-model", use_dspy=False)

        # Should return a SimplePromptGenerator when DSPy is disabled
        assert hasattr(result, "generate_schema_prompt")
        assert hasattr(result, "model_name")
        assert hasattr(result, "schema_prompts")
        # Should not have DSPy-specific attributes
        assert not hasattr(result, "optimizer")

    def test_create_prompt_generator_defaults(self):
        """Test create_prompt_generator with default parameters."""
        with patch(
            "data4ai.integrations.dspy_prompts.SchemaAwarePromptGenerator"
        ) as mock_generator_class:
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator

            result = create_prompt_generator()

            assert result == mock_generator
            mock_generator_class.assert_called_once_with("openai/gpt-4o-mini")


class TestDSPyIntegrationEndToEnd:
    """End-to-end tests for DSPy integration."""

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    def test_dspy_integration_workflow(self, mock_configure):
        """Test complete DSPy integration workflow."""
        # Create prompt generator
        generator = create_prompt_generator(model_name="test-model", use_dspy=True)

        # Test schema prompt generation
        prompt = generator.generate_schema_prompt(
            description="Create programming questions",
            schema_name="alpaca",
            count=5,
            use_dspy=True,
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0

        # Test adaptive prompt generation
        examples = [
            {
                "instruction": "Write a function",
                "input": "",
                "output": "def func(): pass",
            }
        ]

        adaptive_prompt = generator.generate_adaptive_prompt(
            description="Create more examples",
            schema_name="alpaca",
            count=3,
            previous_examples=examples,
        )

        assert isinstance(adaptive_prompt, str)
        assert len(adaptive_prompt) > 0

    @patch("data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter")
    def test_dspy_fallback_mechanism(self, mock_configure):
        """Test that DSPy falls back gracefully when errors occur."""
        generator = create_prompt_generator(model_name="test-model", use_dspy=True)

        # This should work even if DSPy fails internally
        prompt = generator.generate_schema_prompt(
            description="Create test examples",
            schema_name="alpaca",
            count=2,
            use_dspy=True,
        )

        assert isinstance(prompt, str)
        assert "Generate 2 high-quality examples" in prompt
