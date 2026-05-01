# Migration Guide: TypeScript to Python

This document outlines the changes made during the refactoring from TypeScript/Node.js to Python 3/FastMCP.

## Technology Stack Changes

### Before (TypeScript)
- **Runtime**: Node.js
- **Language**: TypeScript
- **MCP SDK**: `@modelcontextprotocol/sdk`
- **HTTP Client**: digest-fetch
- **Configuration**: Environment variables only

### After (Python)
- **Runtime**: Python 3.10+
- **Language**: Python 3
- **MCP SDK**: FastMCP
- **HTTP Client**: httpx with custom Digest authentication
- **Configuration**: YAML config files + environment variables + .env support

## Project Structure Changes

### Before
```
src/
├── index.ts          # Main server file
└── arkime-client.ts  # Arkime API client
package.json
tsconfig.json
```

### After
```
arkime_mcp_server/
├── __init__.py       # Package initialization
├── server.py         # FastMCP server with all tools
├── client.py         # Arkime API client
├── config.py         # Configuration management
└── utils.py          # Utility functions
pyproject.toml
requirements.txt
config.example.yaml
.env.example
```

## Feature Additions

### 1. Configuration Management
- **YAML Configuration**: `config.yaml` for persistent settings
- **Environment Variables**: Support for .env files
- **Tool Management**: Enable/disable individual tools via configuration

### 2. Expanded API Coverage
- **Before**: 12 tools covering basic operations
- **After**: 30+ tools covering comprehensive Arkime API v3

New tool categories:
- Tags & Annotations (add_tags, remove_tags)
- Hunt (create_hunt, get_hunts, delete_hunt)
- Views (create_view, get_views, delete_view)
- Statistics (get_stats, get_es_stats)
- User & Settings (get_current_user, get_settings)
- Advanced (get_notifiers, get_parliament)

### 3. HTTP Digest Authentication
- **Before**: Used `digest-fetch` npm package
- **After**: Custom implementation using httpx's auth flow system

## Tool Mapping

All original tools are preserved with the same names:

| Tool | Status | Notes |
|------|--------|-------|
| search_sessions | ✅ Migrated | Same functionality |
| get_session_detail | ✅ Migrated | Same functionality |
| get_session_packets | ✅ Migrated | Same functionality |
| top_talkers | ✅ Migrated | Same functionality |
| connections_graph | ✅ Migrated | Same functionality |
| unique_destinations | ✅ Migrated | Same functionality |
| dns_lookups | ✅ Migrated | Same functionality |
| reverse_dns | ✅ Migrated | Same functionality |
| external_connections | ✅ Migrated | Same functionality |
| geo_summary | ✅ Migrated | Same functionality |
| capture_status | ✅ Migrated | Same functionality |
| pcap_files | ✅ Migrated | Same functionality |
| list_fields | ✅ Migrated | Same functionality |

## API Changes

### Client Initialization

**Before (TypeScript):**
```typescript
const client = new ArkimeClient(url, user, password);
```

**After (Python):**
```python
client = ArkimeClient(url, user, password)
```

### Making Requests

**Before (TypeScript):**
```typescript
const result = await client.sessions({
  expression: "ip.src==192.168.1.1",
  date: 1,
  length: 50
});
```

**After (Python):**
```python
result = client.get_sessions(
    expression="ip.src==192.168.1.1",
    date=1,
    length=50
)
```

## Configuration Examples

### Environment Variables

**Before:**
```bash
export ARKIME_URL="http://192.168.5.176:8005"
export ARKIME_USER="mcp"
export ARKIME_PASSWORD="your-password"
```

**After (same, with .env support):**
```bash
# .env file
ARKIME_URL=http://your-arkime-server:8005
ARKIME_USER=mcp
ARKIME_PASSWORD=your-password
```

### New: YAML Configuration

```yaml
# config.yaml
arkime:
  url: "http://your-arkime-server:8005"
  user: "mcp"

tools:
  search_sessions: true
  get_session_detail: false  # Disable this tool
```

## Claude Desktop Configuration

**Before (TypeScript):**
```json
{
  "mcpServers": {
    "arkime": {
      "command": "node",
      "args": ["/path/to/build/index.js"],
      "env": {
        "ARKIME_PASSWORD": "your-password"
      }
    }
  }
}
```

**After (Python):**
```json
{
  "mcpServers": {
    "arkime": {
      "command": "python",
      "args": ["-m", "arkime_mcp_server.server"],
      "env": {
        "ARKIME_PASSWORD": "your-password"
      }
    }
  }
}
```

## Installation Changes

### Before
```bash
npm install
npm run build
npm start
```

### After
```bash
pip install -r requirements.txt
# Or: pip install -e .
python -m arkime_mcp_server.server
# Or: arkime-mcp-server (if installed)
```

## Benefits of the Migration

1. **Simpler Dependency Management**: Python's pip vs npm
2. **Configuration Flexibility**: YAML + env + .env support
3. **Tool Granularity**: Enable/disable specific tools
4. **Expanded Functionality**: 30+ tools vs 12 tools
5. **Better Error Handling**: Python's exception handling
6. **Type Hints**: Python type hints for better IDE support
7. **No Build Step**: Direct Python execution vs TypeScript compilation

## Breaking Changes

None for end users! The tool names and functionality remain the same. Only the installation and configuration methods have changed.

## Migration Checklist

For users migrating from TypeScript to Python version:

- [ ] Install Python 3.10+ if not already installed
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Update Claude Desktop config to use Python instead of Node
- [ ] (Optional) Create config.yaml for persistent configuration
- [ ] (Optional) Create .env file for environment variables
- [ ] Test that all tools work as expected

## Future Enhancements

Potential areas for future development:
- Unit tests for all tools
- Integration tests with mock Arkime server
- Support for Arkime API v4+ (when released)
- CLI interface for standalone usage
- Docker container for easy deployment
- Performance optimizations for large result sets
