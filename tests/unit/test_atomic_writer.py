"""Unit tests for atomic writer module."""

import gzip
import json

import pytest

from data4ai.atomic_writer import AtomicWriter, ShardedWriter


class TestAtomicWriter:
    """Test atomic writer functionality."""

    def test_write_jsonl_new_file(self, temp_dir):
        """Test writing JSONL to a new file."""
        data = [{"id": 1, "text": "Hello"}, {"id": 2, "text": "World"}]

        file_path = temp_dir / "test.jsonl"
        count = AtomicWriter.write_jsonl(data, file_path)

        assert count == 2
        assert file_path.exists()

        # Verify content
        with open(file_path) as f:
            lines = f.readlines()
            assert len(lines) == 2
            assert json.loads(lines[0]) == data[0]
            assert json.loads(lines[1]) == data[1]

    def test_write_jsonl_append(self, temp_dir):
        """Test appending to existing JSONL file."""
        initial_data = [{"id": 1, "text": "Initial"}]
        append_data = [{"id": 2, "text": "Appended"}]

        file_path = temp_dir / "test.jsonl"

        # Write initial data
        AtomicWriter.write_jsonl(initial_data, file_path)

        # Append new data
        count = AtomicWriter.write_jsonl(append_data, file_path, append=True)

        assert count == 1

        # Verify combined content
        with open(file_path) as f:
            lines = f.readlines()
            assert len(lines) == 2
            assert json.loads(lines[0]) == initial_data[0]
            assert json.loads(lines[1]) == append_data[0]

    def test_write_jsonl_compressed(self, temp_dir):
        """Test writing compressed JSONL file."""
        data = [{"id": 1, "text": "Compressed data"}]

        file_path = temp_dir / "test.jsonl.gz"
        count = AtomicWriter.write_jsonl(data, file_path, compress=True)

        assert count == 1
        assert file_path.exists()

        # Verify compressed content
        with gzip.open(file_path, "rt") as f:
            line = f.readline()
            assert json.loads(line) == data[0]

    def test_write_json(self, temp_dir):
        """Test atomic JSON write."""
        data = {"key": "value", "number": 42}

        file_path = temp_dir / "test.json"
        AtomicWriter.write_json(data, file_path)

        assert file_path.exists()

        with open(file_path) as f:
            loaded = json.load(f)
            assert loaded == data

    def test_write_text(self, temp_dir):
        """Test atomic text write."""
        content = "Hello, World!\nThis is a test."

        file_path = temp_dir / "test.txt"
        AtomicWriter.write_text(content, file_path)

        assert file_path.exists()

        with open(file_path) as f:
            assert f.read() == content

    def test_atomic_failure_recovery(self, temp_dir):
        """Test that atomic write doesn't corrupt file on failure."""
        initial_data = [{"id": 1, "text": "Original"}]
        bad_data = [{"id": 2, "bad": object()}]  # This will fail to serialize

        file_path = temp_dir / "test.jsonl"

        # Write initial good data
        AtomicWriter.write_jsonl(initial_data, file_path)

        # Try to write bad data (should fail)
        with pytest.raises(TypeError):
            AtomicWriter.write_jsonl(bad_data, file_path)

        # Original file should still be intact
        with open(file_path) as f:
            line = f.readline()
            assert json.loads(line) == initial_data[0]

    def test_creates_parent_directories(self, temp_dir):
        """Test that parent directories are created if they don't exist."""
        data = [{"id": 1}]

        file_path = temp_dir / "nested" / "dirs" / "test.jsonl"
        AtomicWriter.write_jsonl(data, file_path)

        assert file_path.exists()
        assert file_path.parent.exists()


class TestShardedWriter:
    """Test sharded writer functionality."""

    def test_basic_sharding(self, temp_dir):
        """Test that data is sharded correctly."""
        writer = ShardedWriter(temp_dir, shard_size=2)

        # Write 5 records (should create 3 shards)
        for i in range(5):
            writer.write({"id": i, "text": f"Record {i}"})

        stats = writer.finalize()

        assert stats["total_records"] == 5
        assert stats["shards"] == 3

        # Check shard files
        shards = list(temp_dir.glob("data-*.jsonl"))
        assert len(shards) == 3

    def test_compressed_sharding(self, temp_dir):
        """Test sharding with compression."""
        writer = ShardedWriter(temp_dir, shard_size=2, compress=True)

        # Write 3 records
        for i in range(3):
            writer.write({"id": i})

        stats = writer.finalize()

        assert stats["compressed"] is True
        assert stats["shards"] == 2

        # Check compressed files
        shards = list(temp_dir.glob("data-*.jsonl.gz"))
        assert len(shards) == 2

    def test_flush_on_finalize(self, temp_dir):
        """Test that remaining data is flushed on finalize."""
        writer = ShardedWriter(temp_dir, shard_size=10)

        # Write only 3 records (less than shard size)
        for i in range(3):
            writer.write({"id": i})

        # No shards yet
        shards = list(temp_dir.glob("data-*.jsonl"))
        assert len(shards) == 0

        # Finalize should flush
        stats = writer.finalize()

        assert stats["total_records"] == 3
        assert stats["shards"] == 1

        shards = list(temp_dir.glob("data-*.jsonl"))
        assert len(shards) == 1
