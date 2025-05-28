# Test Suite for nshconfig-extra

This directory contains a comprehensive test suite for the `nshconfig-extra` library, which provides additional file configuration capabilities for the `nshconfig` library.

## Test Structure

### Test Files

- **`conftest.py`** - Pytest configuration and shared fixtures
- **`test_base.py`** - Tests for the base file configuration functionality
- **`test_cached_path.py`** - Tests for the CachedPathConfig functionality
- **`test_ssh.py`** - Tests for SSH file configuration functionality
- **`test_integration.py`** - Integration tests between different components
- **`test_imports.py`** - Tests for package imports and public API

### Fixtures

The test suite includes several useful fixtures defined in `conftest.py`:

- `temp_dir` - Provides a temporary directory for tests
- `sample_text_file` - Creates a sample text file with known content
- `sample_binary_file` - Creates a sample binary file with known content
- `nonexistent_file` - Returns a path to a nonexistent file
- `ssh_config_content` - Sample SSH config content
- `mock_ssh_config_file` - Creates a mock SSH config file

## Running Tests

### Prerequisites

Install the test dependencies:

```bash
poetry install --with dev
```

### Running All Tests

```bash
# From the project root
pytest tests/

# With coverage
pytest tests/ --cov=nshconfig_extra --cov-report=html
```

### Running Specific Test Files

```bash
# Test base functionality
pytest tests/test_base.py

# Test CachedPath functionality
pytest tests/test_cached_path.py

# Test SSH functionality
pytest tests/test_ssh.py

# Test integration
pytest tests/test_integration.py

# Test imports
pytest tests/test_imports.py
```

### Running Specific Test Classes or Methods

```bash
# Test a specific class
pytest tests/test_base.py::TestBaseFileConfig

# Test a specific method
pytest tests/test_ssh.py::TestSSHConfig::test_from_uri_complete
```

## Test Coverage

The test suite aims for comprehensive coverage of:

### Base Functionality (`test_base.py`)
- Abstract `BaseFileConfig` class behavior
- `resolve_file_config()` utility function with different input types
- `open_file_config()` utility function with different modes
- Type alias `AnyFileConfig` behavior
- Error handling for invalid inputs

### CachedPath Functionality (`test_cached_path.py`)
- `CachedPathConfig` initialization with various options
- Integration with `cached_path` library (mocked)
- File resolution and opening for local and remote files
- Archive extraction functionality
- Caching behavior

### SSH Functionality (`test_ssh.py`)
- `SSHConfig` creation and configuration
- URI parsing for SSH/SCP URIs
- SSH config file parsing (with paramiko mocking)
- `RemoteSSHFileConfig` file access over SSH
- Proxy jump configuration
- Authentication methods (password, key files)

### Integration Tests (`test_integration.py`)
- Cross-functionality between different file config types
- Utility functions working with all config types
- Error handling consistency
- Binary vs text mode consistency
- Multiple configurations in workflows

### Import Tests (`test_imports.py`)
- All public imports work correctly
- Import consistency across different paths
- Package structure validation
- Class hierarchy verification
- Integration with nshconfig library

## Mocking Strategy

The test suite uses extensive mocking to avoid external dependencies:

- **SSH connections** are mocked using `unittest.mock` to avoid requiring actual SSH servers
- **`cached_path`** functionality is mocked to avoid network requests
- **`paramiko`** availability is mocked to test optional dependency handling
- **File system operations** use temporary directories to avoid side effects

## Test Patterns

### Configuration Testing
```python
# Test configuration creation
config = CachedPathConfig(uri="https://example.com/file.txt")
assert config.uri == "https://example.com/file.txt"
```

### Mocked External Calls
```python
@patch("nshconfig_extra.file.cached_path_.cached_path")
def test_resolve_calls_cached_path(self, mock_cached_path, temp_dir):
    mock_cached_path.return_value = temp_dir / "cached_file.txt"
    # ... test logic
```

### Error Handling
```python
def test_invalid_input_raises_error(self):
    with pytest.raises(ValueError, match="expected error message"):
        function_that_should_fail()
```

### Context Manager Testing
```python
def test_file_opening(self, sample_file):
    with open_file_config(sample_file, "r") as f:
        content = f.read()
        assert content == "expected content"
```

## Adding New Tests

When adding new functionality to `nshconfig-extra`, please:

1. **Add unit tests** for the new functionality in the appropriate test file
2. **Add integration tests** if the functionality interacts with existing components
3. **Update fixtures** in `conftest.py` if new test data is needed
4. **Mock external dependencies** appropriately
5. **Test error conditions** as well as success cases
6. **Verify imports** work correctly in `test_imports.py`

## Continuous Integration

This test suite is designed to run in CI environments without external dependencies thanks to comprehensive mocking. All tests should pass in environments with only the core dependencies installed.

## Test Performance

The test suite is designed to be fast:
- No network requests (all mocked)
- No actual SSH connections (all mocked)
- Minimal file system operations (temporary directories only)
- Parallel execution safe (no shared state between tests)
