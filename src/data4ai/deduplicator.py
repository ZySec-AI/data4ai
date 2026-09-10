"""Deduplication module for Data4AI datasets."""

import hashlib
import json
import logging
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Optional

from rich.console import Console
from rich.table import Table

logger = logging.getLogger("data4ai")
console = Console()


@dataclass
class DeduplicationStats:
    """Statistics from deduplication process."""

    total_items: int
    unique_items: int
    duplicates_removed: int
    method: str
    threshold: Optional[float] = None

    def display(self) -> None:
        """Display deduplication statistics."""
        table = Table(title="Deduplication Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Items", str(self.total_items))
        table.add_row("Unique Items", str(self.unique_items))
        table.add_row("Duplicates Removed", str(self.duplicates_removed))
        table.add_row(
            "Reduction",
            f"{self.duplicates_removed / max(self.total_items, 1) * 100:.1f}%",
        )
        table.add_row("Method", self.method)

        if self.threshold is not None:
            table.add_row("Similarity Threshold", f"{self.threshold:.2f}")

        console.print(table)


class Deduplicator:
    """Handle dataset deduplication with multiple strategies."""

    STRATEGIES = ["exact", "fuzzy", "instruction", "content"]

    def __init__(self, strategy: str = "exact", threshold: float = 0.95):
        """Initialize deduplicator.

        Args:
            strategy: Deduplication strategy (exact, fuzzy, instruction, content)
            threshold: Similarity threshold for fuzzy matching (0-1)
        """
        if strategy not in self.STRATEGIES:
            raise ValueError(
                f"Unknown strategy: {strategy}. Use one of {self.STRATEGIES}"
            )

        self.strategy = strategy
        self.threshold = threshold
        logger.info(f"Deduplicator initialized with {strategy} strategy")

    def deduplicate(
        self, dataset: list[dict[str, Any]], verbose: bool = False
    ) -> tuple[list[dict[str, Any]], DeduplicationStats]:
        """Deduplicate dataset based on selected strategy.

        Args:
            dataset: List of dataset items
            verbose: Whether to show detailed progress

        Returns:
            Tuple of (deduplicated dataset, statistics)
        """
        if not dataset:
            return dataset, DeduplicationStats(0, 0, 0, self.strategy)

        total = len(dataset)

        if verbose:
            console.print(
                f"Deduplicating {total} items using {self.strategy} strategy...",
                style="blue",
            )

        if self.strategy == "exact":
            unique = self._dedupe_exact(dataset)
        elif self.strategy == "fuzzy":
            unique = self._dedupe_fuzzy(dataset, verbose)
        elif self.strategy == "instruction":
            unique = self._dedupe_by_field(dataset, "instruction")
        elif self.strategy == "content":
            unique = self._dedupe_content(dataset)
        else:
            unique = dataset

        stats = DeduplicationStats(
            total_items=total,
            unique_items=len(unique),
            duplicates_removed=total - len(unique),
            method=self.strategy,
            threshold=self.threshold if self.strategy == "fuzzy" else None,
        )

        if verbose:
            stats.display()

        return unique, stats

    def _dedupe_exact(self, dataset: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove exact duplicates using hash comparison.

        Args:
            dataset: Dataset to deduplicate

        Returns:
            Deduplicated dataset
        """
        seen_hashes: set[str] = set()
        unique: list[dict[str, Any]] = []

        for item in dataset:
            # Create hash of the item
            item_hash = self._hash_item(item)

            if item_hash not in seen_hashes:
                seen_hashes.add(item_hash)
                unique.append(item)

        return unique

    def _dedupe_fuzzy(
        self, dataset: list[dict[str, Any]], verbose: bool = False
    ) -> list[dict[str, Any]]:
        """Remove near-duplicates using fuzzy matching.

        Args:
            dataset: Dataset to deduplicate
            verbose: Show progress

        Returns:
            Deduplicated dataset
        """
        unique: list[dict[str, Any]] = []

        for i, item in enumerate(dataset):
            is_duplicate = False

            # Compare with existing unique items
            for unique_item in unique:
                similarity = self._calculate_similarity(item, unique_item)

                if similarity >= self.threshold:
                    is_duplicate = True
                    if verbose:
                        logger.debug(
                            f"Item {i} is duplicate (similarity: {similarity:.2f})"
                        )
                    break

            if not is_duplicate:
                unique.append(item)

        return unique

    def _dedupe_by_field(
        self, dataset: list[dict[str, Any]], field: str
    ) -> list[dict[str, Any]]:
        """Deduplicate based on a specific field.

        Args:
            dataset: Dataset to deduplicate
            field: Field to use for deduplication

        Returns:
            Deduplicated dataset
        """
        seen_values: set[str] = set()
        unique: list[dict[str, Any]] = []

        for item in dataset:
            value = str(item.get(field, ""))

            # Normalize value
            normalized = value.strip().lower()

            if normalized and normalized not in seen_values:
                seen_values.add(normalized)
                unique.append(item)
            elif not normalized:
                # Keep items without the field
                unique.append(item)

        return unique

    def _dedupe_content(self, dataset: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Deduplicate based on main content fields.

        Args:
            dataset: Dataset to deduplicate

        Returns:
            Deduplicated dataset
        """
        seen_content: set[str] = set()
        unique: list[dict[str, Any]] = []

        for item in dataset:
            # Extract main content based on schema
            content = self._extract_content(item)

            if content not in seen_content:
                seen_content.add(content)
                unique.append(item)

        return unique

    def _hash_item(self, item: dict[str, Any]) -> str:
        """Create hash of dictionary item.

        Args:
            item: Item to hash

        Returns:
            Hash string
        """
        # Sort keys for consistent hashing
        sorted_str = json.dumps(item, sort_keys=True)
        return hashlib.sha256(sorted_str.encode()).hexdigest()

    def _calculate_similarity(
        self, item1: dict[str, Any], item2: dict[str, Any]
    ) -> float:
        """Calculate similarity between two items.

        Args:
            item1: First item
            item2: Second item

        Returns:
            Similarity score (0-1)
        """
        # Convert to strings for comparison
        str1 = self._item_to_string(item1)
        str2 = self._item_to_string(item2)

        # Use SequenceMatcher for similarity
        return SequenceMatcher(None, str1, str2).ratio()

    def _item_to_string(self, item: dict[str, Any]) -> str:
        """Convert item to string for comparison.

        Args:
            item: Item to convert

        Returns:
            String representation
        """
        # Handle different schemas
        if "conversations" in item:
            # ShareGPT format
            parts = []
            for conv in item.get("conversations", []):
                parts.append(f"{conv.get('from', '')}: {conv.get('value', '')}")
            return " ".join(parts)
        elif "instruction" in item:
            # Alpaca/Dolly format
            parts = [
                item.get("instruction", ""),
                item.get("input", "") or item.get("context", ""),
                item.get("output", "") or item.get("response", ""),
            ]
            return " ".join(filter(None, parts))
        else:
            # Generic
            return json.dumps(item, sort_keys=True)

    def _extract_content(self, item: dict[str, Any]) -> str:
        """Extract main content from item.

        Args:
            item: Item to extract from

        Returns:
            Content string
        """
        # Focus on output/response content
        if "output" in item:
            return item["output"]
        elif "response" in item:
            return item["response"]
        elif "conversations" in item:
            # Get assistant responses
            responses = []
            for conv in item.get("conversations", []):
                if conv.get("from") in ["gpt", "assistant"]:
                    responses.append(conv.get("value", ""))
            return " ".join(responses)
        else:
            return self._item_to_string(item)


class IncrementalDeduplicator:
    """Deduplicate incrementally during generation."""

    def __init__(self, strategy: str = "exact"):
        """Initialize incremental deduplicator.

        Args:
            strategy: Deduplication strategy
        """
        self.deduplicator = Deduplicator(strategy)
        self.seen_items: list[dict[str, Any]] = []

    def is_duplicate(self, item: dict[str, Any]) -> bool:
        """Check if item is duplicate of seen items.

        Args:
            item: Item to check

        Returns:
            True if duplicate
        """
        # Check against seen items
        combined = self.seen_items + [item]
        deduped, _ = self.deduplicator.deduplicate(combined, verbose=False)

        return len(deduped) == len(self.seen_items)

    def add_item(self, item: dict[str, Any]) -> bool:
        """Add item if not duplicate.

        Args:
            item: Item to add

        Returns:
            True if added (not duplicate)
        """
        if not self.is_duplicate(item):
            self.seen_items.append(item)
            return True
        return False

    def get_unique_items(self) -> list[dict[str, Any]]:
        """Get all unique items seen so far.

        Returns:
            List of unique items
        """
        return self.seen_items.copy()
