from __future__ import annotations

import logging
from pathlib import Path

from cached_path import cached_path
from typing_extensions import override

from .base import BaseFileConfig

log = logging.getLogger(__name__)


class CachedPathConfig(BaseFileConfig):
    uri: str | Path
    """
    The origin of the cached path.

    This can be a local path, a downloadable URL, an S3 URL, a GCS URL, or an Hugging Face Hub URL.
    """

    cache_dir: Path | None = None
    """
    The directory to cache the file in.

    If not specified, the file will be cached in the default cache directory for `cached_path`.
    """

    extract_archive: bool = False
    """
    Whether to extract the archive after downloading it.
    """

    force_extract: bool = False
    """
    Whether to force extraction of the archive even if the extracted directory already exists.
    """

    quiet: bool = False
    """
    Whether to suppress the progress bar.
    """

    @override
    def resolve(self) -> Path:
        return cached_path(
            self.uri,
            cache_dir=self.cache_dir,
            extract_archive=self.extract_archive,
            force_extract=self.force_extract,
            quiet=self.quiet,
        )

    @override
    def open(self, mode: str = "rb"):
        return open(self.resolve(), mode)
