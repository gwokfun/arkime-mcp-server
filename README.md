# arkime-mcp-server

An [MCP](https://modelcontextprotocol.io) server for [Arkime](https://arkime.com) full packet capture. Lets AI assistants search network sessions, investigate traffic patterns, and monitor capture health.

## Tools

| Tool | Description |
|------|-------------|
| `search_sessions` | Search sessions with Arkime expressions, returns source/dest IPs, ports, protocols, bytes, geo, and AS info |
| `get_session_detail` | Full decoded protocol detail for a single session |
| `get_session_packets` | Decoded packet data for a session |
| `top_talkers` | Top N values for any field by session count (hosts, ports, domains, etc.) |
| `connections_graph` | Network connection graph — nodes and links with byte/packet/session counts |
| `unique_destinations` | Distinct external IPs contacted by an internal host |
| `dns_lookups` | DNS queries captured in traffic, filterable by domain pattern or source IP |
| `reverse_dns` | PTR/reverse DNS lookup for an IP |
| `external_connections` | Sessions going to non-RFC1918 destinations, sorted by bytes |
| `geo_summary` | Destination traffic breakdown by country |
| `capture_status` | Arkime cluster health — node count, shard status, OpenSearch version |
| `pcap_files` | PCAP capture files with sizes, packet counts, and time ranges |
| `list_fields` | Available Arkime session fields for use in search expressions |

## Setup

```bash
npm install
npm run build
```

## Configuration

Set environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ARKIME_URL` | No | `http://192.168.5.176:8005` | Arkime viewer URL |
| `ARKIME_USER` | No | `mcp` | Arkime API username |
| `ARKIME_PASSWORD` | **Yes** | — | Arkime API password |

## Usage with Claude Code

Add to your MCP settings (e.g., `.mcp.json`):

```json
{
  "mcpServers": {
    "arkime": {
      "command": "node",
      "args": ["/path/to/arkime-mcp-server/build/index.js"],
      "env": {
        "ARKIME_PASSWORD": "your-password"
      }
    }
  }
}
```

## Authentication

Arkime uses HTTP Digest authentication. The server handles this via the [digest-fetch](https://www.npmjs.com/package/digest-fetch) library.

## License

MIT
