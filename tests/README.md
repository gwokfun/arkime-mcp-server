# Testing Guide

This document describes the testing infrastructure for the Arkime MCP Server.

## Test Structure

```
tests/
├── __init__.py           # Test package initialization
├── test_utils.py         # Tests for utility functions
├── test_config.py        # Tests for configuration management
├── test_client.py        # Tests for Arkime API client
├── test_e2e.py           # End-to-end tests for MCP server tools
├── README.md             # This file - testing overview
└── E2E_TESTS.md          # Detailed E2E testing documentation
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=arkime_mcp_server --cov-report=term-missing
```

### Run Tests with HTML Coverage Report

```bash
pytest --cov=arkime_mcp_server --cov-report=html
# Open htmlcov/index.html in a browser
```

### Run Specific Test File

```bash
pytest tests/test_utils.py
```

### Run Specific Test Class

```bash
pytest tests/test_utils.py::TestFormatBytes
```

### Run Specific Test Method

```bash
pytest tests/test_utils.py::TestFormatBytes::test_kilobytes
```

### Run Tests in Verbose Mode

```bash
pytest -v
```

## Test Coverage

Current test coverage:

- **utils.py**: 100% - All utility functions fully tested
- **config.py**: 100% - All configuration scenarios covered
- **client.py**: 67% - Core client functionality tested with mocks
- **server.py**: 34% - Tool registration tested (FastMCP framework limitations)

### Coverage by Module

| Module | Coverage | Notes |
|--------|----------|-------|
| `utils.py` | 100% | Complete coverage of formatting and helper functions |
| `config.py` | 100% | All configuration paths tested including YAML and env vars |
| `client.py` | 67% | Core API methods tested; some edge cases remain |
| `server.py` | 34% | Tool decorators and basic structure tested |

## Test Categories

### Unit Tests

Test individual functions and classes in isolation:

- **test_utils.py**: Tests for formatting functions (bytes, timestamps, protocols)
- **test_config.py**: Tests for configuration loading from env vars and YAML
- **test_client.py**: Tests for HTTP client and API methods (with mocking)

### End-to-End Tests

Test complete MCP server tool functionality with all integrations:

- **test_e2e.py**: Tests for all 30+ MCP tools with mocked Arkime backend

See [E2E_TESTS.md](E2E_TESTS.md) for detailed end-to-end testing documentation.

### Integration Tests

Currently, integration tests would require a live Arkime instance. These are not included but could be added in a separate test suite.

## Test Fixtures

Tests use the following approaches:

- **Environment Variables**: Tests set/unset env vars to test configuration
- **Temporary Files**: Tests create temporary YAML config files for testing
- **Mocking**: HTTP responses are mocked using `unittest.mock` and `pytest-mock`

## Writing New Tests

### Test Naming Convention

- Test files: `test_<module>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<functionality>`

### Example Test

```python
import pytest
from arkime_mcp_server.utils import format_bytes

class TestFormatBytes:
    """Tests for format_bytes function."""

    def test_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(2048) == "2.0 KB"
```

### Testing Configuration

When testing configuration:

1. Save existing environment variables
2. Set test environment variables
3. Run test
4. Restore original environment variables

Example:

```python
def test_config_env_override(self):
    """Test environment variable override."""
    os.environ["ARKIME_URL"] = "http://custom.url:9000"
    try:
        config = Config()
        assert config.arkime_url == "http://custom.url:9000"
    finally:
        del os.environ["ARKIME_URL"]
```

### Testing with Mocks

When testing HTTP clients:

```python
from unittest.mock import Mock, patch

@patch("arkime_mcp_server.client.httpx.Client")
def test_get_sessions(self, mock_client_class):
    """Test get_sessions method."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}

    mock_http_client = Mock()
    mock_http_client.get.return_value = mock_response
    mock_client_class.return_value = mock_http_client

    client = ArkimeClient("http://test", "user", "pass")
    result = client.get_sessions()
    assert "data" in result
```

## Continuous Integration

Tests are designed to run in CI/CD environments:

- No external dependencies required (Arkime server not needed for unit tests)
- Environment variables can be set in CI configuration
- Tests complete in under 10 seconds

## Test Dependencies

Required packages for testing (from `requirements-dev.txt`):

- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `pytest-mock>=3.10.0` - Mocking utilities
- `responses>=0.23.0` - HTTP response mocking (optional)

## Future Test Enhancements

Potential additions:

1. **Integration Tests**: Tests against a live Arkime instance
2. **Performance Tests**: Load testing for API methods
3. **End-to-End Tests**: Full MCP server testing with Claude
4. **Mutation Testing**: Using `mutmut` or similar
5. **Property-Based Testing**: Using `hypothesis`

## Troubleshooting

### ImportError Issues

If you get import errors, ensure dependencies are installed:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Configuration Errors

Some tests require `ARKIME_PASSWORD` to not be set. If you have it in your environment, temporarily unset it:

```bash
unset ARKIME_PASSWORD
pytest
```

Or run pytest with a clean environment:

```bash
env -i PATH=$PATH HOME=$HOME python3 -m pytest
```

### Coverage Not Generated

Ensure pytest-cov is installed:

```bash
pip install pytest-cov
```

## Test Metrics

As of the latest run:

- **Total Tests**: 85 (52 unit tests + 33 E2E tests)
- **Passing**: 85 (100%)
- **Failing**: 0
- **Average Runtime**: ~2.5 seconds
- **Overall Coverage**: 57%
