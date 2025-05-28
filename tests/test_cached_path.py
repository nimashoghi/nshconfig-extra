"""Tests for the CachedPathConfig functionality."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from nshconfig_extra.file import CachedPathConfig


class TestCachedPathConfig:
    """Test the CachedPathConfig class."""

    def test_init_with_string_uri(self):
        """Test initializing CachedPathConfig with a string URI."""
        config = CachedPathConfig(uri="https://example.com/file.txt")
        assert config.uri == "https://example.com/file.txt"
        assert config.cache_dir is None
        assert config.extract_archive is False
        assert config.force_extract is False
        assert config.quiet is False

    def test_init_with_path_uri(self, sample_text_file):
        """Test initializing CachedPathConfig with a Path URI."""
        config = CachedPathConfig(uri=sample_text_file)
        assert config.uri == sample_text_file
        assert config.cache_dir is None
        assert config.extract_archive is False
        assert config.force_extract is False
        assert config.quiet is False

    def test_init_with_all_options(self, temp_dir):
        """Test initializing CachedPathConfig with all options set."""
        cache_dir = temp_dir / "cache"
        config = CachedPathConfig(
            uri="https://example.com/archive.zip",
            cache_dir=cache_dir,
            extract_archive=True,
            force_extract=True,
            quiet=True,
        )
        assert config.uri == "https://example.com/archive.zip"
        assert config.cache_dir == cache_dir
        assert config.extract_archive is True
        assert config.force_extract is True
        assert config.quiet is True

    @patch("nshconfig_extra.file.cached_path_.cached_path")
    def test_resolve_calls_cached_path(self, mock_cached_path, temp_dir):
        """Test that resolve method calls cached_path with correct arguments."""
        cached_file = temp_dir / "cached_file.txt"
        mock_cached_path.return_value = cached_file

        config = CachedPathConfig(uri="https://example.com/file.txt")
        result = config.resolve()

        mock_cached_path.assert_called_once_with(
            "https://example.com/file.txt",
            cache_dir=None,
            extract_archive=False,
            force_extract=False,
            quiet=False,
        )
        assert result == cached_file

    @patch("nshconfig_extra.file.cached_path_.cached_path")
    def test_resolve_with_custom_options(self, mock_cached_path, temp_dir):
        """Test resolve method with custom options."""
        cached_file = temp_dir / "cached_file.txt"
        mock_cached_path.return_value = cached_file
        cache_dir = temp_dir / "cache"

        config = CachedPathConfig(
            uri="https://example.com/archive.tar.gz",
            cache_dir=cache_dir,
            extract_archive=True,
            force_extract=True,
            quiet=True,
        )
        result = config.resolve()

        mock_cached_path.assert_called_once_with(
            "https://example.com/archive.tar.gz",
            cache_dir=cache_dir,
            extract_archive=True,
            force_extract=True,
            quiet=True,
        )
        assert result == cached_file

    @patch("nshconfig_extra.file.cached_path_.cached_path")
    def test_open_resolves_and_opens_file(self, mock_cached_path, sample_text_file):
        """Test that open method resolves the file and opens it."""
        mock_cached_path.return_value = sample_text_file

        config = CachedPathConfig(uri="https://example.com/file.txt")

        with config.open("r") as f:
            content = f.read()
            assert content == "Hello, World!\nThis is a test file.\n"

        mock_cached_path.assert_called_once()

    @patch("nshconfig_extra.file.cached_path_.cached_path")
    def test_open_binary_mode(self, mock_cached_path, sample_binary_file):
        """Test opening file in binary mode."""
        mock_cached_path.return_value = sample_binary_file

        config = CachedPathConfig(uri="https://example.com/file.bin")

        with config.open("rb") as f:
            content = f.read()
            assert content == b"\x00\x01\x02\x03\xff\xfe\xfd"

    @patch("nshconfig_extra.file.cached_path_.cached_path")
    def test_open_default_mode(self, mock_cached_path, sample_binary_file):
        """Test that default open mode is binary."""
        mock_cached_path.return_value = sample_binary_file

        config = CachedPathConfig(uri="https://example.com/file.bin")

        with config.open() as f:
            content = f.read()
            assert content == b"\x00\x01\x02\x03\xff\xfe\xfd"

    def test_is_base_file_config(self):
        """Test that CachedPathConfig is a BaseFileConfig instance."""
        from nshconfig_extra.file import BaseFileConfig

        config = CachedPathConfig(uri="https://example.com/file.txt")
        assert isinstance(config, BaseFileConfig)

    def test_local_file_path(self, sample_text_file):
        """Test using CachedPathConfig with a local file path."""
        config = CachedPathConfig(uri=str(sample_text_file))

        # This should work without any network access
        result = config.resolve()
        assert result.exists()

        with config.open("r") as f:
            content = f.read()
            assert content == "Hello, World!\nThis is a test file.\n"

    @patch("nshconfig_extra.file.cached_path_.cached_path")
    def test_cache_dir_path_object(self, mock_cached_path, temp_dir):
        """Test using Path object for cache_dir."""
        cached_file = temp_dir / "cached_file.txt"
        mock_cached_path.return_value = cached_file
        cache_dir = temp_dir / "custom_cache"

        config = CachedPathConfig(
            uri="https://example.com/file.txt",
            cache_dir=cache_dir,
        )
        config.resolve()

        mock_cached_path.assert_called_once_with(
            "https://example.com/file.txt",
            cache_dir=cache_dir,
            extract_archive=False,
            force_extract=False,
            quiet=False,
        )

    def test_config_serialization(self):
        """Test that CachedPathConfig can be serialized/deserialized properly."""
        # Since it inherits from nshconfig.Config, it should support serialization
        config = CachedPathConfig(
            uri="https://example.com/file.txt",
            extract_archive=True,
            quiet=True,
        )

        # Test that the config has the expected attributes
        assert hasattr(config, "uri")
        assert hasattr(config, "extract_archive")
        assert hasattr(config, "quiet")
        assert hasattr(config, "cache_dir")
        assert hasattr(config, "force_extract")

    @patch("nshconfig_extra.file.cached_path_.cached_path")
    def test_resolve_multiple_calls_cache_behavior(self, mock_cached_path, temp_dir):
        """Test that multiple resolve calls work as expected."""
        cached_file = temp_dir / "cached_file.txt"
        mock_cached_path.return_value = cached_file

        config = CachedPathConfig(uri="https://example.com/file.txt")

        # Call resolve multiple times
        result1 = config.resolve()
        result2 = config.resolve()

        # Should be called twice (no caching at this level)
        assert mock_cached_path.call_count == 2
        assert result1 == cached_file
        assert result2 == cached_file
