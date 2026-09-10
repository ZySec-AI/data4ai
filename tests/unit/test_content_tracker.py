"""Tests for content hashing and change tracking."""

from data4ai.content_tracker import ContentTracker


def test_file_hash_info_and_change_detection(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("first")

    info = ContentTracker.get_file_info(path)
    assert info["exists"] is True
    assert info["size"] == 5
    assert info["hash"] == ContentTracker.calculate_content_hash("first")
    assert ContentTracker.has_file_changed(path, info) is False

    path.write_text("second value")
    assert ContentTracker.has_file_changed(path, info) is True
    path.unlink()
    assert ContentTracker.has_file_changed(path, info) is True
    assert ContentTracker.get_file_info(path)["exists"] is False
    assert ContentTracker.calculate_file_hash(path) == ""


def test_scan_directory_filters_files(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "one.txt").write_text("one")
    (tmp_path / "skip.txt").write_text("skip")
    (tmp_path / "nested" / "two.txt").write_text("two")
    (tmp_path / "nested" / "other.md").write_text("other")

    recursive = ContentTracker.scan_directory(
        tmp_path, patterns=["*.txt"], exclude_patterns=["skip.txt"]
    )
    assert {item["path"] for item in recursive} == {
        str(tmp_path / "one.txt"),
        str(tmp_path / "nested" / "two.txt"),
    }
    direct = ContentTracker.scan_directory(
        tmp_path, patterns=["*.txt"], recursive=False
    )
    assert {item["path"] for item in direct} == {
        str(tmp_path / "one.txt"),
        str(tmp_path / "skip.txt"),
    }
    assert ContentTracker.scan_directory(tmp_path / "missing") == []


def test_youtube_hashes_and_change_categories():
    video = {
        "id": "abc",
        "channel": "channel",
        "title": "title",
        "duration": 10,
        "upload_date": "today",
    }
    content_id = ContentTracker.create_youtube_content_id(video)
    content_hash = ContentTracker.create_youtube_content_hash(video, "transcript")
    assert len(content_id) == 16
    assert content_hash != ContentTracker.create_youtube_content_hash(video)

    current = [
        {**video, "title": "new", "content_hash": "new-hash"},
        {**video, "id": "new", "content_hash": "brand-new"},
    ]
    changed_id = ContentTracker.create_youtube_content_id(current[0])
    cached = {changed_id: {"content_hash": "old-hash"}}
    new, changed, unchanged = ContentTracker.detect_content_changes(
        current, cached, "youtube"
    )
    assert new == [current[1]]
    assert changed == [current[0]]
    assert unchanged == []


def test_file_and_generic_change_categories():
    current = [
        {"path": "new", "hash": "one"},
        {"path": "changed", "hash": "two"},
        {"path": "same", "hash": "three"},
    ]
    cached = {
        "changed": {"hash": "old"},
        "same": {"hash": "three"},
    }
    new, changed, unchanged = ContentTracker.detect_content_changes(current, cached)
    assert new == [current[0]]
    assert changed == [current[1]]
    assert unchanged == [current[2]]

    generic = [{"id": "one", "hash": "same"}]
    assert ContentTracker.detect_content_changes(
        generic, {"one": {"hash": "same"}}, "generic"
    ) == ([], [], generic)


def test_registry_moves_and_folder_fingerprint(tmp_path):
    entry = ContentTracker.create_content_registry_entry(
        "id", "source", "hash", 5, {"kind": "test"}
    )
    assert entry["metadata"] == {"kind": "test"}
    assert entry["created_at"] == entry["updated_at"]

    current = [{"path": "new.txt", "hash": "same"}]
    cached = {"old.txt": {"path": "old.txt", "hash": "same"}}
    assert ContentTracker.find_moved_files(current, cached) == [
        ("old.txt", "new.txt", current[0])
    ]

    assert ContentTracker.get_folder_structure_fingerprint(tmp_path / "missing") == ""
    first = ContentTracker.get_folder_structure_fingerprint(tmp_path)
    assert ContentTracker.should_rescan_folder(tmp_path, first) is False
    assert ContentTracker.should_rescan_folder(tmp_path, "") is True
    assert (
        ContentTracker.should_rescan_folder(tmp_path, first, force_rescan=True) is True
    )
    (tmp_path / "new.txt").write_text("new")
    assert ContentTracker.should_rescan_folder(tmp_path, first) is True
