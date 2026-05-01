# End-to-End Testing Guide

This document describes the end-to-end (E2E) test suite for the Arkime MCP Server.

## Overview

End-to-end tests verify that the MCP server tools work correctly when invoked through the server with all integrations in place. These tests use mocked Arkime backend responses to ensure reproducible and fast test execution without requiring a live Arkime instance.

## Test Coverage

The E2E test suite (`tests/test_e2e.py`) includes **33 comprehensive tests** covering all major tool categories:

### Session Search & Analysis Tools (5 tests)
- ✅ `search_sessions` - Session search with filtering and pagination
- ✅ `get_session_detail` - Full session details retrieval
- ✅ `get_session_packets` - Packet-level data access
- ✅ `get_session_raw` - Raw PCAP data retrieval
- ✅ Session limit enforcement (MAX_SESSION_LIMIT = 200)

### Network Investigation Tools (5 tests)
- ✅ `top_talkers` - Aggregated field value rankings
- ✅ `connections_graph` - Network connection visualization data
- ✅ `unique_destinations` - External IP tracking with RFC1918 filtering
- ✅ `dns_lookups` - DNS query analysis
- ✅ `reverse_dns` - PTR record lookups

### Security & System Health Tools (11 tests)
- ✅ `external_connections` - Non-RFC1918 traffic analysis
- ✅ `geo_summary` - Geographic traffic distribution
- ✅ `capture_status` - Cluster health monitoring
- ✅ `pcap_files` - Capture file inventory
- ✅ `list_fields` - Available field metadata
- ✅ `list_fields` with group filtering
- ✅ `get_field_values` - Field value enumeration
- ✅ `get_current_user` - User information
- ✅ `get_settings` - Viewer configuration
- ✅ `get_stats` - System statistics
- ✅ `get_es_stats` - Elasticsearch/OpenSearch metrics

### Tags, Hunts, Views & Advanced Tools (10 tests)
- ✅ `add_tags` - Session tagging
- ✅ `remove_tags` - Tag removal
- ✅ `create_hunt` - Hunt job creation
- ✅ `get_hunts` - Hunt job listing
- ✅ `delete_hunt` - Hunt job deletion
- ✅ `create_view` - Saved view creation
- ✅ `get_views` - View listing
- ✅ `delete_view` - View deletion
- ✅ `get_notifiers` - Notifier configuration
- ✅ `get_parliament` - Multi-cluster information

### Tool Configuration Tests (2 tests)
- ✅ Disabled tool JSON error responses
- ✅ Disabled tool text error responses

## Running E2E Tests

### Run Only E2E Tests

```bash
# Run all E2E tests
pytest tests/test_e2e.py -v

# Run specific test class
pytest tests/test_e2e.py::TestE2ESessionSearchTools -v

# Run specific test
pytest tests/test_e2e.py::TestE2ESessionSearchTools::test_search_sessions -v
```

### Run All Tests (Unit + E2E)

```bash
# Run entire test suite
pytest -v

# With coverage report
pytest --cov=arkime_mcp_server --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=arkime_mcp_server --cov-report=html
```

## Test Structure

### Test Organization

```python
tests/test_e2e.py
├── Fixtures
│   ├── mock_arkime_client   # Fully mocked Arkime API client
│   └── mock_config           # Mock configuration with all tools enabled
│
├── TestE2ESessionSearchTools     # 5 tests
├── TestE2ENetworkInvestigationTools  # 5 tests
├── TestE2ESecurityAndHealthTools    # 11 tests
├── TestE2ETagsHuntsViewsTools       # 10 tests
└── TestE2EToolConfiguration         # 2 tests
```

### Key Testing Patterns

#### Pattern 1: Tool Invocation with Mocked Backend

```python
@patch("arkime_mcp_server.server.get_client")
@patch("arkime_mcp_server.server.get_config")
def test_search_sessions(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
    """Test tool with mocked Arkime client."""
    mock_get_config.return_value = mock_config
    mock_get_client.return_value = mock_arkime_client

    # Call tool directly (as FastMCP would)
    result = server.search_sessions(expression="ip.src==192.168.1.100")
    result_data = json.loads(result)

    # Verify response structure
    assert "sessions" in result_data
    assert result_data["total_matching"] == 1

    # Verify backend was called correctly
    mock_arkime_client.get_sessions.assert_called_once()
```

#### Pattern 2: Response Validation

```python
def test_connections_graph(self, ...):
    """Test graph structure and data types."""
    result = server.connections_graph()
    result_data = json.loads(result)

    # Validate structure
    assert "nodes" in result_data
    assert "links" in result_data

    # Validate data types and required fields
    node = result_data["nodes"][0]
    assert "id" in node
    assert "sessions" in node
    assert isinstance(node["sessions"], int)
```

#### Pattern 3: Parameter Validation

```python
def test_search_sessions_respects_limit(self, ...):
    """Test parameter constraints are enforced."""
    # Try to exceed MAX_SESSION_LIMIT
    result = server.search_sessions(limit=500)

    # Verify limit was clamped to maximum
    call_args = mock_arkime_client.get_sessions.call_args
    assert call_args[1]["length"] == 200  # MAX_SESSION_LIMIT
```

#### Pattern 4: Configuration Testing

```python
def test_disabled_tool_returns_error(self, ...):
    """Test disabled tools return appropriate error."""
    mock_config.is_tool_enabled.return_value = False

    result = server.search_sessions()
    result_data = json.loads(result)

    assert "error" in result_data
    assert result_data["error"] == "Tool is disabled"
```

## Mock Data Structure

The `mock_arkime_client` fixture provides realistic mock responses for all Arkime API endpoints:

### Session Data
```python
{
    "node": "test-node",
    "id": "session123",
    "source": {"ip": "192.168.1.100", "port": 12345},
    "destination": {"ip": "8.8.8.8", "port": 443},
    "protocol": 6,
    "totBytes": 2048,
    "totDataBytes": 1500,
    "totPackets": 15,
    "firstPacket": 1609459200000,
    "lastPacket": 1609459260000,
    "destination.geo.country_iso_code": "US",
    "destination.as.full": "AS15169 Google LLC"
}
```

### Connection Graph Data
```python
{
    "nodes": [
        {"id": "192.168.1.100", "sessions": 10, "totDataBytes": 50000, "type": 1},
        {"id": "8.8.8.8", "sessions": 5, "totDataBytes": 30000, "type": 2}
    ],
    "links": [
        {"source": 0, "target": 1, "value": 5, "totDataBytes": 30000}
    ]
}
```

### Cluster Health Data
```python
{
    "cluster_name": "arkime-cluster",
    "status": "green",
    "number_of_nodes": 3,
    "active_shards": 10,
    "unassigned_shards": 0,
    "version": "7.10.2",
    "molochDbVersion": 73
}
```

## Test Metrics

As of the latest run:

| Metric | Value |
|--------|-------|
| **Total E2E Tests** | 33 |
| **Passing** | 33 (100%) |
| **Failing** | 0 |
| **Average Runtime** | ~1.1 seconds |
| **Tools Covered** | 30+ tools |

## Adding New E2E Tests

When adding new MCP tools to the server, follow this pattern:

### Step 1: Add Mock Response

```python
# In mock_arkime_client fixture
client.new_method.return_value = {
    "expected": "data",
    "structure": "here"
}
```

### Step 2: Create Test

```python
@patch("arkime_mcp_server.server.get_client")
@patch("arkime_mcp_server.server.get_config")
def test_new_tool(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
    """Test new_tool functionality."""
    mock_get_config.return_value = mock_config
    mock_get_client.return_value = mock_arkime_client

    result = server.new_tool(param="value")
    result_data = json.loads(result)

    # Verify response
    assert "expected" in result_data

    # Verify backend call
    mock_arkime_client.new_method.assert_called_once_with(param="value")
```

### Step 3: Run Tests

```bash
pytest tests/test_e2e.py::TestYourClass::test_new_tool -v
```

## Best Practices

### ✅ DO:
- Test all tool parameters and their effects
- Verify JSON structure of responses
- Check that backend methods are called with correct arguments
- Test both enabled and disabled tool configurations
- Validate data type constraints
- Test edge cases (empty results, maximum limits, etc.)

### ❌ DON'T:
- Rely on a live Arkime instance (use mocks)
- Test implementation details (internal functions)
- Duplicate unit test coverage
- Test FastMCP framework behavior (that's upstream's responsibility)

## Integration with CI/CD

E2E tests run automatically in GitHub Actions on:
- Push to `main` or `develop` branches
- Pull requests
- Manual workflow dispatch

CI configuration (`.github/workflows/tests.yml`):
```yaml
- name: Run tests
  run: |
    pytest --cov=arkime_mcp_server --cov-report=xml --cov-report=term-missing
```

This includes both unit tests and E2E tests in a single run.

## Troubleshooting

### Issue: Import Errors

**Solution:** Ensure dependencies are installed:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Issue: Mock Not Working

**Problem:** Patches not applying correctly

**Solution:** Ensure patch decorators are in correct order (bottom-up execution):
```python
@patch("module.get_client")      # Applied second (innermost)
@patch("module.get_config")      # Applied first (outermost)
def test_function(self, mock_get_config, mock_get_client):
    # mock_get_config corresponds to second decorator
    # mock_get_client corresponds to first decorator
    pass
```

### Issue: JSON Decode Errors

**Problem:** Tool returns string instead of JSON

**Solution:** Some tools return plain text (e.g., `top_talkers`, `geo_summary`). Don't use `json.loads()` on these:
```python
# For text-returning tools
result = server.top_talkers()
assert isinstance(result, str)

# For JSON-returning tools
result = server.search_sessions()
result_data = json.loads(result)
```

### Issue: Test Isolation Problems

**Problem:** Tests interfere with each other

**Solution:** Each test should be independent. Avoid class-level state. Use fresh fixtures per test:
```python
@pytest.fixture
def fresh_client():
    """Create new mock client for each test."""
    return Mock()
```

## Comparison: Unit vs E2E Tests

| Aspect | Unit Tests | E2E Tests |
|--------|-----------|-----------|
| **Scope** | Single function/class | Full tool invocation |
| **Dependencies** | Mocked or minimal | All integrations |
| **Speed** | Very fast (~0.01s each) | Fast (~0.03s each) |
| **Coverage** | Implementation details | User-facing behavior |
| **Example** | `format_bytes(1024)` | `search_sessions(limit=50)` |

Both are valuable:
- **Unit tests** ensure individual components work correctly
- **E2E tests** ensure the complete system behaves as expected

## Future Enhancements

Potential additions to the E2E test suite:

1. **Error Handling Tests**
   - Network failures
   - Authentication errors
   - Malformed responses

2. **Performance Tests**
   - Large result set handling
   - Timeout behavior
   - Rate limiting

3. **Integration Tests with Real MCP Protocol**
   - Test with actual MCP client
   - Test JSON-RPC serialization
   - Test streaming responses

4. **Workflow Tests**
   - Multi-step investigations
   - Chained tool invocations
   - State management

## Related Documentation

- [Main Testing Guide](README.md) - Overview of all testing
- [Test Summary](../TEST_SUMMARY.md) - High-level metrics
- [pytest Documentation](https://docs.pytest.org/) - Testing framework
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html) - Mocking library

## Questions?

For questions or issues with E2E tests:
1. Check existing test examples in `tests/test_e2e.py`
2. Review mock fixture setup in the same file
3. Ensure patches target the correct import paths
4. Verify mock return values match expected structure
