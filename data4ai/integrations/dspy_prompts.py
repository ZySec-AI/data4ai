"""DSPy integration for dynamic prompt generation."""

import json
import logging
import os
from typing import Any, Optional

import dspy

logger = logging.getLogger(__name__)


class DatasetGenerationSignature(dspy.Signature):
    """DSPy signature for dataset generation."""

    description = dspy.InputField(
        desc="Natural language description of the dataset to generate"
    )
    schema_name = dspy.InputField(
        desc="Dataset schema name (alpaca, dolly, sharegpt, etc.)"
    )
    count = dspy.InputField(desc="Number of examples to generate")
    examples = dspy.OutputField(
        desc="List of high-quality dataset examples in JSON format"
    )


class PromptOptimizer:
    """DSPy-based prompt optimizer for dataset generation."""

    def __init__(self, model_name: str = "openai/gpt-4o-mini"):
        """Initialize DSPy with the specified model."""
        self.model_name = model_name
        self._setup_dspy()
        self._setup_signatures()

    def _setup_dspy(self):
        """Setup DSPy with OpenRouter configuration."""
        try:
            # Import and use the new OpenRouter DSPy client
            from data4ai.integrations.openrouter_dspy import (
                configure_dspy_with_openrouter,
            )

            configure_dspy_with_openrouter(
                model=self.model_name,
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
        except ImportError:
            # Fallback to original method if new client is not available
            logger.warning("OpenRouter DSPy client not available, using fallback")
            dspy.configure(
                lm=dspy.LM(
                    model=f"openrouter/{self.model_name}",
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                    base_url="https://openrouter.ai/api/v1",
                )
            )

    def _setup_signatures(self):
        """Setup DSPy signatures for different schemas."""
        self.signatures = {
            "alpaca": DatasetGenerationSignature,
            "dolly": DatasetGenerationSignature,
            "sharegpt": DatasetGenerationSignature,
            "custom": DatasetGenerationSignature,
        }

    def generate_dynamic_prompt(
        self,
        description: str,
        schema_name: str,
        count: int,
        examples: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        """Generate a dynamic prompt using DSPy signature."""
        try:
            # For now, use fallback prompt as DSPy integration needs more work
            logger.info(
                "Using fallback static prompt (DSPy integration in development)"
            )
            return self._fallback_prompt(description, schema_name, count)

        except Exception as e:
            logger.error(f"DSPy prompt generation failed: {e}")
            return self._fallback_prompt(description, schema_name, count)

    def _fallback_prompt(self, description: str, schema_name: str, count: int) -> str:
        """Fallback to static prompt if DSPy fails."""
        base_prompt = f"""Generate {count} high-quality examples for a {schema_name} dataset based on this description: {description}

Please provide the examples in valid JSON format as a list of objects.

For {schema_name} schema, each example should have:"""

        if schema_name == "alpaca":
            base_prompt += """
- instruction: The task or question
- input: Additional context (can be empty)
- output: The expected response or answer"""
        elif schema_name == "dolly":
            base_prompt += """
- instruction: The task or question
- context: Additional context
- response: The expected response"""
        elif schema_name == "sharegpt":
            base_prompt += """
- conversations: List of messages with role and content"""
        else:
            base_prompt += """
- Follow the custom schema format"""

        base_prompt += f"""

Generate exactly {count} diverse, high-quality examples. Ensure the JSON is valid and properly formatted."""

        return base_prompt

    def optimize_prompt_with_examples(
        self,
        description: str,
        schema_name: str,
        count: int,
        example_data: list[dict[str, Any]],
    ) -> str:
        """Optimize prompt using existing examples as few-shot learning."""
        try:
            # Create a few-shot signature
            class FewShotSignature(dspy.Signature):
                description = dspy.InputField(desc="Dataset description")
                examples = dspy.InputField(desc="Example data to learn from")
                new_examples = dspy.OutputField(
                    desc="New examples following the same pattern"
                )

            predictor = dspy.Predict(FewShotSignature)

            result = predictor(
                description=description,
                examples=json.dumps(example_data[:3]),  # Use first 3 examples
            )

            return result.new_examples

        except Exception as e:
            logger.error(f"Few-shot optimization failed: {e}")
            return self.generate_dynamic_prompt(description, schema_name, count)


class SchemaAwarePromptGenerator:
    """Schema-aware prompt generator using DSPy."""

    def __init__(self, model_name: str = "openai/gpt-4o-mini"):
        """Initialize with schema-specific prompt generators."""
        self.optimizer = PromptOptimizer(model_name)
        self.schema_prompts = self._create_schema_prompts()

    def _create_schema_prompts(self) -> dict[str, str]:
        """Create schema-specific prompt templates."""
        return {
            "alpaca": """You are an expert at creating high-quality instruction-following datasets.
Generate {count} diverse examples for the Alpaca format based on: {description}

Each example should have:
- instruction: Clear, specific task or question
- input: Additional context (empty string if not needed)
- output: Comprehensive, accurate response

Focus on:
- Diversity in topics and difficulty levels
- Clear, unambiguous instructions
- Realistic, helpful outputs
- Proper JSON formatting""",
            "dolly": """You are an expert at creating high-quality question-answer datasets.
Generate {count} diverse examples for the Dolly format based on: {description}

Each example should have:
- instruction: Clear question or task
- context: Relevant background information
- response: Detailed, accurate answer

Focus on:
- Educational value
- Clear context provision
- Comprehensive responses
- Proper JSON formatting""",
            "sharegpt": """You are an expert at creating conversational datasets.
Generate {count} diverse conversation examples based on: {description}

Each example should have:
- conversations: List of messages with role ("human" or "gpt") and content

Focus on:
- Natural conversation flow
- Realistic human questions
- Helpful AI responses
- Proper JSON formatting""",
        }

    def generate_schema_prompt(
        self,
        description: str,
        schema_name: str,
        count: int,
        use_dspy: bool = True,
    ) -> str:
        """Generate a schema-aware prompt."""
        if use_dspy:
            return self.optimizer.generate_dynamic_prompt(
                description, schema_name, count
            )
        else:
            # Fallback to template-based prompts
            template = self.schema_prompts.get(
                schema_name, self.schema_prompts["alpaca"]
            )
            return template.format(description=description, count=count)

    def generate_adaptive_prompt(
        self,
        description: str,
        schema_name: str,
        count: int,
        previous_examples: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        """Generate an adaptive prompt that learns from previous examples."""
        if previous_examples and len(previous_examples) > 0:
            return self.optimizer.optimize_prompt_with_examples(
                description, schema_name, count, previous_examples
            )
        else:
            return self.generate_schema_prompt(description, schema_name, count)


# Factory function for easy integration
def create_prompt_generator(
    model_name: str = "openai/gpt-4o-mini",
    use_dspy: bool = True,
) -> SchemaAwarePromptGenerator:
    """Create a prompt generator with the specified configuration."""
    if use_dspy:
        return SchemaAwarePromptGenerator(model_name)
    else:
        # Return a simplified version without DSPy
        class SimplePromptGenerator:
            def __init__(self, model_name: str):
                self.model_name = model_name
                self.schema_prompts = SchemaAwarePromptGenerator(
                    model_name
                ).schema_prompts

            def generate_schema_prompt(
                self, description: str, schema_name: str, count: int, **kwargs
            ) -> str:
                template = self.schema_prompts.get(
                    schema_name, self.schema_prompts["alpaca"]
                )
                return template.format(description=description, count=count)

        return SimplePromptGenerator(model_name)
