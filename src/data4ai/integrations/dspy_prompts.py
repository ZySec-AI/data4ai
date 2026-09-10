"""DSPy integration for dynamic prompt generation."""

import json
import logging
import os
from typing import Any, Optional

import dspy

logger = logging.getLogger(__name__)


class DynamicPromptSignature(dspy.Signature):
    """DSPy signature for dynamic prompt generation based on schema."""

    description = dspy.InputField(
        desc="Natural language description of the dataset to generate"
    )
    schema_name = dspy.InputField(desc="Dataset schema name (chatml, alpaca)")
    count = dspy.InputField(desc="Number of examples to generate")
    schema_requirements = dspy.InputField(
        desc="Specific requirements and format for the schema"
    )
    prompt = dspy.OutputField(
        desc="A comprehensive, schema-specific prompt that will generate high-quality examples in the correct format"
    )


class SchemaAwareGenerationSignature(dspy.Signature):
    """DSPy signature for schema-aware dataset generation."""

    description = dspy.InputField(
        desc="Natural language description of the dataset to generate"
    )
    schema_name = dspy.InputField(desc="Dataset schema name (chatml, alpaca)")
    count = dspy.InputField(desc="Number of examples to generate")
    examples = dspy.OutputField(
        desc="List of high-quality dataset examples in the specified schema format. Must follow the schema requirements exactly."
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
            "dynamic_prompt": DynamicPromptSignature,
            "schema_aware_generation": SchemaAwareGenerationSignature,
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
            # Get schema requirements dynamically
            schema_requirements = self._get_schema_requirements(schema_name)

            # Use DSPy to generate the prompt dynamically
            predictor = dspy.Predict(DynamicPromptSignature)

            result = predictor(
                description=description,
                schema_name=schema_name,
                count=count,
                schema_requirements=schema_requirements,
            )

            # Extract the generated prompt
            prompt = result.prompt

            # If we have previous examples, enhance the prompt with few-shot learning
            if examples and len(examples) > 0:
                prompt += "\n\nHere are some examples to follow:\n"
                prompt += json.dumps(examples[:2], indent=2)
                prompt += "\n\nGenerate similar examples following the same format."

            logger.info(f"Generated dynamic prompt using DSPy for {schema_name}")
            return prompt

        except Exception as e:
            logger.error(f"DSPy prompt generation failed: {e}")
            return self._fallback_prompt(description, schema_name, count)

    def _get_schema_requirements(self, schema_name: str) -> str:
        """Get schema-specific requirements for DSPy."""
        requirements = {
            "chatml": """
CHATML SCHEMA REQUIREMENTS:
- Each example MUST have a "messages" array with at least 2 messages
- NEVER create empty messages arrays: []
- Every conversation must have user input and assistant response
- Use roles: "user", "assistant", "system" (optional)
- Example format: {"messages": [{"role": "user", "content": "question"}, {"role": "assistant", "content": "answer"}]}
- Critical: The messages array cannot be empty and must contain meaningful conversation""",
            "alpaca": """
ALPACA SCHEMA REQUIREMENTS:
- Each example MUST have "instruction" and "output" fields with meaningful content
- "input" field can be empty string when not needed
- Example format: {"instruction": "task", "input": "context", "output": "response"}
- Critical: instruction and output must contain substantial, useful content""",
        }

        return requirements.get(
            schema_name,
            f"Follow the {schema_name} schema format with meaningful content.",
        )

    def _fallback_prompt(self, description: str, schema_name: str, count: int) -> str:
        """Fallback to static prompt if DSPy fails."""
        base_prompt = f"""Generate {count} high-quality examples for a {schema_name} dataset based on this description: {description}

Please provide the examples in valid JSON format as a list of objects.

For {schema_name} schema, each example should have:"""

        if schema_name == "chatml":
            base_prompt += """
- messages: List of conversation messages with role and content

CRITICAL: Each "messages" array MUST contain at least 2 messages (user + assistant). NEVER return empty messages arrays.

Example format:
[
  {
    "messages": [
      {"role": "user", "content": "What is 2+2?"},
      {"role": "assistant", "content": "2+2 equals 4."}
    ]
  }
]"""
        elif schema_name == "alpaca":
            base_prompt += """
- instruction: The task or question
- input: Additional context (can be empty)
- output: The expected response or answer"""

        else:
            base_prompt += """
- Follow the custom schema format"""

        base_prompt += f"""

Generate exactly {count} diverse, high-quality examples. Ensure the JSON is valid and properly formatted. All examples must be fully self-contained and understandable without external references; never write phrases like "according to the document/video" or "see above"."""

        return base_prompt

    def _convert_dspy_result_to_prompt(
        self, dspy_result: Any, schema_name: str, count: int
    ) -> str:
        """Convert DSPy result to a proper prompt format."""
        try:
            # If DSPy returned a string, use it directly
            if isinstance(dspy_result, str):
                return dspy_result

            # If DSPy returned examples, create a prompt that includes them
            if hasattr(dspy_result, "__iter__"):
                examples = list(dspy_result)
                if examples:
                    # Create a few-shot prompt with the examples
                    base_prompt = f"""Generate {count} high-quality examples for a {schema_name} dataset.

Here are some example formats to follow:"""

                    # Add schema-specific formatting
                    if schema_name == "chatml":
                        base_prompt += """

CRITICAL REQUIREMENTS:
- Each "messages" array MUST contain at least 2 messages (user + assistant)
- NEVER return empty messages arrays: []
- Every conversation must have user input and assistant response

Example format:
[
  {
    "messages": [
      {"role": "user", "content": "What is 2+2?"},
      {"role": "assistant", "content": "2+2 equals 4."}
    ]
  }
]"""
                    elif schema_name == "alpaca":
                        base_prompt += """

Example format:
[
  {
    "instruction": "What is 2+2?",
    "input": "Basic arithmetic question",
    "output": "2+2 equals 4."
  }
]"""

                    base_prompt += f"""

Generate exactly {count} diverse, high-quality examples following the format above."""
                    return base_prompt

            # Fallback to static prompt
            return self._fallback_prompt("", schema_name, count)

        except Exception as e:
            logger.error(f"Failed to convert DSPy result to prompt: {e}")
            return self._fallback_prompt("", schema_name, count)

    def _create_enhanced_prompt(
        self, description: str, schema_name: str, count: int
    ) -> str:
        """Create an enhanced prompt with schema-specific instructions."""
        base_prompt = f"""You are an expert dataset generator specializing in {schema_name.upper()} format.

TASK: Generate {count} high-quality examples for a {schema_name} dataset based on this description: {description}

CRITICAL REQUIREMENTS:
1. You MUST respond with ONLY a valid JSON array
2. Do NOT include any explanatory text, code examples, or other content
3. Do NOT use markdown formatting
4. The response must be parseable JSON
5. Each example must be realistic and useful for training
6. Generate exactly {count} examples
7. Each example must be fully self-contained and meaningful without referencing external material (no "as shown", "in the document", or similar)"""

        # Add schema-specific instructions
        if schema_name == "chatml":
            base_prompt += """

CHATML SPECIFIC REQUIREMENTS:
- Each example MUST have a "messages" array with at least 2 messages
- NEVER create empty messages arrays: []
- Every conversation must have user input and assistant response
- Use roles: "user", "assistant", "system" (optional)
- Example format: {"messages": [{"role": "user", "content": "question"}, {"role": "assistant", "content": "answer"}]}"""
        elif schema_name == "alpaca":
            base_prompt += """

ALPACA DATASET SPECIFIC REQUIREMENTS:
- Each example MUST have "instruction" and "output" fields with meaningful content
- "input" field can be empty string when not needed
- Example format: {"instruction": "task", "input": "context", "output": "response"}"""

        base_prompt += f"""

RESPONSE FORMAT: Return ONLY a JSON array with exactly {count} examples. No other text.

Example response format:
[
  {{
    // Your examples here
  }}
]"""

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

    def generate_examples_with_dspy(
        self,
        description: str,
        schema_name: str,
        count: int,
        examples: Optional[list[dict[str, Any]]] = None,
    ) -> list[dict[str, Any]]:
        """Generate examples directly using DSPy."""
        try:
            # Use DSPy to generate examples directly
            predictor = dspy.Predict(SchemaAwareGenerationSignature)

            result = predictor(
                description=description, schema_name=schema_name, count=count
            )

            # Extract and parse the examples
            if hasattr(result, "examples"):
                if isinstance(result.examples, str):
                    # Parse JSON string
                    import json

                    return json.loads(result.examples)
                elif isinstance(result.examples, list):
                    return result.examples
                else:
                    logger.warning(
                        f"Unexpected examples format: {type(result.examples)}"
                    )
                    return []
            else:
                logger.warning("No examples found in DSPy result")
                return []

        except Exception as e:
            logger.error(f"DSPy example generation failed: {e}")
            return []


class SchemaAwarePromptGenerator:
    """Schema-aware prompt generator using DSPy."""

    def __init__(self, model_name: str = "openai/gpt-4o-mini"):
        """Initialize with schema-specific prompt generators."""
        self.optimizer = PromptOptimizer(model_name)
        self.schema_prompts = self._create_schema_prompts()

    def _create_schema_prompts(self) -> dict[str, str]:
        """Create schema-specific prompt templates."""
        return {
            "chatml": """You are an expert at creating high-quality ChatML conversation datasets.
Generate {count} diverse conversation examples for the ChatML format based on: {description}

Each example should have:
- messages: List of conversation messages with role and content

CRITICAL REQUIREMENTS:
- Each "messages" array MUST contain at least 2 messages (user + assistant)
- NEVER return empty messages arrays: []
- Every conversation must have user input and assistant response
- Use roles: "user", "assistant", "system" (optional)

Example format:
[
  {{
    "messages": [
      {{"role": "user", "content": "What is 2+2?"}},
      {{"role": "assistant", "content": "2+2 equals 4."}}
    ]
  }},
  {{
    "messages": [
      {{"role": "system", "content": "You are a helpful assistant."}},
      {{"role": "user", "content": "Translate 'hello' to French"}},
      {{"role": "assistant", "content": "Hello in French is 'bonjour'."}}
    ]
  }}
]

Focus on:
- Natural conversation flow
- Realistic user questions
- Helpful assistant responses
- Proper JSON formatting
- NEVER empty messages arrays""",
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
        }

    def generate_schema_prompt(
        self,
        description: str,
        schema_name: str,
        count: int,
        use_dspy: bool = True,
    ) -> str:
        """Generate a schema-aware prompt using DSPy."""
        if use_dspy:
            return self.optimizer.generate_dynamic_prompt(
                description, schema_name, count
            )
        else:
            # Fallback to template-based prompts
            template = self.schema_prompts.get(
                schema_name, self.schema_prompts["chatml"]
            )
            return template.format(description=description, count=count)

    def generate_examples_directly(
        self,
        description: str,
        schema_name: str,
        count: int,
        examples: Optional[list[dict[str, Any]]] = None,
    ) -> list[dict[str, Any]]:
        """Generate examples directly using DSPy without intermediate prompts."""
        return self.optimizer.generate_examples_with_dspy(
            description, schema_name, count, examples
        )

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

    def _create_enhanced_prompt(
        self, description: str, schema_name: str, count: int
    ) -> str:
        """Create an enhanced prompt with schema-specific instructions."""
        return self.optimizer._create_enhanced_prompt(description, schema_name, count)


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
                    schema_name, self.schema_prompts["chatml"]
                )
                return template.format(description=description, count=count)

        return SimplePromptGenerator(model_name)
