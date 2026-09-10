"""Tests for Hugging Face dataset publishing."""

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from data4ai.exceptions import PublishingError
from data4ai.publisher import HuggingFacePublisher


def test_validate_token():
    assert HuggingFacePublisher().validate_token() is False
    with patch("data4ai.publisher.HfApi") as api_class:
        api_class.return_value.whoami.return_value = {"name": "user"}
        assert HuggingFacePublisher("token").validate_token() is True
        api_class.return_value.whoami.side_effect = RuntimeError("bad token")
        assert HuggingFacePublisher("token").validate_token() is False


def test_push_dataset_with_metadata(tmp_path):
    (tmp_path / "data.jsonl").write_text("{}\n")
    (tmp_path / "metadata.json").write_text(
        json.dumps({"schema": "chatml", "row_count": 1, "model": "model"})
    )
    with (
        patch("data4ai.publisher.HfApi") as api_class,
        patch("data4ai.publisher.create_repo") as create_repo,
        patch("data4ai.publisher.upload_file") as upload_file,
        patch("data4ai.publisher.generate_dataset_card", return_value="card") as card,
    ):
        api_class.return_value.whoami.return_value = {"name": "user"}
        publisher = HuggingFacePublisher("token")
        result = publisher.push_dataset(tmp_path, "dataset", description="description")

    assert result == "https://huggingface.co/datasets/user/dataset"
    create_repo.assert_called_once()
    card.assert_called_once()
    assert (tmp_path / "README.md").read_text() == "card"
    assert upload_file.call_count == 3


def test_push_dataset_organization_and_upload_failure(tmp_path):
    (tmp_path / "data.jsonl").write_text("{}\n")
    (tmp_path / "README.md").write_text("existing")
    with (
        patch("data4ai.publisher.HfApi"),
        patch("data4ai.publisher.create_repo"),
        patch("data4ai.publisher.upload_file", side_effect=RuntimeError("upload")),
    ):
        publisher = HuggingFacePublisher("token", organization="org")
        assert publisher.push_dataset(tmp_path, "dataset") == (
            "https://huggingface.co/datasets/org/dataset"
        )


@pytest.mark.parametrize("create_data", [False, True])
def test_push_dataset_validation_errors(tmp_path, create_data):
    path = tmp_path / "dataset"
    if create_data:
        path.mkdir()
    with pytest.raises(PublishingError):
        HuggingFacePublisher("token", "org").push_dataset(path, "dataset")

    with (
        patch("data4ai.publisher.check_environment_variables"),
        pytest.raises(PublishingError, match="token is required"),
    ):
        HuggingFacePublisher().push_dataset(path, "dataset")


def test_list_delete_and_update_dataset():
    with (
        patch("data4ai.publisher.HfApi") as api_class,
        patch("data4ai.publisher.upload_file") as upload_file,
    ):
        api = api_class.return_value
        api.whoami.return_value = {"name": "user"}
        api.list_datasets.return_value = [SimpleNamespace(id="user/one")]
        publisher = HuggingFacePublisher("token")

        assert publisher.list_datasets() == ["user/one"]
        assert publisher.delete_dataset("dataset") is True
        api.delete_repo.assert_called_with(
            repo_id="user/dataset", repo_type="dataset", token="token"
        )
        assert publisher.update_dataset_card("org/dataset", "card") is True
        upload_file.assert_called_once()


def test_publisher_operation_failures():
    publisher = HuggingFacePublisher()
    with pytest.raises(PublishingError):
        publisher.list_datasets()
    assert publisher.delete_dataset("dataset") is False
    assert publisher.update_dataset_card("dataset", "card") is False

    with patch("data4ai.publisher.HfApi") as api_class:
        api_class.return_value.delete_repo.side_effect = RuntimeError("delete")
        assert HuggingFacePublisher("token").delete_dataset("org/dataset") is False
