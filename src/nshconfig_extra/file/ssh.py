from __future__ import annotations

import contextlib
import logging
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from typing_extensions import override

from .base import BaseFileConfig

log = logging.getLogger(__name__)


class RemoteSSHFileConfig(BaseFileConfig):
    hostname: str
    port: int = 22
    username: str | None = None
    password: str | None = None
    remote_path: str

    @override
    def resolve(self):
        """
        Downloads the remote file to a temporary file and returns its local Path.
        This method incurs the overhead of copying the file locally.
        """
        try:
            import paramiko
        except ImportError:
            raise ImportError(
                "Paramiko is required for SSH/SCP URIs. Please install it with `pip install paramiko`."
            )

        log.info(
            f"Downloading remote file via SSH from {self.hostname}:{self.port}{self.remote_path}"
        )
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            self.hostname,
            port=self.port,
            username=self.username,
            password=self.password,
        )
        sftp = ssh.open_sftp()
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            sftp.getfo(self.remote_path, tmp_file)
            tmp_file.close()
        finally:
            sftp.close()
            ssh.close()
        return Path(tmp_file.name)

    @override
    def open(self, mode: str = "rb"):
        """
        Opens the remote file directly over SSH without copying it locally.
        Returns a file-like object wrapped in a context manager that ensures proper cleanup.
        """
        try:
            import paramiko
        except ImportError:
            raise ImportError(
                "Paramiko is required for SSH/SCP URIs. Please install it with `pip install paramiko`."
            )

        log.info(
            f"Opening remote file via SSH from {self.hostname}:{self.port}{self.remote_path}"
        )
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            self.hostname,
            port=self.port,
            username=self.username,
            password=self.password,
        )
        sftp = ssh.open_sftp()
        remote_file = sftp.open(self.remote_path, mode)

        @contextlib.contextmanager
        def sftp_file_context():
            try:
                yield remote_file
            finally:
                remote_file.close()
                sftp.close()
                ssh.close()

        return sftp_file_context()

    @classmethod
    def from_uri(cls, uri: str) -> RemoteSSHFileConfig:
        """
        Parses a URI in the form:
            ssh://[username:password@]hostname[:port]/path/to/file
        and returns an instance of RemoteSSHFileConfig.
        """
        parsed = urlparse(uri)
        if parsed.scheme not in ("ssh", "scp"):
            raise ValueError("URI scheme must be ssh or scp")
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("URI must contain a hostname")

        port = parsed.port or 22
        username = parsed.username
        password = parsed.password
        remote_path = parsed.path
        if not remote_path:
            raise ValueError("URI must contain a path")

        return cls(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            remote_path=remote_path,
        )
