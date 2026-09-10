"""Focused unit coverage for DatasetGenerator orchestration helpers."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from data4ai.exceptions import GenerationError
from data4ai.generator import DatasetGenerator, create_prompt_generator


def bare_generator() -> DatasetGenerator:
    generator = object.__new__(DatasetGenerator)
    generator.model = "test/model"
    generator.api_key = "test-key"
    generator.temperature = 0.2
    generator.seed = 7
    generator.client = SimpleNamespace(chat_completion=AsyncMock())
    generator.document_prompt_optimizer = None
    generator.prompt_generator = generator._create_static_prompt_generator(
        generator.model
    )
    return generator


def test_prompt_factory_and_static_generator_fallback():
    created = object()
    with patch(
        "data4ai.integrations.dspy_prompts.create_prompt_generator",
        return_value=created,
    ) as factory:
        assert create_prompt_generator("model", False) is created
        factory.assert_called_once_with(model_name="model", use_dspy=False)

    with patch(
        "data4ai.integrations.dspy_prompts.create_prompt_generator",
        side_effect=RuntimeError("unavailable"),
    ):
        fallback = create_prompt_generator("model")
    assert fallback.model_name == "model"
    assert fallback.generate_schema_prompt("topic", "alpaca", 3) == (
        "Generate 3 alpaca examples: topic"
    )


def test_generation_prompt_paths_and_system_messages():
    generator = bare_generator()
    dynamic = Mock()
    dynamic.generate_dynamic_prompt.return_value = "dynamic"
    generator.prompt_generator = dynamic
    assert (
        generator._build_generation_prompt("topic", "alpaca", 2, [{"a": 1}])
        == "dynamic"
    )

    optimized = SimpleNamespace(optimizer=Mock())
    optimized.optimizer.generate_dynamic_prompt.return_value = "optimized"
    generator.prompt_generator = optimized
    assert generator._build_generation_prompt("topic", "chatml", 1) == "optimized"

    generator.use_static_prompt_generator()
    assert "instruction" in generator._build_generation_prompt("topic", "alpaca", 2)
    assert "messages" in generator._build_generation_prompt("topic", "chatml", 2)
    assert "messages" in generator._get_system_prompt("chatml")
    assert generator._get_system_prompt("alpaca").endswith("valid JSON.")


def test_parse_response_valid_invalid_limit_and_chatml_repair():
    generator = bare_generator()
    schema = Mock()
    valid = Mock()
    valid.validate_content.return_value = True
    valid.to_jsonl_entry.return_value = {"instruction": "i", "output": "o"}
    invalid = Mock()
    invalid.validate_content.return_value = False
    schema.from_dict.side_effect = [valid, invalid, valid]

    with patch("data4ai.generator.SchemaRegistry.get", return_value=schema):
        result = generator._parse_response(
            '[{"a": 1}, {"a": 2}, {"a": 3}]', "alpaca", 1
        )
    assert result == [{"instruction": "i", "output": "o"}]
    assert generator._parse_response("not json", "alpaca") == []

    repaired = generator._fix_empty_chatml_entry(
        {"messages": [], "source": "doc"}, "chatml"
    )
    assert len(repaired["messages"]) == 2
    assert repaired["source"] == "doc"
    assert generator._fix_empty_chatml_entry({"messages": []}, "alpaca") is None
    assert (
        generator._fix_empty_chatml_entry({"messages": [{"role": "user"}]}, "chatml")
        is None
    )


def test_parse_response_repairs_after_schema_validation_error():
    generator = bare_generator()
    schema = Mock()
    instance = Mock()
    instance.validate_content.return_value = True
    instance.to_jsonl_entry.return_value = {"messages": [{"role": "user"}]}
    schema.from_dict.side_effect = [ValueError("empty"), instance]
    repaired = {"messages": [{"role": "user", "content": "fallback"}]}
    with (
        patch("data4ai.generator.SchemaRegistry.get", return_value=schema),
        patch.object(
            generator, "_fix_empty_chatml_entry", side_effect=[None, repaired]
        ),
    ):
        result = generator._parse_response('[{"messages": []}]', "chatml")
    assert result == [{"messages": [{"role": "user"}]}]


@pytest.mark.asyncio
async def test_process_batch_success_parse_failure_and_api_failure():
    generator = bare_generator()
    generator.client.chat_completion.return_value = {
        "choices": [{"message": {"content": "response"}}]
    }
    generator._parse_response = Mock(return_value=[{"instruction": "one"}])
    entries, audit = await generator._process_batch_concurrent(
        1, 2, "prompt", 1, "alpaca", batch_levels=["apply"]
    )
    assert entries[0]["taxonomy_level"] == "apply"
    assert audit["system_message"].startswith("You are")
    assert "OUTPUT REQUIREMENTS" in audit["user_message"]

    generator._parse_response.return_value = []
    entries, audit = await generator._process_batch_concurrent(
        1, 1, "prompt", 1, "alpaca"
    )
    assert entries == []
    assert audit["system_message"] == "Parse Error"

    generator.client.chat_completion.side_effect = RuntimeError("offline")
    entries, audit = await generator._process_batch_concurrent(
        1, 1, "prompt", 1, "alpaca"
    )
    assert entries == []
    assert audit == {"system_message": "Exception", "user_message": "offline"}


@pytest.mark.asyncio
async def test_generate_from_prompt_dry_run_and_success(tmp_path: Path):
    generator = bare_generator()
    assert await generator.generate_from_prompt(
        "topic", tmp_path, "alpaca", count=4, dry_run=True
    ) == {
        "count": 4,
        "dry_run": True,
    }

    generator.prompt_generator = SimpleNamespace(
        generate_dynamic_prompt=Mock(return_value="master prompt")
    )
    generator._process_batch_concurrent = AsyncMock(
        side_effect=[
            ([{"instruction": "a", "output": "b"}], {"user_message": "one"}),
            ([{"instruction": "c", "output": "d"}], {"user_message": "two"}),
        ]
    )
    with (
        patch("data4ai.generator.write_jsonl") as write_jsonl,
        patch("data4ai.generator.calculate_metrics", return_value={"valid": 2}),
        patch("data4ai.generator.save_metadata") as save_metadata,
    ):
        result = await generator.generate_from_prompt(
            "topic", tmp_path, "alpaca", count=3, batch_size=2, taxonomy_all_levels=True
        )
    assert result["row_count"] == 2
    assert result["prompt_generation_method"] == "dspy"
    assert len(result["prompts_used"]) == 2
    write_jsonl.assert_called_once()
    save_metadata.assert_called_once()


@pytest.mark.asyncio
async def test_verify_example_success_invalid_and_error():
    generator = bare_generator()
    generator.client.chat_completion.return_value = {
        "choices": [{"message": {"content": '{"answer": "better"}'}}]
    }
    assert await generator._verify_and_improve_example(
        {"answer": "old"}, "text", "alpaca"
    ) == {"answer": "better"}

    generator.client.chat_completion.return_value = {
        "choices": [{"message": {"content": "[]"}}]
    }
    original = {"answer": "old"}
    assert (
        await generator._verify_and_improve_example(original, "text", "alpaca")
        is original
    )
    generator.client.chat_completion.side_effect = RuntimeError("offline")
    assert (
        await generator._verify_and_improve_example(original, "text", "alpaca")
        is original
    )


def test_document_prompt_helpers_and_configuration():
    generator = bare_generator()
    optimizer = Mock()
    optimizer.generate_taxonomy_prompt.return_value = "qa"
    optimizer.generate_summary_prompt.return_value = "summary"
    optimizer.generate_general_prompt.return_value = "general"
    generator.document_prompt_optimizer = optimizer

    assert generator._build_document_qa_prompt("text", "alpaca", 2) == "qa"
    assert generator._build_document_summary_prompt("text", "alpaca", 2) == "summary"
    assert generator._build_document_general_prompt("text", "alpaca", 2) == "general"
    assert generator._build_document_instruction_prompt("text", "alpaca", 2) is None
    assert generator._get_taxonomy_instruction("apply") == ""

    generator.document_prompt_optimizer = None
    with patch.object(generator, "_ensure_document_prompt_optimizer"):
        with pytest.raises(GenerationError):
            generator._build_document_qa_prompt("text", "alpaca", 1)
        with pytest.raises(GenerationError):
            generator._build_document_summary_prompt("text", "alpaca", 1)
    with pytest.raises(GenerationError):
        generator._build_document_general_prompt("text", "alpaca", 1)


def test_enable_dspy_and_lazy_optimizer_paths():
    generator = bare_generator()
    prompt_generator = object()
    with patch(
        "data4ai.integrations.openrouter_dspy.create_openrouter_prompt_generator",
        return_value=prompt_generator,
    ):
        assert generator.enable_dspy_prompt_generator() is True
        assert generator.prompt_generator is prompt_generator
    with patch(
        "data4ai.integrations.openrouter_dspy.create_openrouter_prompt_generator",
        side_effect=RuntimeError("no dspy"),
    ):
        assert generator.enable_dspy_prompt_generator() is False

    optimizer = object()
    generator.document_prompt_optimizer = None
    with patch(
        "data4ai.integrations.dspy_document_prompts.create_document_prompt_optimizer",
        return_value=optimizer,
    ):
        generator._ensure_document_prompt_optimizer()
    assert generator.document_prompt_optimizer is optimizer

    generator.document_prompt_optimizer = None
    with patch(
        "data4ai.integrations.dspy_document_prompts.create_document_prompt_optimizer",
        side_effect=RuntimeError("no optimizer"),
    ):
        generator._ensure_document_prompt_optimizer()
    assert generator.document_prompt_optimizer is None


@pytest.mark.asyncio
async def test_generate_from_document_dspy_dry_run_and_success(tmp_path: Path):
    generator = bare_generator()
    optimizer = Mock()
    optimizer.plan.return_value = {"prompt": "make a plan"}
    optimizer.generate.return_value = "generate examples"
    generator.document_prompt_optimizer = optimizer
    document = tmp_path / "source.txt"
    document.write_text("source material", encoding="utf-8")

    with patch(
        "data4ai.generator.DocumentHandler.extract_text", return_value="source material"
    ):
        preview = await generator.generate_from_document_dspy(
            document, tmp_path / "preview", dry_run=True
        )
    assert preview["dry_run"] is True
    assert preview["document_length"] == len("source material")

    generator.client.chat_completion.side_effect = [
        {
            "choices": [
                {"message": {"content": '{"total_examples": 2, "sections": []}'}}
            ]
        },
        {"choices": [{"message": {"content": "examples"}}]},
    ]
    generator._parse_response = Mock(return_value=[{"instruction": "i", "output": "o"}])
    with (
        patch(
            "data4ai.generator.DocumentHandler.extract_text",
            return_value="source material",
        ),
        patch("data4ai.generator.write_jsonl") as write_jsonl,
        patch("data4ai.generator.calculate_metrics", return_value={"valid": 1}),
        patch("data4ai.generator.save_metadata") as save_metadata,
    ):
        result = await generator.generate_from_document_dspy(
            document, tmp_path / "output"
        )
    assert result["row_count"] == 1
    assert result["realized_vs_planned"] == "1/2"
    optimizer.plan.assert_called_once()
    optimizer.generate.assert_called_once()
    write_jsonl.assert_called_once()
    save_metadata.assert_called_once()


@pytest.mark.asyncio
async def test_generate_from_document_flat_summary_flow(tmp_path: Path):
    generator = bare_generator()
    optimizer = Mock()
    optimizer.generate_summary_prompt.return_value = "summarize"
    generator.document_prompt_optimizer = optimizer
    generator.client.chat_completion.return_value = {
        "choices": [{"message": {"content": "examples"}}]
    }
    generator._parse_response = Mock(
        side_effect=lambda *_: [{"instruction": "i", "output": "o"}]
    )
    doc_data = {
        "total_chunks": 2,
        "total_documents": 2,
        "document_type": "text",
        "input_type": "folder",
        "document_names": ["one.txt", "two.txt"],
        "chunks": [
            {"id": 0, "text": "first", "start": 0, "end": 5, "source": "one.txt"},
            {"id": 1, "text": "second", "start": 0, "end": 6, "source": "two.txt"},
        ],
    }
    stats = SimpleNamespace(
        method="content",
        duplicates_removed=0,
        unique_items=2,
        total_items=2,
        threshold=0.97,
    )
    with (
        patch(
            "data4ai.generator.DocumentHandler.prepare_for_generation",
            return_value=doc_data,
        ),
        patch("data4ai.generator.Deduplicator") as deduplicator,
        patch("data4ai.generator.write_jsonl") as write_jsonl,
        patch("data4ai.generator.calculate_metrics", return_value={"valid": 2}),
        patch("data4ai.generator.save_metadata") as save_metadata,
    ):
        deduplicator.return_value.deduplicate.return_value = (
            [{"instruction": "i", "output": "o"}] * 2,
            stats,
        )
        result = await generator.generate_from_document(
            tmp_path / "docs",
            tmp_path / "output",
            "alpaca",
            extraction_type="summary",
            count=2,
            chunk_tokens=20,
            include_provenance=True,
            verify_quality=True,
            long_context=True,
        )
    assert result["row_count"] == 2
    assert result["total_documents"] == 2
    assert result["organized_by_folders"] is None
    assert optimizer.generate_summary_prompt.call_count == 1
    write_jsonl.assert_called_once()
    save_metadata.assert_called_once()


@pytest.mark.asyncio
async def test_generate_from_document_flat_qa_baseline_flow(tmp_path: Path):
    generator = bare_generator()
    optimizer = Mock()
    optimizer.generate_taxonomy_prompt.return_value = "ask question"
    generator.document_prompt_optimizer = optimizer
    generator.client.chat_completion.return_value = {
        "choices": [{"message": {"content": "examples"}}]
    }
    generator._parse_response = Mock(
        side_effect=lambda *_: [{"instruction": "i", "output": "o"}]
    )
    doc_data = {
        "total_chunks": 1,
        "total_documents": 1,
        "document_type": "text",
        "input_type": "file",
        "chunks": [
            {
                "id": 0,
                "text": "source",
                "start": 0,
                "end": 6,
                "file_path": "source.txt",
            }
        ],
    }
    with (
        patch(
            "data4ai.generator.DocumentHandler.prepare_for_generation",
            return_value=doc_data,
        ),
        patch("data4ai.generator.Deduplicator") as deduplicator,
        patch("data4ai.generator.write_jsonl"),
        patch("data4ai.generator.calculate_metrics", return_value={}),
        patch("data4ai.generator.save_metadata"),
    ):
        deduplicator.return_value.deduplicate.side_effect = RuntimeError("skip dedup")
        result = await generator.generate_from_document(
            tmp_path / "source.txt",
            tmp_path / "output",
            "chatml",
            extraction_type="qa",
            count=1,
            taxonomy="advanced",
            taxonomy_all_levels=True,
        )
    assert result["row_count"] == 7
    assert "taxonomy_coverage_overall" in result["metrics"]
    assert generator.client.chat_completion.await_count == 8


@pytest.mark.asyncio
async def test_generate_from_document_organized_folder_flow(tmp_path: Path):
    generator = bare_generator()
    optimizer = Mock()
    optimizer.generate_general_prompt.return_value = "generate"
    generator.document_prompt_optimizer = optimizer
    generator.client.chat_completion.return_value = {
        "choices": [{"message": {"content": "examples"}}]
    }
    generator._parse_response = Mock(
        side_effect=lambda *_: [{"instruction": "i", "output": "o"}]
    )
    doc_data = {
        "total_chunks": 2,
        "total_documents": 1,
        "document_type": "text",
        "input_type": "folder",
        "folder_structure": {"has_subfolders": True},
        "chunks": [
            {
                "id": 0,
                "text": "first",
                "start": 0,
                "end": 5,
                "file_path": "team/source.txt",
            },
            {
                "id": 1,
                "text": "second",
                "start": 5,
                "end": 11,
                "file_path": "team/source.txt",
            },
        ],
    }
    stats = SimpleNamespace(
        method="content",
        duplicates_removed=0,
        unique_items=1,
        total_items=1,
        threshold=0.97,
    )
    with (
        patch(
            "data4ai.generator.DocumentHandler.prepare_for_generation",
            return_value=doc_data,
        ),
        patch("data4ai.generator.Deduplicator") as deduplicator,
        patch("data4ai.generator.write_jsonl") as write_jsonl,
        patch("data4ai.generator.calculate_metrics", return_value={"valid": 1}),
        patch("data4ai.generator.save_metadata") as save_metadata,
    ):
        deduplicator.return_value.deduplicate.return_value = (
            [{"instruction": "i", "output": "o"}],
            stats,
        )
        result = await generator.generate_from_document(
            tmp_path / "docs",
            tmp_path / "output",
            "alpaca",
            extraction_type="general",
            count=1,
            long_context=True,
        )
    assert result["organized_by_folders"] is True
    assert result["row_count"] == 1
    assert optimizer.generate_general_prompt.call_count == 2
    assert write_jsonl.call_count == 2
    assert save_metadata.call_count == 2


@pytest.mark.asyncio
async def test_generate_from_document_preflight_failure(tmp_path: Path):
    generator = bare_generator()
    generator.client.chat_completion.side_effect = RuntimeError("offline")
    with pytest.raises(GenerationError, match="preflight"):
        await generator.generate_from_document(
            tmp_path / "source.txt", tmp_path / "output", "alpaca"
        )


def test_document_sync_dry_run_paths(tmp_path: Path):
    generator = bare_generator()
    document = tmp_path / "source.txt"
    document.write_text("text", encoding="utf-8")
    assert generator.generate_from_document_sync(document, dry_run=True) == {
        "document": "source.txt",
        "chunks": 2,
        "total_documents": 1,
        "dry_run": True,
    }

    folder = tmp_path / "docs"
    folder.mkdir()
    with patch(
        "data4ai.document_handler.DocumentHandler.scan_folder", return_value=[document]
    ):
        preview = generator.generate_from_document_sync(folder, dry_run=True)
    assert preview["total_documents"] == 1
    assert preview["chunks"] == 2


@pytest.mark.asyncio
async def test_generate_from_document_folder_qa_quality_flow(tmp_path: Path):
    generator = bare_generator()
    optimizer = Mock()
    optimizer.generate_taxonomy_prompt.return_value = "ask question"
    generator.document_prompt_optimizer = optimizer
    generator.client.chat_completion.return_value = {
        "choices": [{"message": {"content": "examples"}}]
    }
    generator._parse_response = Mock(
        side_effect=lambda *_: [{"instruction": "i", "output": "o"}]
    )
    generator._verify_and_improve_example = AsyncMock(
        side_effect=lambda entry, *_: entry
    )
    doc_data = {
        "total_chunks": 1,
        "total_documents": 1,
        "document_type": "text",
        "input_type": "folder",
        "folder_structure": {"has_subfolders": True},
        "chunks": [
            {
                "id": 0,
                "text": "source",
                "start": 0,
                "end": 6,
                "file_path": "topic/source.txt",
            }
        ],
    }
    stats = SimpleNamespace(
        method="content",
        duplicates_removed=0,
        unique_items=7,
        total_items=7,
        threshold=0.97,
    )
    with (
        patch(
            "data4ai.generator.DocumentHandler.prepare_for_generation",
            return_value=doc_data,
        ),
        patch("data4ai.generator.Deduplicator") as deduplicator,
        patch("data4ai.generator.write_jsonl"),
        patch("data4ai.generator.calculate_metrics", return_value={}),
        patch("data4ai.generator.save_metadata"),
    ):
        deduplicator.return_value.deduplicate.side_effect = lambda rows, **_: (
            rows,
            stats,
        )
        result = await generator.generate_from_document(
            tmp_path / "docs",
            tmp_path / "output",
            "alpaca",
            extraction_type="qa",
            count=1,
            taxonomy_all_levels=True,
            include_provenance=True,
            verify_quality=True,
        )
    assert result["organized_by_folders"] is True
    assert result["row_count"] == 1
    assert generator._verify_and_improve_example.await_count >= 1
