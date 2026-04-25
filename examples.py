#!/usr/bin/env python3
"""
Example usage of Arkime MCP Server with Claude Desktop.

This example shows how to configure and use the Arkime MCP Server.
"""

# Example 1: Basic usage with environment variables
# Set these in your environment or .env file:
# export ARKIME_URL="http://your-arkime-server:8005"
# export ARKIME_USER="your-username"
# export ARKIME_PASSWORD="your-password"

# Then run:
# python -m arkime_mcp_server.server

# Example 2: Using with Claude Desktop
# Add to your Claude Desktop config file:
# (macOS: ~/Library/Application Support/Claude/claude_desktop_config.json)
# (Windows: %APPDATA%/Claude/claude_desktop_config.json)
# (Linux: ~/.config/Claude/claude_desktop_config.json)

CLAUDE_DESKTOP_CONFIG = {
    "mcpServers": {
        "arkime": {
            "command": "python",
            "args": ["-m", "arkime_mcp_server.server"],
            "env": {
                "ARKIME_URL": "http://192.168.5.176:8005",
                "ARKIME_USER": "mcp",
                "ARKIME_PASSWORD": "your-password-here"
            }
        }
    }
}

# Example 3: Using with custom config file
# Create config.yaml:
"""
arkime:
  url: "http://your-arkime-server:8005"
  user: "your-username"

tools:
  # Disable specific tools if needed
  search_sessions: true
  get_session_detail: true
  create_hunt: false  # Disable hunt creation
  delete_hunt: false  # Disable hunt deletion
"""

# Example 4: Programmatic usage
"""
from arkime_mcp_server.client import ArkimeClient

# Create client
client = ArkimeClient(
    "http://your-arkime-server:8005",
    "username",
    "password"
)

# Search sessions
result = client.get_sessions(
    expression="ip.src==192.168.1.100",
    hours=24,
    limit=100
)

print(f"Found {result['recordsFiltered']} sessions")

# Get connection graph
connections = client.get_connections(
    expression="port.dst==443",
    hours=24
)

# Clean up
client.close()
"""

print("See comments in this file for usage examples!")
print("\nQuick Start:")
print("1. Copy .env.example to .env and fill in your Arkime credentials")
print("2. Run: python -m arkime_mcp_server.server")
print("3. Or add to Claude Desktop config (see examples above)")
