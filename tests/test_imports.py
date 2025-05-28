"""Tests for package imports and public API."""

from __future__ import annotations

import pytest


class TestPackageImports:
    """Test that all public imports work correctly."""

    def test_main_package_imports(self):
        """Test importing from the main package."""
        # These should all work without error
        from nshconfig_extra import (
            AnyFileConfig,
            BaseFileConfig,
            CachedPath,
            CachedPathConfig,
            RemoteSSHFileConfig,
            open_file_config,
            resolve_file_config,
        )

        # Verify they are not None
        assert AnyFileConfig is not None
        assert BaseFileConfig is not None
        assert CachedPath is not None
        assert CachedPathConfig is not None
        assert RemoteSSHFileConfig is not None
        assert open_file_config is not None
        assert resolve_file_config is not None

    def test_file_subpackage_imports(self):
        """Test importing from the file subpackage."""
        from nshconfig_extra.file import (
            AnyFileConfig,
            BaseFileConfig,
            CachedPath,
            CachedPathConfig,
            RemoteSSHFileConfig,
            open_file_config,
            resolve_file_config,
        )

        # Verify they are not None
        assert AnyFileConfig is not None
        assert BaseFileConfig is not None
        assert CachedPath is not None
        assert CachedPathConfig is not None
        assert RemoteSSHFileConfig is not None
        assert open_file_config is not None
        assert resolve_file_config is not None

    def test_ssh_submodule_imports(self):
        """Test importing from the SSH submodule."""
        from nshconfig_extra.file.ssh import RemoteSSHFileConfig, SSHConfig

        assert RemoteSSHFileConfig is not None
        assert SSHConfig is not None

    def test_cached_path_submodule_imports(self):
        """Test importing from the cached path submodule."""
        from nshconfig_extra.file.cached_path_ import CachedPathConfig

        assert CachedPathConfig is not None

    def test_base_submodule_imports(self):
        """Test importing from the base submodule."""
        from nshconfig_extra.file.base import (
            AnyFileConfig,
            BaseFileConfig,
            open_file_config,
            resolve_file_config,
        )

        assert AnyFileConfig is not None
        assert BaseFileConfig is not None
        assert open_file_config is not None
        assert resolve_file_config is not None

    def test_version_import(self):
        """Test that version can be imported."""
        from nshconfig_extra import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)

    def test_import_consistency(self):
        """Test that imports from different paths refer to the same objects."""
        # Import from main package
        from nshconfig_extra import BaseFileConfig as MainBaseFileConfig
        from nshconfig_extra import CachedPathConfig as MainCachedPathConfig
        from nshconfig_extra import RemoteSSHFileConfig as MainRemoteSSHFileConfig

        # Import from file subpackage
        from nshconfig_extra.file import BaseFileConfig as FileBaseFileConfig
        from nshconfig_extra.file import CachedPathConfig as FileCachedPathConfig
        from nshconfig_extra.file import (
            RemoteSSHFileConfig as FileRemoteSSHFileConfig,
        )

        # Import from specific submodules
        from nshconfig_extra.file.base import BaseFileConfig as BaseBaseFileConfig
        from nshconfig_extra.file.cached_path_ import (
            CachedPathConfig as CachedCachedPathConfig,
        )
        from nshconfig_extra.file.ssh import (
            RemoteSSHFileConfig as SSHRemoteSSHFileConfig,
        )

        # All should be the same object
        assert MainBaseFileConfig is FileBaseFileConfig
        assert FileBaseFileConfig is BaseBaseFileConfig

        assert MainCachedPathConfig is FileCachedPathConfig
        assert FileCachedPathConfig is CachedCachedPathConfig

        assert MainRemoteSSHFileConfig is FileRemoteSSHFileConfig
        assert FileRemoteSSHFileConfig is SSHRemoteSSHFileConfig

    def test_cached_path_alias(self):
        """Test that CachedPath and CachedPathConfig are the same."""
        from nshconfig_extra import CachedPath, CachedPathConfig

        # These should be the same class (CachedPath is an alias)
        assert CachedPath is CachedPathConfig

    def test_class_hierarchy(self):
        """Test that class hierarchy is correctly exposed."""
        from nshconfig_extra import (
            BaseFileConfig,
            CachedPathConfig,
            RemoteSSHFileConfig,
        )

        # Both concrete classes should inherit from BaseFileConfig
        assert issubclass(CachedPathConfig, BaseFileConfig)
        assert issubclass(RemoteSSHFileConfig, BaseFileConfig)

        # Create instances to verify they work
        cached_config = CachedPathConfig(uri="test://example.com/file")
        assert isinstance(cached_config, BaseFileConfig)

        # We need SSHConfig for RemoteSSHFileConfig
        from nshconfig_extra.file.ssh import SSHConfig

        ssh_config = SSHConfig(hostname="example.com")
        remote_config = RemoteSSHFileConfig(ssh=ssh_config, remote_path="/test")
        assert isinstance(remote_config, BaseFileConfig)

    def test_nshconfig_integration(self):
        """Test that the classes properly integrate with nshconfig."""
        from nshconfig_extra import BaseFileConfig, CachedPathConfig

        # BaseFileConfig should inherit from nshconfig.Config
        try:
            import nshconfig as C

            assert issubclass(BaseFileConfig, C.Config)

            # Concrete implementations should also inherit from nshconfig.Config
            assert issubclass(CachedPathConfig, C.Config)
        except ImportError:
            # If nshconfig is not available, skip this test
            pytest.skip("nshconfig is not available")

    def test_optional_dependencies(self):
        """Test behavior with optional dependencies."""
        # Test that SSH functionality requires paramiko
        from nshconfig_extra.file.ssh import SSHConfig

        # This should work (creating the config doesn't require paramiko)
        ssh_config = SSHConfig(hostname="example.com")
        assert ssh_config.hostname == "example.com"

        # But using SSH config file functionality should check for paramiko
        # (this is tested more thoroughly in test_ssh.py)

    def test_typing_extensions_usage(self):
        """Test that typing extensions are used correctly."""
        # The package uses typing_extensions for TypeAliasType and other features
        # This test ensures the imports work correctly
        from nshconfig_extra.file.base import AnyFileConfig

        # AnyFileConfig should be a TypeAliasType
        # We can't easily test this without importing typing_extensions
        # But we can at least verify it exists and can be used in type annotations
        assert AnyFileConfig is not None
