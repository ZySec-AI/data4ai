"""Tests for dataset deduplication strategies."""

from unittest.mock import patch

import pytest

from data4ai.deduplicator import (
    DeduplicationStats,
    Deduplicator,
    IncrementalDeduplicator,
)


def test_rejects_unknown_strategy():
    with pytest.raises(ValueError, match="Unknown strategy"):
        Deduplicator("unknown")


def test_exact_and_empty_deduplication():
    deduplicator = Deduplicator("exact")
    first = {"instruction": "Question", "output": "Answer"}
    second = {"output": "Answer", "instruction": "Question"}
    unique, stats = deduplicator.deduplicate([first, second, {"output": "Other"}])
    assert unique == [first, {"output": "Other"}]
    assert stats.duplicates_removed == 1
    assert stats.threshold is None
    assert deduplicator.deduplicate([])[1].total_items == 0


def test_instruction_and_content_strategies():
    instruction_items = [
        {"instruction": " Same ", "output": "one"},
        {"instruction": "same", "output": "two"},
        {"output": "missing one"},
        {"output": "missing two"},
    ]
    unique, _ = Deduplicator("instruction").deduplicate(instruction_items)
    assert unique == [instruction_items[0], instruction_items[2], instruction_items[3]]

    content_items = [
        {"output": "same"},
        {"response": "same"},
        {
            "conversations": [
                {"from": "user", "value": "question"},
                {"from": "assistant", "value": "different"},
            ]
        },
    ]
    unique, _ = Deduplicator("content").deduplicate(content_items)
    assert unique == [content_items[0], content_items[2]]


def test_fuzzy_strategy_and_verbose_output():
    items = [
        {"instruction": "write a test", "output": "answer"},
        {"instruction": "write a test", "output": "answer"},
        {"instruction": "different", "output": "result"},
    ]
    with patch("data4ai.deduplicator.console.print") as print_mock:
        unique, stats = Deduplicator("fuzzy", threshold=0.9).deduplicate(
            items, verbose=True
        )
    assert unique == [items[0], items[2]]
    assert stats.threshold == 0.9
    assert print_mock.call_count == 2


def test_item_string_formats_and_similarity():
    deduplicator = Deduplicator()
    chat = {
        "conversations": [
            {"from": "human", "value": "hello"},
            {"from": "gpt", "value": "hi"},
        ]
    }
    assert deduplicator._item_to_string(chat) == "human: hello gpt: hi"
    assert (
        deduplicator._item_to_string(
            {"instruction": "do", "context": "ctx", "response": "done"}
        )
        == "do ctx done"
    )
    assert deduplicator._item_to_string({"b": 2, "a": 1}) == '{"a": 1, "b": 2}'
    assert deduplicator._extract_content(chat) == "hi"
    assert deduplicator._calculate_similarity({"output": "x"}, {"output": "x"}) == 1


def test_incremental_deduplicator():
    incremental = IncrementalDeduplicator("exact")
    item = {"instruction": "one", "output": "answer"}
    assert incremental.is_duplicate(item) is False
    assert incremental.add_item(item) is True
    assert incremental.is_duplicate(item) is True
    assert incremental.add_item(item) is False
    assert incremental.get_unique_items() == [item]
    assert incremental.get_unique_items() is not incremental.seen_items


def test_stats_display_includes_threshold():
    stats = DeduplicationStats(2, 1, 1, "fuzzy", 0.9)
    with patch("data4ai.deduplicator.console.print") as print_mock:
        stats.display()
    print_mock.assert_called_once()
