"""Integration tests for nshconfig-extra file configurations."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from nshconfig_extra.file import (
    AnyFileConfig,
    BaseFileConfig,
    CachedPathConfig,
    RemoteSSHFileConfig,
    open_file_config,
    resolve_file_config,
)
from nshconfig_extra.file.ssh import SSHConfig


class TestIntegration:
    """Integration tests for the file configuration system."""

    def test_resolve_file_config_with_different_types(self, sample_text_file):
        """Test resolve_file_config with all supported AnyFileConfig types."""
        # Test with string
        result1 = resolve_file_config(str(sample_text_file))
        assert result1 == sample_text_file

        # Test with Path
        result2 = resolve_file_config(sample_text_file)
        assert result2 == sample_text_file

        # Test with CachedPathConfig
        cached_config = CachedPathConfig(uri=str(sample_text_file))
        result3 = resolve_file_config(cached_config)
        assert result3.exists()

        # Test with RemoteSSHFileConfig (mocked)
        ssh_config = SSHConfig(hostname="example.com")

        # Mock the connect_host function instead of patching the instance
        with patch("nshconfig_extra.file.ssh.connect_host") as mock_connect_host:
            # Mock SSH connection
            mock_ssh_client = Mock()
            mock_sftp_client = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp_client
            mock_connect_host.return_value = (mock_ssh_client, [])

            # Mock file content and create a temporary file to represent downloaded file
            file_content = b"Hello from remote file!"
            mock_file = Mock()
            mock_file.read.return_value = file_content

            # Create context manager for SFTP file
            mock_sftp_file = Mock()
            mock_sftp_file.__enter__ = Mock(return_value=mock_file)
            mock_sftp_file.__exit__ = Mock(return_value=False)
            mock_sftp_client.open.return_value = mock_sftp_file

            remote_config = RemoteSSHFileConfig(
                ssh=ssh_config, remote_path="/remote/file.txt"
            )

            result4 = resolve_file_config(remote_config)
            assert isinstance(result4, Path)
            assert result4.exists()

    def test_open_file_config_with_different_types(self, sample_text_file):
        """Test open_file_config with all supported AnyFileConfig types."""
        expected_content = "Hello, World!\nThis is a test file.\n"

        # Test with string
        with open_file_config(str(sample_text_file), "r") as f:
            assert f.read() == expected_content

        # Test with Path
        with open_file_config(sample_text_file, "r") as f:
            assert f.read() == expected_content

        # Test with CachedPathConfig
        cached_config = CachedPathConfig(uri=str(sample_text_file))
        with open_file_config(cached_config, "r") as f:
            assert f.read() == expected_content

        # Test with RemoteSSHFileConfig (mocked)
        ssh_config = SSHConfig(hostname="example.com")

        with patch("nshconfig_extra.file.ssh.connect_host") as mock_connect_host:
            # Mock SSH connection
            mock_ssh_client = Mock()
            mock_sftp_client = Mock()
            mock_file = Mock()
            mock_file.read.return_value = expected_content

            mock_ssh_client.open_sftp.return_value = mock_sftp_client
            mock_sftp_client.open.return_value = mock_file
            mock_connect_host.return_value = (mock_ssh_client, [])

            remote_config = RemoteSSHFileConfig(
                ssh=ssh_config, remote_path="/remote/file.txt"
            )

            with open_file_config(remote_config, "r") as f:
                assert f.read() == expected_content

    @patch("nshconfig_extra.file.cached_path_.cached_path")
    def test_cached_path_with_remote_url(self, mock_cached_path, sample_text_file):
        """Test CachedPathConfig with a remote URL (mocked)."""
        mock_cached_path.return_value = sample_text_file

        config = CachedPathConfig(uri="https://example.com/remote-file.txt")

        # Test resolve
        result = resolve_file_config(config)
        assert result == sample_text_file

        # Test open
        with open_file_config(config, "r") as f:
            content = f.read()
            assert content == "Hello, World!\nThis is a test file.\n"

        # Verify cached_path was called correctly
        mock_cached_path.assert_called_with(
            "https://example.com/remote-file.txt",
            cache_dir=None,
            extract_archive=False,
            force_extract=False,
            quiet=False,
        )

    def test_ssh_config_uri_to_remote_file_config(self):
        """Test creating RemoteSSHFileConfig from SSH URI."""
        uri = "ssh://user@example.com:2222/path/to/remote/file.txt"
        config = RemoteSSHFileConfig.from_uri(uri)

        # Verify SSH configuration
        assert config.ssh.hostname == "example.com"
        assert config.ssh.port == 2222
        assert config.ssh.username == "user"
        assert config.ssh.password is None
        # remote_path is stored as Path object, so compare as Path
        assert config.remote_path == Path("/path/to/remote/file.txt")

        # Verify it's a valid AnyFileConfig
        assert isinstance(config, BaseFileConfig)

    def test_multiple_file_configs_in_list(self, sample_text_file, temp_dir):
        """Test working with multiple file configurations."""
        # Create additional test files
        file1 = temp_dir / "file1.txt"
        file1.write_text("Content of file 1", encoding="utf-8")
        file2 = temp_dir / "file2.txt"
        file2.write_text("Content of file 2", encoding="utf-8")

        # Define different config types
        configs: list[AnyFileConfig] = [
            str(file1),  # String path
            file2,  # Path object
            CachedPathConfig(uri=str(sample_text_file)),  # Cached config
        ]

        # Test that all can be resolved
        resolved_paths = [resolve_file_config(config) for config in configs]
        assert all(path.exists() for path in resolved_paths)

        # Test that all can be opened
        contents = []
        for config in configs:
            with open_file_config(config, "r") as f:
                contents.append(f.read())

        assert contents[0] == "Content of file 1"
        assert contents[1] == "Content of file 2"
        assert contents[2] == "Hello, World!\nThis is a test file.\n"

    @patch("nshconfig_extra.file.cached_path_.cached_path")
    def test_cached_path_with_archive_extraction(self, mock_cached_path, temp_dir):
        """Test CachedPathConfig with archive extraction enabled."""
        extracted_dir = temp_dir / "extracted"
        extracted_dir.mkdir()
        extracted_file = extracted_dir / "extracted_file.txt"
        extracted_file.write_text("Extracted content", encoding="utf-8")

        mock_cached_path.return_value = extracted_file

        config = CachedPathConfig(
            uri="https://example.com/archive.tar.gz",
            extract_archive=True,
            force_extract=True,
        )

        result = resolve_file_config(config)
        assert result == extracted_file

        with open_file_config(config, "r") as f:
            assert f.read() == "Extracted content"

        mock_cached_path.assert_called_with(
            "https://example.com/archive.tar.gz",
            cache_dir=None,
            extract_archive=True,
            force_extract=True,
            quiet=False,
        )

    def test_error_handling_consistency(self, temp_dir):
        """Test that error handling is consistent across different config types."""
        nonexistent_path = temp_dir / "nonexistent.txt"

        # String path
        with pytest.raises(FileNotFoundError):
            with open_file_config(str(nonexistent_path), "r"):
                pass

        # Path object
        with pytest.raises(FileNotFoundError):
            with open_file_config(nonexistent_path, "r"):
                pass

        # CachedPathConfig with nonexistent local file
        cached_config = CachedPathConfig(uri=str(nonexistent_path))
        with pytest.raises(FileNotFoundError):
            with open_file_config(cached_config, "r"):
                pass

    def test_binary_vs_text_mode_consistency(self, sample_binary_file):
        """Test that binary and text modes work consistently across config types."""
        binary_content = b"\x00\x01\x02\x03\xff\xfe\xfd"

        configs: list[AnyFileConfig] = [
            str(sample_binary_file),
            sample_binary_file,
            CachedPathConfig(uri=str(sample_binary_file)),
        ]

        # Test binary mode
        for config in configs:
            with open_file_config(config, "rb") as f:
                content = f.read()
                assert content == binary_content

        # Test default mode (should be binary)
        for config in configs:
            with open_file_config(config) as f:
                content = f.read()
                assert content == binary_content

    @patch("nshconfig_extra.file.ssh.connect_host")
    def test_ssh_config_integration_with_utilities(
        self, mock_connect_host, sample_text_file
    ):
        """Test that SSH configurations work properly with utility functions."""
        # Mock SSH connection
        mock_ssh_client = Mock()
        mock_sftp_client = Mock()
        mock_file = Mock()

        mock_ssh_client.open_sftp.return_value = mock_sftp_client
        mock_sftp_client.open.return_value = mock_file
        mock_connect_host.return_value = (mock_ssh_client, [])

        # Create SSH config
        ssh_config = SSHConfig(hostname="example.com", username="testuser")
        remote_config = RemoteSSHFileConfig(
            ssh=ssh_config, remote_path="/remote/file.txt"
        )

        # Test with open utility
        mock_file.read.return_value = "Remote file content"
        with open_file_config(remote_config, "r") as f:
            content = f.read()
            assert content == "Remote file content"

    def test_config_type_validation(self):
        """Test that invalid config types raise appropriate errors."""
        # This should raise an AssertionError due to assert_never
        invalid_config = 123  # type: ignore

        # The match statement in utility functions should handle this with assert_never
        with pytest.raises(AssertionError, match="Expected code to be unreachable"):
            resolve_file_config(invalid_config)  # type: ignore

        with pytest.raises(AssertionError, match="Expected code to be unreachable"):
            with open_file_config(invalid_config):  # type: ignore
                pass
