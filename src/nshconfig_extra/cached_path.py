import importlib.util
import logging
from pathlib import Path

import nshconfig as C
from typing_extensions import override

log = logging.getLogger(__name__)


class CachedPath(C.Config):
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
    def __post_init__(self):
        super().__post_init__()
        if not importlib.util.find_spec("cached_path"):
            raise ImportError(
                "The 'cached_path' library is required to use 'CachedPath'. "
                "Please make sure you install nshconfig with all extras: `pip install nshconfig[extra]`."
            )

    def resolve(self) -> Path:
        from cached_path import cached_path

        return cached_path(
            self.uri,
            cache_dir=self.cache_dir,
            extract_archive=self.extract_archive,
            force_extract=self.force_extract,
            quiet=self.quiet,
        )

    @classmethod
    def from_uri(
        cls,
        uri: str | Path,
        cache_dir: Path | None = None,
        extract_archive: bool = False,
        force_extract: bool = False,
        quiet: bool = False,
    ):
        return cls(
            uri=uri,
            cache_dir=cache_dir,
            extract_archive=extract_archive,
            force_extract=force_extract,
            quiet=quiet,
        ).resolve()
