import importlib.util
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import nshconfig as C

log = logging.getLogger(__name__)


class HFPath(C.Config):
    repo: str
    """Path to the repo containing the model files.

    Format is {user}/{repo}"""

    path: str
    """Path to the file within the repo."""

    branch: str = "main"
    """Branch to use."""

    @classmethod
    def from_hf_path(cls, path: str):
        """Parse a Hugging Face path.

        Args:
            path (str): Path to parse.

        Returns:
            HFPath: Parsed path.
        """
        # Regular expression to match the Hugging Face path format
        pattern = r"^([^/]+/[^/]+)(?:@([^/]+))?(?:/(.+))?$"
        match = re.match(pattern, path)

        if not match:
            raise ValueError(f"Invalid Hugging Face path: {path}")

        repo, branch, file_path = match.groups()

        # If branch is not specified, use the default "main"
        branch = branch or cls.branch

        # If file_path is not specified, use an empty string
        file_path = file_path or ""

        return cls(repo=repo, path=file_path, branch=branch)

    @classmethod
    def from_hf_url(cls, url: str):
        """Parse a Hugging Face URL.

        Args:
            url (str): URL to parse.

        Returns:
            HFPath: Parsed path.
        """
        # Parse the URL
        parsed_url = urlparse(url)

        # Ensure it's a Hugging Face URL
        if not parsed_url.netloc.endswith("huggingface.co"):
            raise ValueError(f"Not a valid Hugging Face URL: {url}")

        # Split the path
        path_parts = parsed_url.path.strip("/").split("/")

        # Extract repo, branch, and file path
        if len(path_parts) < 4 or path_parts[1] != "resolve":
            raise ValueError(f"Invalid Hugging Face URL format: {url}")

        repo = "/".join(path_parts[:2])
        branch = path_parts[3]
        file_path = "/".join(path_parts[4:])

        # Decode URL-encoded characters
        file_path = unquote(file_path)

        return cls(repo=repo, path=file_path, branch=branch)

    def download(self, **kwargs: Any):
        """Download the file if it doesn't exist and return the path.

        Args:
            **kwargs: Additional arguments to pass to ``HfApi.hf_hub_download``.

        Returns:
            Path: Local path to the downloaded file.
        """
        # If we don't have HuggingFace Hub installed, error out.
        if importlib.util.find_spec("huggingface_hub") is None:
            raise ImportError("Please install huggingface_hub to use `HFPath`.")

        import huggingface_hub as hfhub  # type: ignore

        try:
            path = hfhub.HfApi().hf_hub_download(
                self.repo,
                self.path,
                revision=self.branch,
                **kwargs,
            )
            path = Path(path)
            log.info(f"Downloaded to {path}")
            return path
        except Exception:
            log.exception(f"Error downloading file: {self}")
            raise
