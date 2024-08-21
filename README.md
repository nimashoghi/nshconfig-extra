# nshconfig-extra

`nshconfig-extra` is a collection of additional configuration types for the [nshconfig](https://github.com/nimashoghi/nshconfig) library. It extends the functionality of `nshconfig` by providing support for some additional custom configuration types, such as `HFPath` for working with Hugging Face paths and URLs.

## Installation

To install `nshconfig-extra`, use the following command:

```bash
pip install nshconfig-extra
```

If you want to use the this library with optional dependencies, you can install the extra dependencies using the following command:

```bash
pip install nshconfig-extra[extra]
```

## Usage

### HFPath

The `HFPath` configuration type allows you to define and work with Hugging Face paths and URLs seamlessly. It provides methods for parsing Hugging Face paths and URLs and downloading the corresponding files.

#### Parsing Hugging Face Paths

To parse a Hugging Face path, use the `HFPath.from_hf_path()` method:

```python
from nshconfig_extra import HFPath

path = HFPath.from_hf_path("user/repo@branch/path/to/file")
```

The path should be in the format `{user}/{repo}@{branch}/{path/to/file}`. If the branch is not specified, the default branch "main" will be used. If the file path is not specified, an empty string will be used.

#### Parsing Hugging Face URLs

To parse a Hugging Face URL, use the `HFPath.from_hf_url()` method:

```python
from nshconfig_extra import HFPath

path = HFPath.from_hf_url("https://huggingface.co/user/repo/resolve/branch/path/to/file")
```

The URL should be a valid Hugging Face URL pointing to a specific file in a repository.

#### Downloading Files

Once you have an `HFPath` instance, you can download the corresponding file using the `download()` method:

```python
local_path = path.download()
```

The `download()` method will download the file if it doesn't exist locally and return the local path to the downloaded file.

## Contributing

Contributions to `nshconfig-extra` are welcome! If you encounter any issues or have suggestions for improvement, please open an issue or submit a pull request on the [GitHub repository](https://github.com/nimashoghi/nshconfig-extra).

## License

`nshconfig-extra` is open-source software licensed under the [MIT License](LICENSE).

## Acknowledgements

`nshconfig-extra` (and `nshconfig`) are heavily dependent on the [Pydantic](https://pydantic-docs.helpmanual.io/) library for defining and validating configuration types.
