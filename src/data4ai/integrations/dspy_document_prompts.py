"""DSPy integration for document-based dataset generation with quality features."""

import json
import logging
import os

import dspy

logger = logging.getLogger(__name__)


class DocumentQASignature(dspy.Signature):
    """DSPy signature for document-based Q&A generation with taxonomy."""

    document_text = dspy.InputField(
        desc="Source document text to generate questions from"
    )
    schema_name = dspy.InputField(
        desc="Dataset schema (chatml, alpaca, dolly, sharegpt)"
    )
    count = dspy.InputField(desc="Number of Q&A pairs to generate")
    taxonomy_level = dspy.InputField(
        desc="Bloom's taxonomy level to target (optional)", default=""
    )
    include_provenance = dspy.InputField(
        desc="Whether to include source references", default=False
    )
    examples = dspy.OutputField(desc="List of high-quality Q&A examples in JSON format")


class TaxonomyQAGenerator(dspy.Module):
    """DSPy module for generating taxonomy-aware Q&A from documents."""

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(DocumentQASignature)

    def forward(
        self,
        document_text: str,
        schema_name: str,
        count: int,
        taxonomy_level: str = "",
        include_provenance: bool = False,
    ):
        """Generate Q&A pairs using Chain of Thought reasoning."""
        return self.generate(
            document_text=document_text,
            schema_name=schema_name,
            count=count,
            taxonomy_level=taxonomy_level,
            include_provenance=include_provenance,
        )


class DocumentPromptOptimizer:
    """DSPy-based prompt optimizer for document dataset generation with plan→generate pipeline."""

    def __init__(self, model_name: str = "openai/gpt-4o-mini"):
        """Initialize DSPy with the specified model."""
        self.model_name = model_name
        self.qa_generator = None
        self._setup_dspy()

    def _setup_dspy(self):
        """Setup DSPy with OpenRouter configuration."""
        try:
            # Import and use the OpenRouter DSPy client
            from data4ai.integrations.openrouter_dspy import (
                configure_dspy_with_openrouter,
            )

            configure_dspy_with_openrouter(
                model=self.model_name,
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )

            # Initialize the QA generator
            self.qa_generator = TaxonomyQAGenerator()
            logger.info("DSPy document optimizer initialized with OpenRouter")

        except Exception as e:
            logger.warning(f"DSPy setup failed: {e}, will use fallback prompts")

    def generate_taxonomy_prompt(
        self,
        document_text: str,
        schema_name: str,
        count: int,
        taxonomy: str = "balanced",
        include_provenance: bool = False,
    ) -> str:
        """Generate a taxonomy-aware prompt using DSPy."""

        # Map taxonomy option to specific instructions
        taxonomy_instructions = {
            "balanced": """Create questions at ALL levels of Bloom's Revised Taxonomy:
1. Remember (20%): Basic recall - "What is...?", "Define...", "List..."
2. Understand (20%): Comprehension - "Explain...", "Summarize...", "Interpret..."
3. Apply (15%): Use knowledge - "How would you...?", "Demonstrate...", "Solve..."
4. Analyze (15%): Break down - "Compare...", "What caused...?", "Classify..."
5. Evaluate (15%): Judge - "Critique...", "Justify...", "Which is better...?"
6. Create (15%): Synthesize - "Design...", "Propose...", "What if...?"

Ensure a balanced distribution across all cognitive levels.""",
            "basic": """Focus on lower-order thinking (Remember & Understand):
- Remember (50%): Factual recall, definitions, lists
- Understand (50%): Explanations, summaries, interpretations
Create foundational questions suitable for beginners.""",
            "advanced": """Focus on higher-order thinking (Analyze, Evaluate & Create):
- Analyze (35%): Compare, contrast, cause-effect, relationships
- Evaluate (35%): Critique, justify, judge, assess
- Create (30%): Design, propose, synthesize, innovate
Create challenging questions requiring critical thinking.""",
            "none": """Create diverse questions without specific taxonomy requirements.
Focus on variety in question types, difficulty levels, and cognitive demands.
Ensure questions are pedagogically valuable and cover the document comprehensively.""",
        }

        # Always use DSPy for taxonomy-aware generation
        logger.info(
            f"Using DSPy for taxonomy-aware generation ({taxonomy or 'balanced'})"
        )

        # Use the specified taxonomy or default to balanced
        taxonomy = taxonomy or "balanced"

        # Create a detailed context prompt with DSPy Chain of Thought
        context_prompt = f"""You are an expert educational content creator specializing in Bloom's Revised Taxonomy.

DOCUMENT CONTEXT:
{document_text[:2000]}{"..." if len(document_text) > 2000 else ""}

TAXONOMY REQUIREMENTS:
{taxonomy_instructions[taxonomy]}

SCHEMA: {schema_name}
Generate {count} high-quality Q&A pairs that:
1. Are directly answerable from the document
2. Follow the specified taxonomy distribution
3. Include diverse question types
4. Avoid repetition or similar questions
{"5. Include source_start and source_end character offsets for evidence" if include_provenance else ""}
5. Are fully self-contained and meaningful without referencing the source; never use phrases like "according to the document/video", "as shown", or "see above". Include any essential context in the question or input.

For {schema_name} format, structure each example as:"""

        # Add schema-specific formatting
        if schema_name == "chatml":
            context_prompt += """
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "[Question based on document]"},
    {"role": "assistant", "content": "[Answer from document]"}
  ]
}

CRITICAL: The 'messages' array MUST contain at least 2 messages (user + assistant). NEVER return empty messages arrays."""
            if include_provenance:
                context_prompt += (
                    ',\n  "source_start": [start_offset],\n  "source_end": [end_offset]'
                )
            context_prompt += "\n}"

        elif schema_name == "alpaca":
            context_prompt += """
{
  "instruction": "[Question at specified taxonomy level]",
  "input": "[Optional context from document]",
  "output": "[Answer based on document]"""
            if include_provenance:
                context_prompt += (
                    ',\n  "source_start": [start_offset],\n  "source_end": [end_offset]'
                )
            context_prompt += "\n}"

        context_prompt += f"""

Think step-by-step:
1. Identify key concepts in the document
2. Map concepts to appropriate taxonomy levels
3. Generate diverse questions at each level
4. Ensure answers are grounded in the document
5. Return ONLY a JSON array of {count} examples"""

        return context_prompt

    def generate_summary_prompt(
        self, document_text: str, schema_name: str, count: int
    ) -> str:
        """Generate a DSPy-powered prompt for summary generation."""

        logger.info("Generating DSPy summary prompt")

        prompt = f"""You are an expert at creating summarization training examples.

DOCUMENT CONTEXT:
{document_text[:2000]}{"..." if len(document_text) > 2000 else ""}

TASK: Generate {count} diverse summarization examples for {schema_name} format.

REQUIREMENTS:
1. Create summaries at different levels:
   - Brief (1-2 sentences)
   - Standard (paragraph)
   - Detailed (multiple paragraphs)
   - Executive (key points only)

2. Focus on different aspects:
   - Main arguments
   - Technical details
   - Conclusions and implications
   - Key facts and figures

3. Vary the summarization style:
   - Extractive (using original phrases)
   - Abstractive (rephrasing in new words)
   - Structured (with sections/bullets)

4. All outputs must be fully self-contained and understandable without the source. Do not reference the document/video. Do not use phrases like "as described above" or "in the document".

Think step-by-step:
1. Identify the main themes and key points
2. Determine what type of summary would be most valuable
3. Create diverse examples that teach different summarization skills
4. Ensure each summary accurately represents the source

Return ONLY a JSON array of {count} examples in {schema_name} format."""

        return prompt

    def generate_instruction_prompt(
        self, document_text: str, schema_name: str, count: int
    ) -> str:
        """Generate a DSPy-powered prompt for instruction generation."""

        logger.info("Generating DSPy instruction prompt")

        prompt = f"""You are an expert at creating instructional training examples from documents.

DOCUMENT CONTEXT:
{document_text[:2000]}{"..." if len(document_text) > 2000 else ""}

TASK: Generate {count} diverse instruction-following examples for {schema_name} format.

REQUIREMENTS:
1. Create varied instruction types:
   - Explain (concepts, processes, relationships)
   - Define (terms, concepts, ideas)
   - Compare (similarities and differences)
   - Apply (use knowledge in scenarios)
   - Analyze (break down complex ideas)
   - Create (synthesize new content)

2. Ensure pedagogical value:
   - Each instruction should teach something meaningful
   - Answers should be comprehensive and accurate
   - Instructions should be clear and unambiguous

3. Cover different complexity levels:
   - Simple (single-step, direct)
   - Moderate (multi-step, some reasoning)
   - Complex (deep analysis, synthesis)

4. Each example must be fully self-contained: do not reference the document/video or external context; include necessary context within the example.

Think step-by-step:
1. Identify key concepts and relationships in the document
2. Map concepts to appropriate instruction types
3. Create instructions that progressively build understanding
4. Ensure all outputs are grounded in the document

Return ONLY a JSON array of {count} examples in {schema_name} format."""

        return prompt

    def generate_general_prompt(
        self, document_text: str, schema_name: str, count: int
    ) -> str:
        """Generate a DSPy-powered general prompt for document generation."""

        logger.info("Generating DSPy general document prompt")

        prompt = f"""You are an expert at creating training datasets from documents.

DOCUMENT CONTEXT:
{document_text[:2000]}{"..." if len(document_text) > 2000 else ""}

TASK: Generate {count} high-quality training examples for {schema_name} format.

REQUIREMENTS:
1. Create diverse example types:
   - Questions and answers
   - Instructions and responses
   - Explanations and elaborations
   - Analyses and insights

2. Ensure variety in:
   - Topic coverage (all major themes)
   - Difficulty levels (easy to challenging)
   - Response lengths (brief to detailed)
   - Cognitive demands (recall to synthesis)

3. Maintain quality:
   - All outputs must be grounded in the document
   - No hallucinations or unsupported claims
   - Clear, accurate, and pedagogically valuable
   - Fully self-contained: avoid references to the source; include essential context directly in each example

Think step-by-step:
1. Survey the document's main topics and themes
2. Identify valuable learning opportunities
3. Create diverse examples that maximize learning potential
4. Ensure all content is factually accurate

Return ONLY a JSON array of {count} examples in {schema_name} format."""

        return prompt

    def plan(
        self, document_text: str, schema_name: str, objectives: dict, budget: dict
    ) -> dict:
        """Create a generation plan for the document with dynamic allocation.

        Args:
            document_text: Full document text
            schema_name: Target schema (chatml, alpaca, etc.)
            objectives: Dict with taxonomy, difficulty preferences
            budget: Dict with token_budget, min_examples, max_examples

        Returns:
            Generation plan with section allocations
        """
        logger.info("Creating DSPy generation plan for document")

        # Extract objectives
        taxonomy = objectives.get("taxonomy", "balanced")
        difficulty = objectives.get("difficulty", "balanced")

        # Extract budget constraints
        token_budget = budget.get("token_budget", 10000)
        min_examples = budget.get("min_examples", 10)
        max_examples = budget.get("max_examples", 100)

        # Create planning prompt
        plan_prompt = f"""You are an expert at planning dataset generation from documents.

DOCUMENT CONTEXT:
{document_text[:3000]}{"..." if len(document_text) > 3000 else ""}

TASK: Create a generation plan for {schema_name} dataset.

OBJECTIVES:
- Taxonomy: {taxonomy} (Bloom's Revised Taxonomy distribution)
- Difficulty: {difficulty} (easy/medium/hard balance)
- Token Budget: {token_budget} tokens total
- Example Range: {min_examples} to {max_examples} examples

REQUIREMENTS:
1. Analyze the document and identify key sections
2. Allocate examples to sections based on importance
3. Plan taxonomy distribution across sections
4. Stay within token budget
5. Return ONLY valid JSON

Create a plan with this structure:
{{
  "sections": [
    {{
      "title": "Section name",
      "span": "Character range or description",
      "key_concepts": ["concept1", "concept2"],
      "allocated_examples": 5,
      "taxonomy_focus": ["Remember", "Understand"],
      "difficulty_mix": {{"easy": 2, "medium": 2, "hard": 1}}
    }}
  ],
  "total_examples": 20,
  "estimated_tokens": 8000,
  "taxonomy_distribution": {{
    "Remember": 4,
    "Understand": 4,
    "Apply": 3,
    "Analyze": 3,
    "Evaluate": 3,
    "Create": 3
  }},
  "rationale": "Brief explanation of allocation strategy"
}}

Return ONLY the JSON plan, no other text."""

        return {
            "prompt": plan_prompt,
            "type": "plan",
            "sections": [],
            "total_examples": min(max(20, min_examples), max_examples),
            "estimated_tokens": token_budget * 0.8,  # Conservative estimate
            "objectives": objectives,
            "budget": budget,
        }

    def generate(self, document_text: str, schema_name: str, plan: dict) -> str:
        """Generate examples following the plan without specifying fixed counts.

        Args:
            document_text: Full document text
            schema_name: Target schema
            plan: Generation plan from plan() method

        Returns:
            Generation prompt (no fixed counts)
        """
        logger.info("Creating DSPy generation prompt from plan")

        # Extract plan details
        sections = plan.get("sections", [])
        total_examples = plan.get("total_examples", 20)
        taxonomy_dist = plan.get("taxonomy_distribution", {})

        # Build section allocation text
        section_text = (
            "\n".join(
                [
                    f"- {s['title']}: {s['allocated_examples']} examples focusing on {', '.join(s.get('taxonomy_focus', []))}"
                    for s in sections
                ]
            )
            if sections
            else f"- Generate approximately {total_examples} examples total"
        )

        # Create generation prompt WITHOUT fixed count
        generate_prompt = f"""You are an expert at creating training datasets from documents.

DOCUMENT CONTEXT:
{document_text[:3000]}{"..." if len(document_text) > 3000 else ""}

GENERATION PLAN:
{section_text}

TAXONOMY DISTRIBUTION TARGET:
{json.dumps(taxonomy_dist, indent=2) if taxonomy_dist else "Balanced across all levels"}

TASK: Generate training examples for {schema_name} format following the plan.

REQUIREMENTS:
1. Follow the allocation plan for sections
2. Maintain taxonomy distribution
3. Ensure all examples are grounded in the document
4. Create diverse, non-repetitive examples
5. Return ONLY a valid JSON array

DO NOT specify a predetermined number in your response.
Follow the plan's allocations naturally.
Quality over quantity - generate as many high-quality examples as the plan suggests.

Return ONLY a JSON array of examples in {schema_name} format."""

        return generate_prompt


def create_document_prompt_optimizer(
    model_name: str = "openai/gpt-4o-mini", use_dspy: bool = True
) -> DocumentPromptOptimizer:
    """Factory function to create a document prompt optimizer."""
    if not use_dspy:
        raise ValueError("DSPy is required for document generation. Set USE_DSPY=true")

    import os

    if not os.getenv("OPENROUTER_API_KEY"):
        raise ValueError(
            "OPENROUTER_API_KEY is required for DSPy document generation. "
            "Set it with: export OPENROUTER_API_KEY='your-key-here'"
        )

    try:
        optimizer = DocumentPromptOptimizer(model_name)
        logger.info(f"DSPy document optimizer created with model: {model_name}")
        return optimizer
    except Exception as e:
        raise ValueError(f"Failed to create DSPy optimizer: {e}") from e
