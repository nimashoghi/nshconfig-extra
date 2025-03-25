from __future__ import annotations

import contextlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import nshconfig as C


class BaseFileConfig(C.Config, ABC):
    @abstractmethod
    def resolve(self) -> Path:
        """
        Resolves the file and returns a local Path.
        For remote files, this may involve downloading the file.
        """

    @abstractmethod
    def open(self, mode: str = "rb") -> contextlib.AbstractContextManager[Any]:
        """
        Opens the file and returns a file handle wrapped in a context manager.
        """
