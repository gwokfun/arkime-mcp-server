# Test Suite Summary

## Overview

The Arkime MCP Server now includes a comprehensive unit test suite built with pytest. This document provides a high-level summary of the testing infrastructure.

## Quick Stats

- **Total Tests**: 46
- **Pass Rate**: 100%
- **Execution Time**: ~1.3 seconds
- **Overall Coverage**: 57%
- **Perfect Coverage Modules**: utils.py (100%), config.py (100%)

## Test Modules

### 1. test_utils.py (18 tests)

Tests all utility functions used throughout the application.

**Coverage: 100%**

- `format_bytes()` - 7 tests for byte size formatting
- `format_timestamp()` - 4 tests for timestamp formatting
- `protocol_name()` - 5 tests for protocol number to name conversion
- `summarize_session()` - 3 tests for session data summarization

**Key Test Cases:**
- Edge cases (None, 0, negative values)
- All unit conversions (B, KB, MB, GB, TB, PB)
- Timestamp validation and formatting
- Protocol mapping for TCP, UDP, ICMP, and unknown protocols
- Session summarization with complete, partial, and minimal data

### 2. test_config.py (8 tests)

Tests configuration loading from environment variables and YAML files.

**Coverage: 100%**

**Test Categories:**
- Environment variable requirements and validation
- Default configuration values
- Environment variable overrides
- YAML configuration file loading
- Environment precedence over YAML
- Tool enable/disable functionality

**Key Test Cases:**
- Password requirement enforcement
- Multiple configuration sources (env vars, YAML, defaults)
- Tool enablement configuration
- Configuration precedence rules

### 3. test_client.py (19 tests)

Tests the Arkime API client with HTTP request mocking.

**Coverage: 67%**

**DigestAuth Tests (6 tests):**
- Initialization
- WWW-Authenticate header parsing
- Authorization header building (with/without qop)
- Opaque value handling

**ArkimeClient Tests (13 tests):**
- Client initialization and configuration
- Context manager functionality
- HTTP methods (GET, POST, DELETE)
- API method wrappers (sessions, health, connections, unique, etc.)
- JSON and text response handling

**Mocking Strategy:**
- Uses `unittest.mock` for HTTP client mocking
- Simulates successful API responses
- Tests parameter passing and response parsing

## Test Infrastructure

### Dependencies (requirements-dev.txt)

```
pytest>=7.0.0          # Testing framework
pytest-cov>=4.0.0      # Coverage reporting
pytest-mock>=3.10.0    # Enhanced mocking
responses>=0.23.0      # HTTP response mocking
```

### Configuration (pytest.ini)

- Test discovery from `tests/` directory
- Coverage reporting with multiple formats (term, HTML, XML)
- Strict marker enforcement
- Short traceback format for readability

### CI/CD (.github/workflows/tests.yml)

**GitHub Actions Workflow:**
- Runs on Python 3.10, 3.11, 3.12
- Triggers on push/PR to main and develop branches
- Generates coverage reports
- Uploads to Codecov (optional)

## Coverage Details

### Module Coverage Breakdown

| Module | Statements | Missing | Coverage |
|--------|------------|---------|----------|
| utils.py | 26 | 0 | 100% |
| config.py | 46 | 0 | 100% |
| client.py | 172 | 56 | 67% |
| server.py | 227 | 149 | 34% |
| **Total** | **474** | **205** | **57%** |

### Why Some Coverage is Lower

- **client.py (67%)**: Some API methods and edge cases not yet tested
- **server.py (34%)**: FastMCP tool registration is harder to test in isolation; would require integration testing

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_utils.py

# Run specific test class
pytest tests/test_utils.py::TestFormatBytes

# Run specific test method
pytest tests/test_utils.py::TestFormatBytes::test_kilobytes
```

### Coverage Reports

```bash
# Terminal coverage report
pytest --cov=arkime_mcp_server --cov-report=term-missing

# HTML coverage report (opens in browser)
pytest --cov=arkime_mcp_server --cov-report=html
open htmlcov/index.html

# XML coverage report (for CI)
pytest --cov=arkime_mcp_server --cov-report=xml
```

## Test Writing Guidelines

### 1. Test Organization

```python
class TestModuleName:
    """Tests for ModuleName class/function."""

    def test_specific_functionality(self):
        """Test description."""
        # Arrange
        input_data = ...

        # Act
        result = function(input_data)

        # Assert
        assert result == expected
```

### 2. Naming Conventions

- Test files: `test_<module>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<functionality>`

### 3. Test Independence

Each test should:
- Be independent (no shared state)
- Clean up after itself (restore env vars, delete temp files)
- Use fixtures for common setup
- Not depend on test execution order

### 4. Coverage Goals

- Aim for 100% coverage on utility functions
- Aim for 90%+ coverage on core logic
- Mock external dependencies (HTTP, file I/O)
- Test edge cases and error conditions

## Future Enhancements

### Recommended Additions

1. **Integration Tests**
   - Test against real Arkime instance
   - End-to-end API workflows
   - Real HTTP request/response cycles

2. **Performance Tests**
   - Load testing for API methods
   - Response time benchmarks
   - Memory usage profiling

3. **MCP Integration Tests**
   - Test full MCP server functionality
   - Tool invocation and responses
   - FastMCP integration

4. **Property-Based Tests**
   - Use Hypothesis for generative testing
   - Test with random inputs
   - Discover edge cases automatically

5. **Mutation Testing**
   - Use mutmut to verify test quality
   - Ensure tests catch code changes
   - Improve test effectiveness

## Continuous Integration

Tests automatically run on:
- Every push to main/develop
- Every pull request
- Multiple Python versions (3.10, 3.11, 3.12)

**CI Status Checks:**
- All tests must pass
- Coverage report generated
- No import errors
- Clean test execution

## Documentation

- **tests/README.md**: Detailed testing documentation
- **README.md**: Quick start testing section
- **This file**: High-level summary

## Maintenance

### Adding New Tests

When adding new functionality:

1. Write tests first (TDD approach)
2. Ensure tests cover normal and edge cases
3. Run tests locally before committing
4. Check coverage hasn't decreased
5. Update test documentation if needed

### Debugging Test Failures

```bash
# Run with full traceback
pytest --tb=long

# Run with print statements visible
pytest -s

# Run with pdb debugger on failure
pytest --pdb

# Run only failed tests from last run
pytest --lf
```

## Conclusion

The test suite provides solid coverage of core functionality with fast execution and clear organization. All critical utility and configuration code has 100% test coverage, ensuring reliability and making refactoring safer.

For questions or issues, see the detailed documentation in `tests/README.md`.
