# arkime-mcp-server

English | [中文](README_zh.md)

An [MCP](https://modelcontextprotocol.io) server for [Arkime](https://arkime.com) full packet capture. Lets AI assistants search network sessions, investigate traffic patterns, and monitor capture health.

Built with Python 3 and [FastMCP](https://github.com/jlowin/fastmcp).

## Features

- **Complete Arkime API v3 Coverage**: Implements all major Arkime viewer APIs
- **Configurable Tools**: Enable/disable specific tools via configuration file
- **Environment-based Configuration**: Support for `.env` files and environment variables
- **30+ Tools** covering:
  - Session search and analysis
  - Network investigation and connection graphs
  - DNS lookups and reverse DNS
  - Security and anomaly detection
  - System health monitoring
  - Tags, hunts, views, and more

## Tools

### Session Search & Analysis
- `search_sessions` - Search sessions with Arkime expressions
- `get_session_detail` - Full decoded protocol detail for a session
- `get_session_packets` - Decoded packet data
- `get_session_raw` - Raw session data

### Network Investigation
- `top_talkers` - Top N values for any field (hosts, ports, domains, etc.)
- `connections_graph` - Network connection graph with nodes and links
- `unique_destinations` - Distinct external IPs contacted by an internal host
- `dns_lookups` - DNS queries captured in traffic
- `reverse_dns` - PTR/reverse DNS lookup for an IP

### Security & Anomaly
- `external_connections` - Sessions to non-RFC1918 destinations
- `geo_summary` - Destination traffic breakdown by country

### System Health & Info
- `capture_status` - Arkime cluster health and status
- `pcap_files` - PCAP capture files with metadata
- `list_fields` - Available Arkime session fields
- `get_field_values` - Possible values for a field
- `get_current_user` - Current user information
- `get_settings` - Arkime viewer settings
- `get_stats` - Arkime statistics
- `get_es_stats` - Elasticsearch/OpenSearch indices statistics

### Tags & Annotations
- `add_tags` - Add tags to sessions
- `remove_tags` - Remove tags from sessions

### Hunt (Packet Search)
- `create_hunt` - Create a hunt job to search packet payloads
- `get_hunts` - List hunt jobs
- `delete_hunt` - Delete a hunt job

### Views (Saved Searches)
- `create_view` - Create a saved view
- `get_views` - List saved views
- `delete_view` - Delete a view

### Advanced
- `get_notifiers` - List configured notifiers
- `get_parliament` - Parliament (multi-cluster) information

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/gwokfun/arkime-mcp-server.git
cd arkime-mcp-server

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Using pip (when published)

```bash
pip install arkime-mcp-server
```

## Configuration

### Environment Variables

Set these environment variables or create a `.env` file:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ARKIME_URL` | No | `http://192.168.5.176:8005` | Arkime viewer URL |
| `ARKIME_USER` | No | `mcp` | Arkime API username |
| `ARKIME_PASSWORD` | **Yes** | — | Arkime API password |

### Configuration File

Copy `config.example.yaml` to `config.yaml` and customize:

```yaml
arkime:
  url: "http://your-arkime-server:8005"
  user: "your-username"
  # password should be set via ARKIME_PASSWORD env var

tools:
  # Enable/disable specific tools
  search_sessions: true
  get_session_detail: true
  # ... etc
```

### Tool Configuration

You can enable or disable individual tools in the `config.yaml` file. By default, all tools are enabled. Set any tool to `false` to disable it:

```yaml
tools:
  search_sessions: true
  get_session_detail: false  # This tool will be disabled
  top_talkers: true
```

## Usage

### Running the Server

```bash
# Run directly
python -m arkime_mcp_server.server

# Or if installed via pip
arkime-mcp-server
```

### With Claude Desktop

Add to your MCP settings (e.g., `~/Library/Application Support/Claude/claude_desktop_config.json`):

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

### With Other MCP Clients

The server uses stdio transport and follows the MCP protocol specification. It can be used with any MCP-compatible client.

## Authentication

Arkime uses HTTP Digest authentication. The server includes a custom implementation of HTTP Digest authentication using httpx's authentication flow system.

## Development

### Project Structure

```
arkime_mcp_server/
├── __init__.py       # Package initialization
├── server.py         # FastMCP server with all tools
├── client.py         # Arkime API client
├── config.py         # Configuration management
└── utils.py          # Utility functions
```

### Testing

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=arkime_mcp_server --cov-report=term-missing

# Run tests with HTML coverage report
pytest --cov=arkime_mcp_server --cov-report=html
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

**Test Coverage:**
- 46 unit tests covering core functionality
- 100% coverage on utils and config modules
- 67% coverage on client module
- All tests pass in ~1.3 seconds

## API Coverage

This server implements the following Arkime APIs from the [v3+ API documentation](https://arkime.com/apiv3):

- ✅ Sessions API (`/api/sessions`)
- ✅ Session Detail APIs (`/api/session/{node}/{id}/detail`, `/packets`, `/raw`)
- ✅ Connections API (`/api/connections`)
- ✅ Unique API (`/api/unique`)
- ✅ Fields API (`/api/fields`)
- ✅ Health APIs (`/api/eshealth`, `/api/stats`, `/api/esindices`)
- ✅ Files API (`/api/files`)
- ✅ DNS APIs (`/api/reversedns`)
- ✅ User APIs (`/api/user`, `/api/user/settings`)
- ✅ Tags APIs (add/remove tags)
- ✅ Hunt APIs (`/api/hunt`)
- ✅ View APIs (`/api/view`, `/api/views`)
- ✅ Notifiers API (`/api/notifiers`)
- ✅ Parliament API (`/api/parliament`)

## Migration from TypeScript Version

This project has been refactored from TypeScript to Python 3. Key changes:

- **Technology Stack**: Node.js → Python 3, `@modelcontextprotocol/sdk` → FastMCP
- **Configuration**: Added YAML configuration file and `.env` support
- **Tool Management**: New feature to enable/disable tools via configuration
- **API Coverage**: Extended from 12 tools to 30+ tools covering all major Arkime APIs

## Skills (agentskills.io)

In addition to MCP, Arkime tools are exposed as **agentskills.io**-compatible skills so they can be used on any mainstream AI agent platform (Claude, GPT-4, Gemini, LangChain, AutoGen, CrewAI, Dify, Coze, etc.).

### What's Included

✅ **Skills Manifest** ([`skills/arkime_skills.yaml`](skills/arkime_skills.yaml)) - 29 skills in agentskills.io v1.0 format
✅ **Agent Integration Examples** ([`skills/examples/`](skills/examples/)) - Ready-to-use adapters for popular platforms
✅ **Scenario Playbooks** ([`skills/playbooks/`](skills/playbooks/)) - Step-by-step investigation workflows
✅ **Validation Testing** ([`skills/tests/`](skills/tests/)) - Automated validation against MCP tools

Design rationale and implementation details are in [`skills/README.md`](skills/README.md).

### Integration Examples

**OpenAI GPT-4:**
```bash
python skills/examples/openai_converter.py > openai_functions.json
```

**Anthropic Claude:**
```bash
python skills/examples/anthropic_converter.py > anthropic_tools.json
```

**LangChain:**
```python
from skills.examples.langchain_agent import ArkimeSkillsAdapter

adapter = ArkimeSkillsAdapter()
tools = adapter.get_langchain_tools()
# Or filter by use case: adapter.get_tools_by_use_case("soc")
```

**Microsoft AutoGen:**
```python
from skills.examples.autogen_config import ArkimeAutoGenConfig

config = ArkimeAutoGenConfig()
llm_config = config.create_agent_config(use_case="threat_hunting")
```

See [`skills/examples/README.md`](skills/examples/README.md) for complete integration guides.

### Scenario Playbooks

Pre-built investigation workflows that chain multiple skills:

- **[SOC Alert Triage](skills/playbooks/alert_triage.md)** - Automated alert enrichment and triage
- **[Data Exfiltration Hunt](skills/playbooks/data_exfiltration_hunt.md)** - Proactive threat hunting for data theft
- **[Host Forensics](skills/playbooks/host_forensics.md)** - Comprehensive compromised host investigation
- **[DNS Tunnel Detection](skills/playbooks/dns_tunnel_detection.md)** - Detect DNS-based C2 and exfiltration

See [`skills/playbooks/README.md`](skills/playbooks/README.md) for usage examples.

### Application Scenarios

| Scenario | Key Skills | Playbook |
|----------|-----------|----------|
| SOC Automation | `search_sessions`, `add_tags`, `geo_summary` | [Alert Triage](skills/playbooks/alert_triage.md) |
| Threat Hunting | `dns_lookups`, `connections_graph`, `create_hunt`, `external_connections` | [Data Exfiltration Hunt](skills/playbooks/data_exfiltration_hunt.md) |
| Incident Response | `get_session_detail`, `unique_destinations`, `get_session_packets` | [Host Forensics](skills/playbooks/host_forensics.md) |
| Network Monitoring | `top_talkers`, `capture_status`, `get_stats` | - |
| Compliance & Audit | `external_connections`, `pcap_files`, `get_current_user` | - |
| Multi-cluster Ops | `get_parliament`, `capture_status` | - |

### Quick Start

**Load skills programmatically:**
```python
import yaml

with open("skills/arkime_skills.yaml") as f:
    manifest = yaml.safe_load(f)

skills = manifest["skills"]  # list of 29 skill definitions
```

**Validate skills manifest:**
```bash
python skills/tests/validate_skills.py
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
