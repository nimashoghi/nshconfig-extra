"""Tests for the SSH file configuration functionality."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from nshconfig_extra.file.ssh import RemoteSSHFileConfig, SSHConfig


class TestSSHConfig:
    """Test the SSHConfig class."""

    def test_init_minimal(self):
        """Test initializing SSHConfig with minimal parameters."""
        config = SSHConfig(hostname="example.com")
        assert config.hostname == "example.com"
        assert config.port == 22
        assert config.username is None
        assert config.password is None
        assert config.identity_files is None
        assert config.proxy_jump is None

    def test_init_complete(self):
        """Test initializing SSHConfig with all parameters."""
        proxy = SSHConfig(hostname="proxy.example.com", username="proxyuser")
        identity_files = [Path("~/.ssh/id_rsa"), Path("~/.ssh/id_ed25519")]

        config = SSHConfig(
            hostname="target.example.com",
            port=2222,
            username="testuser",
            password="testpass",
            identity_files=identity_files,
            proxy_jump=proxy,
        )

        assert config.hostname == "target.example.com"
        assert config.port == 2222
        assert config.username == "testuser"
        assert config.password == "testpass"
        assert config.identity_files == identity_files
        assert config.proxy_jump == proxy

    def test_init_single_identity_file(self):
        """Test initializing SSHConfig with a single identity file."""
        identity_file = Path("~/.ssh/id_rsa")
        config = SSHConfig(
            hostname="example.com",
            identity_files=identity_file,
        )
        assert config.identity_files == identity_file

    def test_from_uri_minimal(self):
        """Test creating SSHConfig from minimal URI."""
        ssh_config, remote_path = SSHConfig.from_uri("ssh://example.com/path/to/file")

        assert ssh_config.hostname == "example.com"
        assert ssh_config.port == 22
        assert ssh_config.username is None
        assert ssh_config.password is None
        assert remote_path == Path("/path/to/file")

    def test_from_uri_complete(self):
        """Test creating SSHConfig from complete URI."""
        uri = "ssh://user:pass@example.com:2222/path/to/file"
        ssh_config, remote_path = SSHConfig.from_uri(uri)

        assert ssh_config.hostname == "example.com"
        assert ssh_config.port == 2222
        assert ssh_config.username == "user"
        assert ssh_config.password == "pass"
        assert remote_path == Path("/path/to/file")

    def test_from_uri_scp_scheme(self):
        """Test creating SSHConfig from SCP URI."""
        uri = "scp://user@example.com/path/to/file"
        ssh_config, remote_path = SSHConfig.from_uri(uri)

        assert ssh_config.hostname == "example.com"
        assert ssh_config.port == 22
        assert ssh_config.username == "user"
        assert ssh_config.password is None
        assert remote_path == Path("/path/to/file")

    def test_from_uri_invalid_scheme(self):
        """Test that invalid URI scheme raises ValueError."""
        with pytest.raises(ValueError, match="URI scheme must be 'ssh' or 'scp'"):
            SSHConfig.from_uri("http://example.com/file")

    def test_from_uri_missing_hostname(self):
        """Test that missing hostname raises ValueError."""
        with pytest.raises(ValueError, match="URI must contain a hostname"):
            SSHConfig.from_uri("ssh:///path/to/file")

    def test_from_uri_missing_path(self):
        """Test that missing path raises ValueError."""
        with pytest.raises(ValueError, match="URI must contain a path"):
            SSHConfig.from_uri("ssh://example.com")

    @patch("importlib.util.find_spec")
    def test_from_ssh_config_missing_paramiko(self, mock_find_spec):
        """Test that missing paramiko raises ImportError."""
        mock_find_spec.return_value = None

        with pytest.raises(ImportError, match="paramiko is not installed"):
            SSHConfig.from_ssh_config("test-host")

    @patch("importlib.util.find_spec")
    def test_from_ssh_config_file_not_found(self, mock_find_spec, temp_dir):
        """Test that missing SSH config file raises FileNotFoundError."""
        mock_find_spec.return_value = Mock()  # Pretend paramiko is available

        nonexistent_config = temp_dir / "nonexistent_ssh_config"
        with pytest.raises(FileNotFoundError, match="SSH config file not found"):
            SSHConfig.from_ssh_config("test-host", nonexistent_config)

    @patch("importlib.util.find_spec")
    @patch("paramiko.config.SSHConfig")
    def test_from_ssh_config_success(
        self, mock_ssh_config_class, mock_find_spec, mock_ssh_config_file
    ):
        """Test successful SSH config parsing."""
        mock_find_spec.return_value = Mock()  # Pretend paramiko is available

        # Mock the paramiko SSHConfig class
        mock_ssh_config_parser = Mock()
        mock_ssh_config_parser.lookup.return_value = {
            "hostname": "example.com",
            "port": "2222",
            "user": "testuser",
            "identityfile": ["~/.ssh/test_key"],
        }
        mock_ssh_config_class.return_value = mock_ssh_config_parser

        with patch("builtins.open", mock_open(read_data="mock config")):
            result = SSHConfig.from_ssh_config("test-host", mock_ssh_config_file)

            assert isinstance(result, SSHConfig)
            assert result.hostname == "example.com"
            assert result.port == 2222
            assert result.username == "testuser"
            assert result.identity_files == [Path("~/.ssh/test_key").expanduser()]

    @patch("importlib.util.find_spec")
    @patch("paramiko.config.SSHConfig")
    def test_from_ssh_config_host_not_found(
        self, mock_ssh_config_class, mock_find_spec, mock_ssh_config_file
    ):
        """Test that missing host in SSH config raises ValueError."""
        mock_find_spec.return_value = Mock()  # Pretend paramiko is available

        # Mock the paramiko SSHConfig class
        mock_ssh_config_parser = Mock()
        mock_ssh_config_parser.lookup.return_value = {"hostname": None}
        mock_ssh_config_class.return_value = mock_ssh_config_parser

        with patch("builtins.open", mock_open(read_data="mock config")):
            with pytest.raises(ValueError, match="Host 'nonexistent-host' not found"):
                SSHConfig.from_ssh_config("nonexistent-host", mock_ssh_config_file)


class TestRemoteSSHFileConfig:
    """Test the RemoteSSHFileConfig class."""

    def test_init(self):
        """Test initializing RemoteSSHFileConfig."""
        ssh_config = SSHConfig(hostname="example.com", username="testuser")
        config = RemoteSSHFileConfig(ssh=ssh_config, remote_path="/path/to/file.txt")

        assert config.ssh == ssh_config
        assert config.remote_path == "/path/to/file.txt"

    @patch("nshconfig_extra.file.ssh.connect_host")
    def test_resolve_creates_temp_file(self, mock_connect_host, temp_dir):
        """Test that resolve method creates a temporary file."""
        # Mock SSH connection
        mock_ssh_client = Mock()
        mock_sftp_client = Mock()
        mock_ssh_client.open_sftp.return_value = mock_sftp_client
        mock_connect_host.return_value = (mock_ssh_client, [])

        # Mock file content
        file_content = b"Hello from remote file!"

        # Mock the getfo method that downloads the file
        def mock_getfo(remote_path, file_obj):
            # Simulate writing content to the temporary file
            file_obj.write(file_content)
            file_obj.flush()

        mock_sftp_client.getfo.side_effect = mock_getfo

        ssh_config = SSHConfig(hostname="example.com")
        config = RemoteSSHFileConfig(ssh=ssh_config, remote_path="/remote/file.txt")

        result = config.resolve()

        # Should return a valid path
        assert isinstance(result, Path)
        assert result.exists()

        # Should contain the expected content
        assert result.read_bytes() == file_content

        # Verify SFTP calls
        mock_connect_host.assert_called_once_with(ssh_config)
        mock_ssh_client.open_sftp.assert_called_once()
        mock_sftp_client.getfo.assert_called_once()
        mock_sftp_client.close.assert_called_once()

    @patch("nshconfig_extra.file.ssh.connect_host")
    def test_open_direct_sftp_access(self, mock_connect_host):
        """Test that open method provides direct SFTP access."""
        # Mock SSH connection
        mock_ssh_client = Mock()
        mock_sftp_client = Mock()
        mock_file = Mock()

        mock_ssh_client.open_sftp.return_value = mock_sftp_client
        mock_sftp_client.open.return_value = mock_file
        mock_connect_host.return_value = (mock_ssh_client, [])

        ssh_config = SSHConfig(hostname="example.com")
        config = RemoteSSHFileConfig(ssh=ssh_config, remote_path="/remote/file.txt")

        with config.open("rb") as f:
            assert f == mock_file

        # Verify calls
        mock_connect_host.assert_called_once_with(ssh_config)
        mock_ssh_client.open_sftp.assert_called_once()
        mock_sftp_client.open.assert_called_once_with("/remote/file.txt", "rb")

    @patch("nshconfig_extra.file.ssh.connect_host")
    def test_open_with_text_mode(self, mock_connect_host):
        """Test opening file in text mode."""
        # Mock SSH connection
        mock_ssh_client = Mock()
        mock_sftp_client = Mock()
        mock_file = Mock()

        mock_ssh_client.open_sftp.return_value = mock_sftp_client
        mock_sftp_client.open.return_value = mock_file
        mock_connect_host.return_value = (mock_ssh_client, [])

        ssh_config = SSHConfig(hostname="example.com")
        config = RemoteSSHFileConfig(ssh=ssh_config, remote_path="/remote/file.txt")

        with config.open("r") as f:
            assert f == mock_file

        mock_sftp_client.open.assert_called_once_with("/remote/file.txt", "r")

    def test_from_uri(self):
        """Test creating RemoteSSHFileConfig from URI."""
        uri = "ssh://user:pass@example.com:2222/path/to/file"
        config = RemoteSSHFileConfig.from_uri(uri)

        assert config.ssh.hostname == "example.com"
        assert config.ssh.port == 2222
        assert config.ssh.username == "user"
        assert config.ssh.password == "pass"
        # remote_path is stored as Path object
        assert config.remote_path == Path("/path/to/file")

    @patch("nshconfig_extra.file.ssh.SSHConfig.from_ssh_config")
    def test_from_ssh_config(self, mock_from_ssh_config):
        """Test creating RemoteSSHFileConfig from SSH config."""
        mock_ssh_config = SSHConfig(hostname="example.com", username="testuser")
        mock_from_ssh_config.return_value = mock_ssh_config

        config = RemoteSSHFileConfig.from_ssh_config(
            host="test-host", remote_path="/remote/file.txt"
        )

        assert config.ssh == mock_ssh_config
        assert config.remote_path == "/remote/file.txt"
        mock_from_ssh_config.assert_called_once_with("test-host", None)

    @patch("nshconfig_extra.file.ssh.SSHConfig.from_ssh_config")
    def test_from_ssh_config_with_custom_config_path(
        self, mock_from_ssh_config, temp_dir
    ):
        """Test creating RemoteSSHFileConfig with custom SSH config path."""
        mock_ssh_config = SSHConfig(hostname="example.com")
        mock_from_ssh_config.return_value = mock_ssh_config
        custom_config_path = temp_dir / "custom_ssh_config"

        config = RemoteSSHFileConfig.from_ssh_config(
            host="test-host",
            remote_path="/remote/file.txt",
            config_path=custom_config_path,
        )

        mock_from_ssh_config.assert_called_once_with("test-host", custom_config_path)

    def test_from_direct_connection(self):
        """Test creating RemoteSSHFileConfig with direct connection parameters."""
        config = RemoteSSHFileConfig.from_direct_connection(
            hostname="example.com",
            remote_path="/remote/file.txt",
            port=2222,
            username="testuser",
            password="testpass",
        )

        assert config.ssh.hostname == "example.com"
        assert config.ssh.port == 2222
        assert config.ssh.username == "testuser"
        assert config.ssh.password == "testpass"
        assert config.remote_path == "/remote/file.txt"

    def test_from_direct_connection_with_identity_files(self):
        """Test creating RemoteSSHFileConfig with identity files."""
        identity_files = [Path("~/.ssh/id_rsa"), Path("~/.ssh/id_ed25519")]
        config = RemoteSSHFileConfig.from_direct_connection(
            hostname="example.com",
            remote_path="/remote/file.txt",
            identity_files=identity_files,
        )

        assert config.ssh.identity_files == identity_files

    def test_from_direct_connection_with_proxy_jump(self):
        """Test creating RemoteSSHFileConfig with proxy jump."""
        proxy_config = SSHConfig(hostname="proxy.example.com")
        config = RemoteSSHFileConfig.from_direct_connection(
            hostname="example.com",
            remote_path="/remote/file.txt",
            proxy_jump=proxy_config,
        )

        assert config.ssh.proxy_jump == proxy_config

    def test_is_base_file_config(self):
        """Test that RemoteSSHFileConfig is a BaseFileConfig instance."""
        from nshconfig_extra.file import BaseFileConfig

        ssh_config = SSHConfig(hostname="example.com")
        config = RemoteSSHFileConfig(ssh=ssh_config, remote_path="/remote/file.txt")
        assert isinstance(config, BaseFileConfig)

    def test_remote_path_str_conversion(self):
        """Test that remote_path accepts both string and Path objects."""
        ssh_config = SSHConfig(hostname="example.com")

        # Test with string
        config1 = RemoteSSHFileConfig(ssh=ssh_config, remote_path="/remote/file.txt")
        assert config1.remote_path == "/remote/file.txt"

        # Test with Path
        path_obj = Path("/remote/file.txt")
        config2 = RemoteSSHFileConfig(ssh=ssh_config, remote_path=path_obj)
        assert config2.remote_path == path_obj
