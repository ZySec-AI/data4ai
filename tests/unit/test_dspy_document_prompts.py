"""Tests for document-specific DSPy prompt construction."""

from unittest.mock import patch

import pytest

from data4ai.integrations.dspy_document_prompts import (
    DocumentPromptOptimizer,
    TaxonomyQAGenerator,
    create_document_prompt_optimizer,
)


def make_optimizer() -> DocumentPromptOptimizer:
    with patch.object(DocumentPromptOptimizer, "_setup_dspy"):
        return DocumentPromptOptimizer("test/model")


def test_taxonomy_generator_forwards_arguments():
    with patch("dspy.ChainOfThought") as chain:
        prediction = object()
        chain.return_value.return_value = prediction
        generator = TaxonomyQAGenerator()
        result = generator.forward("text", "alpaca", 2, "apply", True)
    assert result is prediction
    chain.return_value.assert_called_once_with(
        document_text="text",
        schema_name="alpaca",
        count=2,
        taxonomy_level="apply",
        include_provenance=True,
    )


def test_setup_dspy_success_and_failure():
    optimizer = object.__new__(DocumentPromptOptimizer)
    optimizer.model_name = "test/model"
    optimizer.qa_generator = None
    with (
        patch(
            "data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter"
        ) as configure,
        patch(
            "data4ai.integrations.dspy_document_prompts.TaxonomyQAGenerator",
            return_value="generator",
        ),
    ):
        optimizer._setup_dspy()
    assert optimizer.qa_generator == "generator"
    configure.assert_called_once()

    optimizer.qa_generator = None
    with patch(
        "data4ai.integrations.openrouter_dspy.configure_dspy_with_openrouter",
        side_effect=RuntimeError("failed"),
    ):
        optimizer._setup_dspy()
    assert optimizer.qa_generator is None


@pytest.mark.parametrize("taxonomy", ["balanced", "basic", "advanced", "none", None])
@pytest.mark.parametrize("schema", ["alpaca", "chatml"])
def test_taxonomy_prompt_variants(taxonomy, schema):
    optimizer = make_optimizer()
    prompt = optimizer.generate_taxonomy_prompt(
        "x" * 2100, schema, 3, taxonomy=taxonomy, include_provenance=True
    )
    assert "Generate 3" in prompt
    assert schema in prompt
    assert "source_start" in prompt
    assert "..." in prompt


def test_summary_instruction_and_general_prompts():
    optimizer = make_optimizer()
    assert "summarization" in optimizer.generate_summary_prompt("text", "alpaca", 2)
    assert "instructional" in optimizer.generate_instruction_prompt("text", "alpaca", 2)
    assert "training datasets" in optimizer.generate_general_prompt("text", "chatml", 2)


def test_plan_and_generate_with_sections_and_defaults():
    optimizer = make_optimizer()
    plan = optimizer.plan(
        "document",
        "alpaca",
        {"taxonomy": "advanced", "difficulty": "hard"},
        {"token_budget": 1000, "min_examples": 5, "max_examples": 10},
    )
    assert plan["total_examples"] == 10
    assert plan["estimated_tokens"] == 800
    detailed = optimizer.generate(
        "document",
        "alpaca",
        {
            "sections": [
                {"title": "Intro", "allocated_examples": 2, "taxonomy_focus": ["Apply"]}
            ],
            "total_examples": 2,
            "taxonomy_distribution": {"Apply": 2},
        },
    )
    assert "Intro: 2 examples" in detailed
    assert '"Apply": 2' in detailed
    fallback = optimizer.generate("document", "chatml", {"total_examples": 4})
    assert "approximately 4" in fallback
    assert "Balanced across all levels" in fallback


def test_factory_validation_and_success(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DSPy is required"):
        create_document_prompt_optimizer(use_dspy=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        create_document_prompt_optimizer()

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    instance = object()
    with patch(
        "data4ai.integrations.dspy_document_prompts.DocumentPromptOptimizer",
        return_value=instance,
    ):
        assert create_document_prompt_optimizer("model") is instance
    with (
        patch(
            "data4ai.integrations.dspy_document_prompts.DocumentPromptOptimizer",
            side_effect=RuntimeError("failed"),
        ),
        pytest.raises(ValueError, match="Failed to create DSPy optimizer"),
    ):
        create_document_prompt_optimizer("model")
