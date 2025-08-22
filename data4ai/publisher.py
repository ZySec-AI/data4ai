"""HuggingFace dataset publishing functionality."""

import logging
from pathlib import Path
from typing import Optional

from huggingface_hub import HfApi, create_repo, upload_file
from huggingface_hub.utils import HfHubHTTPError

from data4ai.error_handler import check_environment_variables
from data4ai.exceptions import AuthenticationError, PublishingError
from data4ai.utils import generate_dataset_card

logger = logging.getLogger("data4ai")


class HuggingFacePublisher:
    """Handle dataset publishing to HuggingFace Hub."""

    def __init__(self, token: Optional[str] = None, organization: Optional[str] = None):
        """Initialize HuggingFace publisher."""
        self.token = token
        self.organization = organization
        self.api = HfApi(token=token) if token else None

    def push_dataset(
        self,
        dataset_dir: Path,
        repo_name: str,
        private: bool = False,
        description: Optional[str] = None,
    ) -> str:
        """Push dataset to HuggingFace Hub."""
        try:
            if not self.token:
                # Check environment variables and provide helpful messages
                check_environment_variables(required_for_operation=["HF_TOKEN"])
                raise AuthenticationError(
                    "HuggingFace token is required for publishing datasets"
                )

            # Validate dataset directory
            if not dataset_dir.exists():
                raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

            jsonl_path = dataset_dir / "data.jsonl"
            if not jsonl_path.exists():
                raise FileNotFoundError(f"Dataset file not found: {jsonl_path}")

            # Create full repository name
            if self.organization:
                full_repo_name = f"{self.organization}/{repo_name}"
            else:
                # Get username from API
                user_info = self.api.whoami()
                username = user_info.get("name", "")
                full_repo_name = f"{username}/{repo_name}"

            logger.info(f"Creating repository: {full_repo_name}")

            # Create repository
            try:
                repo_url = create_repo(
                    repo_id=full_repo_name,
                    repo_type="dataset",
                    private=private,
                    token=self.token,
                    exist_ok=True,
                )
                logger.info(f"Repository created/found: {repo_url}")
            except HfHubHTTPError as e:
                if "already exists" in str(e):
                    repo_url = f"https://huggingface.co/datasets/{full_repo_name}"
                    logger.info(f"Repository already exists: {repo_url}")
                else:
                    raise PublishingError(
                        f"Failed to create repository: {str(e)}"
                    ) from e

            # Generate dataset card if not exists
            readme_path = dataset_dir / "README.md"
            if not readme_path.exists():
                # Read metadata to get schema and stats
                metadata_path = dataset_dir / "metadata.json"
                if metadata_path.exists():
                    import json

                    with open(metadata_path) as f:
                        metadata = json.load(f)

                    dataset_card = generate_dataset_card(
                        dataset_name=repo_name,
                        schema=metadata.get("schema", "alpaca"),
                        row_count=metadata.get("row_count", 0),
                        model=metadata.get("model", "unknown"),
                        description=description,
                        tags=["ZySecAI", "Data4AI", "instruction-tuning", "dataset"],
                    )
                else:
                    dataset_card = generate_dataset_card(
                        dataset_name=repo_name,
                        schema="alpaca",
                        row_count=0,
                        model="unknown",
                        description=description,
                        tags=["ZySecAI", "Data4AI", "instruction-tuning", "dataset"],
                    )

                with open(readme_path, "w") as f:
                    f.write(dataset_card)

            # Upload files
            files_to_upload = [
                "data.jsonl",
                "README.md",
                "metadata.json",
                "validation_report.json",
                "completed.xlsx",
            ]

            uploaded_files = []
            for file_name in files_to_upload:
                file_path = dataset_dir / file_name
                if file_path.exists():
                    logger.info(f"Uploading {file_name}")
                    try:
                        upload_file(
                            path_or_fileobj=str(file_path),
                            path_in_repo=file_name,
                            repo_id=full_repo_name,
                            repo_type="dataset",
                            token=self.token,
                        )
                        uploaded_files.append(file_name)
                    except Exception as e:
                        logger.warning(f"Failed to upload {file_name}: {e}")

            logger.info(f"Successfully uploaded {len(uploaded_files)} files")

            # Return the dataset URL
            dataset_url = f"https://huggingface.co/datasets/{full_repo_name}"
            return dataset_url

        except Exception as e:
            logger.error(f"Failed to push dataset: {e}")
            raise PublishingError(f"Failed to push dataset: {str(e)}") from e

    def validate_token(self) -> bool:
        """Validate HuggingFace token."""
        try:
            if not self.token:
                return False

            api = HfApi(token=self.token)
            user_info = api.whoami()
            logger.info(f"Authenticated as: {user_info.get('name', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False

    def list_datasets(self) -> list:
        """List user's datasets on HuggingFace."""
        try:
            if not self.token:
                raise AuthenticationError("HuggingFace token required")

            api = HfApi(token=self.token)
            user_info = api.whoami()
            username = user_info.get("name", "")

            # List datasets
            datasets = api.list_datasets(author=username)
            return [d.id for d in datasets]

        except Exception as e:
            logger.error(f"Failed to list datasets: {e}")
            raise PublishingError(f"Failed to list datasets: {str(e)}") from e

    def delete_dataset(self, repo_name: str) -> bool:
        """Delete a dataset from HuggingFace Hub."""
        try:
            if not self.token:
                raise AuthenticationError("HuggingFace token required")

            # Create full repository name
            if "/" not in repo_name:
                user_info = self.api.whoami()
                username = user_info.get("name", "")
                full_repo_name = f"{username}/{repo_name}"
            else:
                full_repo_name = repo_name

            # Delete repository
            self.api.delete_repo(
                repo_id=full_repo_name,
                repo_type="dataset",
                token=self.token,
            )

            logger.info(f"Deleted dataset: {full_repo_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete dataset: {e}")
            return False

    def update_dataset_card(
        self,
        repo_name: str,
        dataset_card: str,
    ) -> bool:
        """Update dataset card on HuggingFace Hub."""
        try:
            if not self.token:
                raise AuthenticationError("HuggingFace token required")

            # Create full repository name
            if "/" not in repo_name:
                user_info = self.api.whoami()
                username = user_info.get("name", "")
                full_repo_name = f"{username}/{repo_name}"
            else:
                full_repo_name = repo_name

            # Upload README
            upload_file(
                path_or_fileobj=dataset_card.encode(),
                path_in_repo="README.md",
                repo_id=full_repo_name,
                repo_type="dataset",
                token=self.token,
            )

            logger.info(f"Updated dataset card for: {full_repo_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update dataset card: {e}")
            return False
