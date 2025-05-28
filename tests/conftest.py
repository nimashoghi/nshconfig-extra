"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file for testing."""
    file_path = temp_dir / "sample.txt"
    file_path.write_text("Hello, World!\nThis is a test file.\n", encoding="utf-8")
    return file_path


@pytest.fixture
def sample_binary_file(temp_dir):
    """Create a sample binary file for testing."""
    file_path = temp_dir / "sample.bin"
    file_path.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")
    return file_path


@pytest.fixture
def nonexistent_file(temp_dir):
    """Return a path to a nonexistent file."""
    return temp_dir / "nonexistent.txt"


@pytest.fixture
def ssh_config_content():
    """Sample SSH config content for testing."""
    return """
Host test-host
    HostName example.com
    Port 2222
    User testuser
    IdentityFile ~/.ssh/test_key

Host proxy-host
    HostName proxy.example.com
    Port 22
    User proxyuser

Host jump-host
    HostName target.example.com
    Port 22
    User targetuser
    ProxyJump proxy-host
"""


@pytest.fixture
def mock_ssh_config_file(temp_dir, ssh_config_content):
    """Create a mock SSH config file."""
    config_file = temp_dir / "ssh_config"
    config_file.write_text(ssh_config_content.strip(), encoding="utf-8")
    return config_file
