from __future__ import annotations

from .file import AnyFileConfig as AnyFileConfig
from .file import BaseFileConfig as BaseFileConfig
from .file import CachedPath as CachedPath
from .file import CachedPathConfig as CachedPathConfig
from .file import RemoteSSHFileConfig as RemoteSSHFileConfig
from .file import open_file_config as open_file_config
from .file import resolve_file_config as resolve_file_config

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    # For Python <3.8
    from importlib_metadata import (  # pyright: ignore[reportMissingImports]
        PackageNotFoundError,
        version,
    )

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "unknown"
