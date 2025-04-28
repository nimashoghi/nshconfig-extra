from __future__ import annotations

import contextlib
import importlib.util
import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import nshconfig as C
from typing_extensions import Required, Self, TypedDict, override

from .base import BaseFileConfig

if TYPE_CHECKING:
    import paramiko


log = logging.getLogger(__name__)


class SSHConfig(C.Config):
    """Configuration for SSH connections.

    Provides all necessary parameters for establishing SSH connections,
    with support for authentication via password or key files.
    """

    hostname: str
    """The target host to connect to."""

    port: int = 22
    """SSH port number (default: 22)."""

    username: str | None = None
    """Username for authentication (optional)."""

    password: str | None = None
    """Password for authentication (optional)."""

    identity_files: Path | list[Path] | None = None
    """SSH private key file paths (optional). Can be a single path or a list of paths."""

    proxy_jump: SSHConfig | None = None
    """Proxy jump configuration (optional). For SSH connections through jump hosts."""

    @classmethod
    def from_uri(cls, uri: str) -> tuple[Self, Path]:
        """Create an SSHConfig instance from an SSH/SCP URI.

        Parses a URI in the format:
        ssh://[username[:password]@]hostname[:port]/path/to/file
        or
        scp://[username[:password]@]hostname[:port]/path/to/file

        Args:
            uri: The SSH or SCP URI to parse.

        Returns:
            A tuple containing:
              - An SSHConfig instance configured with connection details
              - A Path object representing the remote file path

        Raises:
            ValueError: If the URI scheme is not 'ssh' or 'scp', or if required components are missing.
        """
        parsed = urlparse(uri)

        if parsed.scheme not in ("ssh", "scp"):
            raise ValueError(
                f"URI scheme must be 'ssh' or 'scp', got '{parsed.scheme}'"
            )

        if not (hostname := parsed.hostname):
            raise ValueError("URI must contain a hostname")

        if not (remote_path := parsed.path):
            raise ValueError("URI must contain a path")

        # Parse connection parameters
        port = parsed.port or 22
        username = parsed.username
        password = parsed.password

        # Create and return the SSH config
        ssh = cls(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
        )

        return ssh, Path(remote_path)

    @classmethod
    def from_ssh_config(cls, host: str, config_path: Path | None = None) -> Self:
        """Create an SSHConfig instance from an SSH config file entry.

        Loads connection parameters from the SSH config file (~/.ssh/config by default)
        for the specified host entry.

        Args:
            host: The host entry name in the SSH config file.
            config_path: Optional custom path to the SSH config file.
                         If None, uses ~/.ssh/config.

        Returns:
            An SSHConfig instance configured with parameters from the SSH config file.

        Raises:
            FileNotFoundError: If the SSH config file doesn't exist.
            ValueError: If the specified host entry is not found in the config file.
            ImportError: If paramiko is not installed.
        """
        # Ensure paramiko is installed
        if not importlib.util.find_spec("paramiko"):
            raise ImportError(
                "paramiko is not installed. Please install it to use SSH features. "
                "This can be done by either running `pip install paramiko` or using "
                "the appropriate extra when installing nshconfig."
            )

        from paramiko.config import SSHConfig

        # Determine the SSH config file path
        if config_path is None:
            config_path = Path.home() / ".ssh" / "config"

        if not config_path.exists():
            raise FileNotFoundError(f"SSH config file not found at {config_path}")

        # Load the SSH config file
        ssh_config_parser = SSHConfig()
        with open(config_path) as f:
            ssh_config_parser.parse(f)

        # Look up the host entry
        host_config = ssh_config_parser.lookup(host)

        # Check if the host exists in the config
        if host_config.get("hostname") is None:
            raise ValueError(f"Host '{host}' not found in SSH config")

        # Extract connection parameters
        hostname = host_config["hostname"]
        port = int(host_config.get("port", 22))
        username = host_config.get("user")

        # Handle identity files
        parsed_identity_files = None
        if identity_files := host_config.get("identityfile"):
            # Convert identity files to Path objects and expand home directory
            if isinstance(identity_files, list):
                parsed_identity_files = [Path(p).expanduser() for p in identity_files]
            else:
                parsed_identity_files = Path(identity_files).expanduser()

        # Handle proxy jump if present
        proxy_jump = None
        if proxy_jump_host := host_config.get("proxyjump"):
            # For simplicity, only handle the first proxy jump host if multiple are specified
            if "," in proxy_jump_host:
                proxy_jump_host = proxy_jump_host.split(",")[0]

            proxy_jump = cls.from_ssh_config(proxy_jump_host, config_path)

        # Create and return the SSH config
        return cls(
            hostname=hostname,
            port=port,
            username=username,
            identity_files=parsed_identity_files,
            proxy_jump=proxy_jump,
        )


class ConnectHostConfig(TypedDict, total=False):
    hostname: Required[str]
    """The target host to connect to."""

    port: int
    """SSH port number (default: 22)."""

    username: str | None
    """Username for authentication (optional)."""

    password: str | None
    """Password for authentication (optional)."""

    identityfile: str | list[str] | None
    """SSH private key file path(s) (optional)."""


def _create_direct_connection(
    config: SSHConfig, sock: Any | None = None
) -> paramiko.SSHClient:
    """Create a direct SSH connection to a host.

    Args:
        config: SSH configuration for the host.
        sock: Optional socket for tunneling.

    Returns:
        A connected SSHClient.

    Raises:
        ValueError: If no valid authentication method is available.
    """
    import paramiko

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Prepare connection parameters
    connect_params: dict[str, Any] = {
        "hostname": config.hostname,
        "port": config.port,
    }

    # Add username if provided
    if config.username:
        connect_params["username"] = config.username

    # Handle authentication
    auth_methods = []

    if config.password:
        connect_params["password"] = config.password
        auth_methods.append("password")

    if config.identity_files:
        identity_files = (
            [config.identity_files]
            if isinstance(config.identity_files, Path)
            else config.identity_files
        )

        for identity_file in identity_files:
            try:
                pkey = paramiko.RSAKey.from_private_key_file(str(identity_file))
                connect_params["pkey"] = pkey
                auth_methods.append("key")
                break
            except (paramiko.SSHException, FileNotFoundError) as e:
                log.debug(f"Failed to load key from {identity_file}: {e}")
                continue

    # If no explicit auth methods, we'll try default keys
    if not auth_methods:
        log.debug(
            "No explicit authentication methods provided, using default mechanisms"
        )

    # Add socket if provided
    if sock is not None:
        connect_params["sock"] = sock

    # Connect and return
    try:
        client.connect(**connect_params)
        log.debug(
            f"Connected to {config.hostname}:{config.port} using {', '.join(auth_methods) if auth_methods else 'default'} authentication"
        )
        return client
    except Exception as e:
        log.error(f"Failed to connect to {config.hostname}:{config.port}: {e}")
        raise


def _connect_through_jump_chain(
    config: SSHConfig,
) -> tuple[paramiko.SSHClient, list[paramiko.SSHClient]]:
    """Connect to a host through a chain of jump hosts.

    Args:
        config: The target host configuration with proxy_jump chain.

    Returns:
        Tuple of (target client, list of jump clients).

    Raises:
        ValueError: If no jump hosts are present in the chain.
        RuntimeError: If transport cannot be established with a jump host.
    """
    # Build the complete jump chain
    jump_chain = []
    current = config.proxy_jump

    while current:
        jump_chain.append(current)
        current = current.proxy_jump

    # Sanity check - we should have at least one jump host
    if not jump_chain:
        raise ValueError("No jump hosts in proxy_jump chain")

    # Connect to jump hosts in sequence
    jump_clients: list[paramiko.SSHClient] = []
    current_client = _create_direct_connection(jump_chain[0])
    jump_clients.append(current_client)

    # Connect through each jump host to the next
    for i in range(1, len(jump_chain)):
        next_host = jump_chain[i]

        # Create tunnel through current jump host
        transport = current_client.get_transport()
        if not transport:
            raise RuntimeError("Failed to get transport from jump host connection")

        dest_addr = (next_host.hostname, next_host.port)
        src_addr = ("", 0)  # Let the OS assign a port

        channel = transport.open_channel("direct-tcpip", dest_addr, src_addr)

        # Connect to the next jump host
        next_client = _create_direct_connection(next_host, sock=channel)
        jump_clients.append(next_client)
        current_client = next_client

    # Finally, connect to the target host
    transport = current_client.get_transport()
    if not transport:
        raise RuntimeError("Failed to get transport from final jump host connection")

    dest_addr = (config.hostname, config.port)
    src_addr = ("", 0)

    channel = transport.open_channel("direct-tcpip", dest_addr, src_addr)

    # Create the target connection
    target_client = _create_direct_connection(
        SSHConfig(
            hostname=config.hostname,
            port=config.port,
            username=config.username,
            password=config.password,
            identity_files=config.identity_files,
        ),
        sock=channel,
    )

    return target_client, jump_clients


def connect_host(
    config: SSHConfig, sock: Any | None = None
) -> tuple[paramiko.SSHClient, list[paramiko.SSHClient]]:
    """Connect to an SSH host using the provided configuration.

    Establishes an SSH connection based on the SSHConfig, handling authentication
    and optionally connecting through jump hosts. Returns both the final client
    and any intermediate jump host clients.

    Args:
        config: SSHConfig with host details (hostname, port, username, etc.).
        sock: Optional socket-like object for jump connections.

    Returns:
        A tuple containing:
          - The SSH client connected to the target host
          - A list of intermediate jump host clients (empty for direct connections)

    Raises:
        ImportError: If paramiko is not installed.
        ValueError: If no valid authentication method is found.
        paramiko.SSHException: If the connection fails.
    """
    # Ensure paramiko is installed
    if not importlib.util.find_spec("paramiko"):
        raise ImportError(
            "paramiko is not installed. Please install it to use SSH features. "
            "This can be done by either running `pip install paramiko` or using "
            "the appropriate extra when installing nshconfig."
        )

    # Handle jump host chain if present
    if config.proxy_jump:
        return _connect_through_jump_chain(config)

    # Direct connection
    client = _create_direct_connection(config, sock)
    return client, []


class RemoteSSHFileConfig(BaseFileConfig):
    """Configuration for accessing a remote file over SSH.

    Provides functionality to download or directly access files on remote servers
    via SSH, with support for authentication and proxy jumps.
    """

    ssh: SSHConfig
    """SSH configuration for connecting to the remote server."""

    remote_path: Path | str
    """Path to the file on the remote server."""

    @override
    def resolve(self) -> Path:
        """Download the remote file to a local temporary file.

        This method incurs the overhead of copying the file locally.

        Returns:
            Path to the downloaded temporary file.

        Raises:
            ImportError: If paramiko is not installed.
            paramiko.SSHException: If the SSH connection fails.
            IOError: If the file transfer fails.
        """
        log.info(f"Downloading remote file from {self.ssh.hostname}:{self.remote_path}")

        # Connect to the SSH server
        ssh_client, jump_clients = connect_host(self.ssh)

        try:
            # Open SFTP connection
            sftp = ssh_client.open_sftp()

            # Create a temporary file
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            tmp_path = Path(tmp_file.name)

            try:
                # Download the file
                sftp.getfo(str(self.remote_path), tmp_file)
                tmp_file.close()
                return tmp_path
            except Exception as e:
                # Clean up the temporary file if download fails
                tmp_file.close()
                tmp_path.unlink(missing_ok=True)
                raise IOError(f"Failed to download remote file: {e}") from e
            finally:
                sftp.close()
        finally:
            # Always close SSH connections
            ssh_client.close()
            for client in reversed(jump_clients):
                client.close()

    @override
    def open(self, mode: str = "rb") -> contextlib.AbstractContextManager[Any]:
        """Open the remote file directly over SSH.

        Returns a file-like object wrapped in a context manager that ensures
        proper cleanup of resources when the file is closed.

        Args:
            mode: File mode ('rb', 'wb', etc.)

        Returns:
            A context manager yielding a file-like object.

        Raises:
            ImportError: If paramiko is not installed.
            paramiko.SSHException: If the SSH connection fails.
            IOError: If the file cannot be opened.
        """
        log.info(f"Opening remote file at {self.ssh.hostname}:{self.remote_path}")

        # Connect to the SSH server
        ssh_client, jump_clients = connect_host(self.ssh)

        try:
            # Open SFTP connection
            sftp = ssh_client.open_sftp()

            try:
                # Open the remote file
                remote_file = sftp.open(str(self.remote_path), mode)
            except Exception as e:
                sftp.close()
                raise IOError(f"Failed to open remote file: {e}") from e
        except Exception as e:
            # Clean up SSH connections if SFTP fails
            ssh_client.close()
            for client in reversed(jump_clients):
                client.close()
            raise

        # Create a context manager to ensure proper cleanup
        @contextlib.contextmanager
        def ssh_file_context():
            try:
                yield remote_file
            finally:
                remote_file.close()
                sftp.close()
                ssh_client.close()
                for client in reversed(jump_clients):
                    client.close()

        return ssh_file_context()

    @classmethod
    def from_uri(cls, uri: str):
        """Create a RemoteSSHFileConfig from an SSH/SCP URI.

        Parses a URI in the format:
        ssh://[username[:password]@]hostname[:port]/path/to/file
        or
        scp://[username[:password]@]hostname[:port]/path/to/file

        Args:
            uri: The SSH or SCP URI to parse.

        Returns:
            A RemoteSSHFileConfig instance configured with connection details and remote path.

        Raises:
            ValueError: If the URI scheme is not 'ssh' or 'scp', or if required components are missing.
        """
        # Parse the URI and get SSH config and remote path
        ssh, remote_path = SSHConfig.from_uri(uri)

        # Create and return the RemoteSSHFileConfig
        return cls(
            ssh=ssh,
            remote_path=remote_path,
        )

    @classmethod
    def from_ssh_config(
        cls,
        host: str,
        remote_path: Path | str,
        config_path: Path | None = None,
    ):
        """Create a RemoteSSHFileConfig from an SSH config host and remote path.

        Args:
            host: The host entry name in the SSH config file.
            remote_path: Path to the file on the remote server.
            config_path: Optional custom path to the SSH config file.
                        If None, uses ~/.ssh/config.

        Returns:
            A RemoteSSHFileConfig instance configured with the SSH config host and remote path.

        Raises:
            FileNotFoundError: If the SSH config file doesn't exist.
            ValueError: If the specified host entry is not found in the config file.
        """
        # Load the SSH config from the config file
        ssh = SSHConfig.from_ssh_config(host, config_path)

        # Create and return the RemoteSSHFileConfig
        return cls(
            ssh=ssh,
            remote_path=remote_path,
        )

    @classmethod
    def from_direct_connection(
        cls,
        hostname: str,
        remote_path: Path | str,
        port: int = 22,
        username: str | None = None,
        password: str | None = None,
        identity_files: Path | list[Path] | None = None,
        proxy_jump: SSHConfig | None = None,
    ):
        """Create a RemoteSSHFileConfig for a direct SSH connection.

        A convenience method for creating a configuration without using SSH config files
        or parsing URIs.

        Args:
            hostname: The hostname or IP address of the SSH server.
            remote_path: Path to the file on the remote server.
            port: SSH port number (default: 22).
            username: Username for authentication (optional).
            password: Password for authentication (optional).
            identity_files: SSH private key file path(s) (optional).
            proxy_jump: SSH configuration for a jump host (optional).

        Returns:
            A RemoteSSHFileConfig instance configured with the provided parameters.
        """
        # Create an SSH config with the provided parameters
        ssh = SSHConfig(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            identity_files=identity_files,
            proxy_jump=proxy_jump,
        )

        # Create and return the RemoteSSHFileConfig
        return cls(ssh=ssh, remote_path=remote_path)
