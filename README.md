# nshconfig-extra

`nshconfig-extra` is a collection of additional configuration types for the [nshconfig](https://github.com/nimashoghi/nshconfig) library. It extends the functionality of `nshconfig` by providing support for file handling across various storage systems (local, remote SSH, URLs, cloud storage) through a unified interface.

## Installation

To install `nshconfig-extra`, use the following command:

```bash
pip install nshconfig-extra
```

If you want to use this library with optional dependencies (SSH support), you can install the extra dependencies using the following command:

```bash
pip install nshconfig-extra[extra]
```

## Usage

### File Handling

The package provides a unified interface for working with files from various sources.

#### Base File Config

All file configurations inherit from `BaseFileConfig`, which provides a consistent interface:

```python
from nshconfig_extra import BaseFileConfig, AnyFileConfig, resolve_file_config, open_file_config

# Type alias for any file reference
# AnyFileConfig = str | Path | BaseFileConfig

# Helper functions for working with any file type
path = resolve_file_config("path/to/file.txt")  # Returns a Path object
with open_file_config("path/to/file.txt", "rt") as f:
    content = f.read()
```

#### CachedPathConfig

The `CachedPathConfig` class provides access to files from various sources with automatic caching:

```python
from nshconfig_extra import CachedPathConfig

# Access a file from Hugging Face Hub
config = CachedPathConfig(uri="https://huggingface.co/user/repo/resolve/main/file.txt")
local_path = config.resolve()  # Downloads if needed, returns local cached path
with config.open("rt") as f:   # Opens the file directly
    content = f.read()

# Access a file from S3
s3_config = CachedPathConfig(uri="s3://bucket/path/to/file.txt")
s3_path = s3_config.resolve()

# Local file with caching
local_config = CachedPathConfig(uri="/path/to/file.txt")
```

Supported URI types:
- Local file paths
- HTTP/HTTPS URLs
- S3 bucket paths (s3://...)
- GCS bucket paths (gs://...)
- Hugging Face Hub paths

#### SSH File Access

For accessing files on remote servers via SSH:

```python
from nshconfig_extra import RemoteSSHFileConfig

# Using SSH URI
ssh_config = RemoteSSHFileConfig.from_uri("ssh://user:pass@hostname:22/path/to/file.txt")

# Using SSH config file (~/.ssh/config)
ssh_config = RemoteSSHFileConfig.from_ssh_config("host_alias", "/path/to/remote/file.txt")

# Direct connection
ssh_config = RemoteSSHFileConfig.from_direct_connection(
    hostname="example.com",
    remote_path="/path/to/file.txt",
    username="user",
    password="pass"
)

# Accessing the file
local_path = ssh_config.resolve()  # Downloads to temporary location
with ssh_config.open("rt") as f:    # Opens directly over SSH
    content = f.read()
```

## Contributing

Contributions to `nshconfig-extra` are welcome! If you encounter any issues or have suggestions for improvement, please open an issue or submit a pull request on the [GitHub repository](https://github.com/nimashoghi/nshconfig-extra).

## License

`nshconfig-extra` is open-source software licensed under the [MIT License](LICENSE).

## Acknowledgements

`nshconfig-extra` (and `nshconfig`) are heavily dependent on the [Pydantic](https://pydantic-docs.helpmanual.io/) library for defining and validating configuration types. The file caching functionality leverages the [cached-path](https://github.com/allenai/cached_path) library.