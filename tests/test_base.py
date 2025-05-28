"""Tests for the base file configuration functionality."""

from __future__ import annotations

import contextlib
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from nshconfig_extra.file import (
    AnyFileConfig,
    BaseFileConfig,
    open_file_config,
    resolve_file_config,
)


class MockFileConfig(BaseFileConfig):
    """Mock implementation of BaseFileConfig for testing."""

    path: Path

    def resolve(self) -> Path:
        return self.path

    @contextlib.contextmanager
    def open(self, mode: str = "rb"):
        with open(self.path, mode) as f:
            yield f


class TestBaseFileConfig:
    """Test the BaseFileConfig abstract base class."""

    def test_abstract_methods_exist(self):
        """Test that BaseFileConfig has the required abstract methods."""
        assert hasattr(BaseFileConfig, "resolve")
        assert hasattr(BaseFileConfig, "open")

    def test_cannot_instantiate_directly(self):
        """Test that BaseFileConfig cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseFileConfig()


class TestResolveFileConfig:
    """Test the resolve_file_config utility function."""

    def test_resolve_string_path(self, sample_text_file):
        """Test resolving a string path."""
        result = resolve_file_config(str(sample_text_file))
        assert result == sample_text_file
        assert isinstance(result, Path)

    def test_resolve_path_object(self, sample_text_file):
        """Test resolving a Path object."""
        result = resolve_file_config(sample_text_file)
        assert result == sample_text_file
        assert isinstance(result, Path)

    def test_resolve_base_file_config(self, sample_text_file):
        """Test resolving a BaseFileConfig instance."""
        mock_config = MockFileConfig(path=sample_text_file)
        result = resolve_file_config(mock_config)
        assert result == sample_text_file
        assert isinstance(result, Path)

    def test_resolve_nonexistent_path(self, nonexistent_file):
        """Test resolving a nonexistent path (should still work)."""
        result = resolve_file_config(str(nonexistent_file))
        assert result == nonexistent_file
        assert isinstance(result, Path)


class TestOpenFileConfig:
    """Test the open_file_config utility function."""

    def test_open_string_path_text_mode(self, sample_text_file):
        """Test opening a string path in text mode."""
        with open_file_config(str(sample_text_file), "r") as f:
            content = f.read()
            assert content == "Hello, World!\nThis is a test file.\n"

    def test_open_string_path_binary_mode(self, sample_binary_file):
        """Test opening a string path in binary mode."""
        with open_file_config(str(sample_binary_file), "rb") as f:
            content = f.read()
            assert content == b"\x00\x01\x02\x03\xff\xfe\xfd"

    def test_open_path_object(self, sample_text_file):
        """Test opening a Path object."""
        with open_file_config(sample_text_file, "r") as f:
            content = f.read()
            assert content == "Hello, World!\nThis is a test file.\n"

    def test_open_base_file_config(self, sample_text_file):
        """Test opening a BaseFileConfig instance."""
        mock_config = MockFileConfig(path=sample_text_file)
        with open_file_config(mock_config, "r") as f:
            content = f.read()
            assert content == "Hello, World!\nThis is a test file.\n"

    def test_open_default_binary_mode(self, sample_binary_file):
        """Test that default mode is binary."""
        with open_file_config(sample_binary_file) as f:
            content = f.read()
            assert content == b"\x00\x01\x02\x03\xff\xfe\xfd"

    def test_open_nonexistent_file_raises_error(self, nonexistent_file):
        """Test that opening a nonexistent file raises an error."""
        with pytest.raises(FileNotFoundError):
            with open_file_config(str(nonexistent_file)):
                pass


class TestAnyFileConfigTypeAlias:
    """Test the AnyFileConfig type alias."""

    def test_any_file_config_accepts_string(self, sample_text_file):
        """Test that AnyFileConfig type accepts string paths."""
        # This is more of a type checking test, but we can test runtime behavior
        config: AnyFileConfig = str(sample_text_file)
        result = resolve_file_config(config)
        assert result == sample_text_file

    def test_any_file_config_accepts_path(self, sample_text_file):
        """Test that AnyFileConfig type accepts Path objects."""
        config: AnyFileConfig = sample_text_file
        result = resolve_file_config(config)
        assert result == sample_text_file

    def test_any_file_config_accepts_base_file_config(self, sample_text_file):
        """Test that AnyFileConfig type accepts BaseFileConfig instances."""
        config: AnyFileConfig = MockFileConfig(path=sample_text_file)
        result = resolve_file_config(config)
        assert result == sample_text_file


class TestMockFileConfig:
    """Test our mock implementation to ensure it works correctly."""

    def test_mock_resolve(self, sample_text_file):
        """Test MockFileConfig resolve method."""
        mock_config = MockFileConfig(path=sample_text_file)
        assert mock_config.resolve() == sample_text_file

    def test_mock_open(self, sample_text_file):
        """Test MockFileConfig open method."""
        mock_config = MockFileConfig(path=sample_text_file)
        with mock_config.open("r") as f:
            content = f.read()
            assert content == "Hello, World!\nThis is a test file.\n"

    def test_mock_is_base_file_config_instance(self, sample_text_file):
        """Test that MockFileConfig is a proper BaseFileConfig instance."""
        mock_config = MockFileConfig(path=sample_text_file)
        assert isinstance(mock_config, BaseFileConfig)
