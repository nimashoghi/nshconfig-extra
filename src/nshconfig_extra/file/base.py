from __future__ import annotations

import contextlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import nshconfig as C
from typing_extensions import TypeAliasType, assert_never


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


AnyFileConfig = TypeAliasType("AnyFileConfig", str | Path | BaseFileConfig)


def resolve_file_config(file: AnyFileConfig) -> Path:
    match file:
        case str() | Path():
            return Path(file)
        case BaseFileConfig():
            return file.resolve()
        case _:
            assert_never(file)


def open_file_config(
    file: AnyFileConfig,
    mode: str = "rb",
) -> contextlib.AbstractContextManager[Any]:
    match file:
        case str() | Path():
            return open(file, mode)
        case BaseFileConfig():
            return file.open(mode)
        case _:
            assert_never(file)
