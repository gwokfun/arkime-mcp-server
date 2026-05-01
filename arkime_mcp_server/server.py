"""
Arkime MCP Server - FastMCP implementation.

Provides MCP tools for Arkime full packet capture system.
"""

import sys
import json
import atexit
import threading
from typing import Any, Dict, Optional
from fastmcp import FastMCP

from .client import ArkimeClient, MAX_SESSION_LIMIT
from .config import Config
from .utils import format_bytes, format_timestamp, protocol_name, summarize_session

# Global variables for lazy initialization
_config = None
_client = None
_mcp = None
_init_lock = threading.Lock()


def _cleanup():
    """Cleanup resources on process exit."""
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass


atexit.register(_cleanup)


def get_config():
    """Get or initialize configuration."""
    global _config
    if _config is None:
        with _init_lock:
            if _config is None:
                try:
                    _config = Config()
                except ValueError as e:
                    print(f"Configuration error: {e}", file=sys.stderr)
                    sys.exit(1)
    return _config


def get_client():
    """Get or initialize Arkime client."""
    global _client
    if _client is None:
        with _init_lock:
            if _client is None:
                config = get_config()
                _client = ArkimeClient(
                    config.arkime_url, config.arkime_user, config.arkime_password
                )
    return _client


def get_mcp():
    """Get or initialize MCP server."""
    global _mcp
    if _mcp is None:
        with _init_lock:
            if _mcp is None:
                _mcp = FastMCP("arkime")
    return _mcp


# ── Session Search & Analysis Tools ──


@get_mcp().tool()
def search_sessions(
    expression: Optional[str] = None,
    hours: int = 1,
    limit: int = 50,
    order: Optional[str] = None,
) -> str:
    """
    Search Arkime sessions with optional filtering.

    Args:
        expression: Arkime search expression (e.g., 'ip.src==192.168.1.101', 'port.dst==443')
        hours: Time range in hours from now (use -1 for all available data)
        limit: Max sessions to return (1-200)
        order: Sort order as 'field:dir' (e.g., 'totDataBytes:desc')

    Returns:
        JSON string with session search results including IPs, ports, protocols, bytes, geo, and AS info
    """
    if not get_config().is_tool_enabled("search_sessions"):
        return json.dumps({"error": "Tool is disabled"})

    length = max(1, min(limit, MAX_SESSION_LIMIT))
    result = get_client().get_sessions(
        expression=expression, date=hours, length=length, order=order
    )

    sessions = [summarize_session(s) for s in result.get("data", [])]

    return json.dumps(
        {
            "total_matching": result.get("recordsFiltered", 0),
            "returned": len(sessions),
            "sessions": sessions,
        },
        indent=2,
    )


@get_mcp().tool()
def get_session_detail(node: str, session_id: str) -> str:
    """
    Get full detail for a single session.

    Args:
        node: Node name (from session search results)
        session_id: Session ID (from session search results)

    Returns:
        JSON string with full decoded protocol information for the session
    """
    if not get_config().is_tool_enabled("get_session_detail"):
        return json.dumps({"error": "Tool is disabled"})

    detail = get_client().get_session_detail(node, session_id)
    return json.dumps(detail, indent=2) if isinstance(detail, dict) else str(detail)


@get_mcp().tool()
def get_session_packets(node: str, session_id: str) -> str:
    """
    Get decoded packet data for a session.

    Args:
        node: Node name (from session search results)
        session_id: Session ID (from session search results)

    Returns:
        JSON string with decoded packet contents
    """
    if not get_config().is_tool_enabled("get_session_packets"):
        return json.dumps({"error": "Tool is disabled"})

    packets = get_client().get_session_packets(node, session_id)
    return json.dumps(packets, indent=2) if isinstance(packets, dict) else str(packets)


@get_mcp().tool()
def get_session_raw(node: str, session_id: str) -> str:
    """
    Get raw session data.

    Args:
        node: Node name (from session search results)
        session_id: Session ID (from session search results)

    Returns:
        Raw session data as string
    """
    if not get_config().is_tool_enabled("get_session_raw"):
        return "Tool is disabled"

    return str(get_client().get_session_raw(node, session_id))


# ── Network Investigation Tools ──


@get_mcp().tool()
def top_talkers(
    field: str = "source.ip",
    expression: Optional[str] = None,
    hours: int = 1,
    limit: int = 20,
) -> str:
    """
    Get top N values for a field by session count.

    Useful for finding the most active hosts, most-contacted destinations,
    busiest ports, or most queried domains.

    Args:
        field: Field to aggregate ('source.ip', 'destination.ip', 'destination.port', 'host.dns', 'http.uri')
        expression: Optional Arkime filter expression
        hours: Time range in hours from now
        limit: Number of top entries to return

    Returns:
        Newline-separated list of top values with session counts
    """
    if not get_config().is_tool_enabled("top_talkers"):
        return "Tool is disabled"

    return str(get_client().get_unique(exp=field, expression=expression, date=hours, length=limit))


@get_mcp().tool()
def connections_graph(
    expression: Optional[str] = None,
    hours: int = 1,
    src_field: str = "source.ip",
    dst_field: str = "ip.dst:port",
    limit: int = 50,
) -> str:
    """
    Get network connection graph showing who is talking to whom.

    Args:
        expression: Optional Arkime filter expression
        hours: Time range in hours from now
        src_field: Source field for graph
        dst_field: Destination field for graph
        limit: Max connections to return

    Returns:
        JSON string with nodes and links between sources and destinations with byte/packet/session counts
    """
    if not get_config().is_tool_enabled("connections_graph"):
        return json.dumps({"error": "Tool is disabled"})

    result = get_client().get_connections(
        expression=expression,
        date=hours,
        src_field=src_field,
        dst_field=dst_field,
        length=limit,
    )

    raw_nodes = result.get("nodes", [])
    nodes = [
        {
            "id": n.get("id"),
            "sessions": n.get("sessions", 0),
            "bytes": format_bytes(n.get("totDataBytes", 0)),
            "packets": n.get("network.packets", 0),
            "type": "source" if n.get("type") == 1 else "destination",
        }
        for n in raw_nodes
    ]

    raw_links = result.get("links", [])
    links = [
        {
            "source": raw_nodes[link.get("source", 0)].get("id", "?")
            if link.get("source", 0) < len(raw_nodes)
            else "?",
            "target": raw_nodes[link.get("target", 0)].get("id", "?")
            if link.get("target", 0) < len(raw_nodes)
            else "?",
            "sessions": link.get("value", 0),
            "bytes": format_bytes(link.get("totDataBytes", 0)),
        }
        for link in raw_links
    ]

    return json.dumps({"nodes": nodes, "links": links}, indent=2)


@get_mcp().tool()
def unique_destinations(source_ip: str, hours: int = 1, limit: int = 50) -> str:
    """
    List distinct external destination IPs contacted by an internal host.

    Useful for answering 'what is this device talking to?'

    Args:
        source_ip: Internal IP address to investigate
        hours: Time range in hours from now
        limit: Max destinations to return

    Returns:
        Newline-separated list of external IPs contacted
    """
    if not get_config().is_tool_enabled("unique_destinations"):
        return "Tool is disabled"

    expr = (
        f"ip.src=={source_ip} && ip.dst!=10.0.0.0/8 && "
        f"ip.dst!=192.168.0.0/16 && ip.dst!=172.16.0.0/12"
    )
    return str(
        get_client().get_unique(exp="destination.ip", expression=expr, date=hours, length=limit)
    )


@get_mcp().tool()
def dns_lookups(
    domain: Optional[str] = None,
    source_ip: Optional[str] = None,
    hours: int = 1,
    limit: int = 30,
) -> str:
    """
    Search DNS queries captured in network traffic.

    Filter by domain name pattern or source IP to see what a device is resolving.

    Args:
        domain: Domain to search for (supports wildcards like '*.example.com')
        source_ip: Only show DNS queries from this source IP
        hours: Time range in hours from now
        limit: Max results to return

    Returns:
        Newline-separated list of DNS queries with counts
    """
    if not get_config().is_tool_enabled("dns_lookups"):
        return "Tool is disabled"

    parts = []
    if domain:
        parts.append(f"host.dns=={domain}")
    if source_ip:
        parts.append(f"ip.src=={source_ip}")

    expr = " && ".join(parts) if parts else None
    return str(get_client().get_unique(exp="host.dns", expression=expr, date=hours, length=limit))


@get_mcp().tool()
def reverse_dns(ip: str) -> str:
    """
    Get PTR/reverse DNS records for an IP address.

    Args:
        ip: IP address to look up

    Returns:
        JSON string with reverse DNS information
    """
    if not get_config().is_tool_enabled("reverse_dns"):
        return json.dumps({"error": "Tool is disabled"})

    result = get_client().get_reverse_dns(ip)
    return json.dumps(result, indent=2) if isinstance(result, dict) else str(result)


# ── Security & Anomaly Tools ──


@get_mcp().tool()
def external_connections(
    source_ip: Optional[str] = None, hours: int = 1, limit: int = 50
) -> str:
    """
    Find sessions going to external (non-RFC1918) destinations.

    Useful for seeing what traffic is leaving your network.

    Args:
        source_ip: Internal IP to filter on (omit for all internal hosts)
        hours: Time range in hours from now
        limit: Max sessions to return

    Returns:
        JSON string with external connections sorted by bytes
    """
    if not get_config().is_tool_enabled("external_connections"):
        return json.dumps({"error": "Tool is disabled"})

    parts = [
        "ip.dst!=10.0.0.0/8",
        "ip.dst!=192.168.0.0/16",
        "ip.dst!=172.16.0.0/12",
        "ip.dst!=224.0.0.0/4",
        "ip.dst!=255.255.255.255",
    ]
    if source_ip:
        parts.append(f"ip.src=={source_ip}")

    expr = " && ".join(parts)
    result = get_client().get_sessions(
        expression=expr, date=hours, length=limit, order="totDataBytes:desc"
    )

    sessions = [summarize_session(s) for s in result.get("data", [])]

    return json.dumps(
        {
            "total_matching": result.get("recordsFiltered", 0),
            "returned": len(sessions),
            "sessions": sessions,
        },
        indent=2,
    )


@get_mcp().tool()
def geo_summary(expression: Optional[str] = None, hours: int = 1, limit: int = 30) -> str:
    """
    Breakdown of destination traffic by country.

    Highlights where your traffic is going geographically.

    Args:
        expression: Optional Arkime filter expression
        hours: Time range in hours from now
        limit: Max countries to return

    Returns:
        Newline-separated list of countries with session counts
    """
    if not get_config().is_tool_enabled("geo_summary"):
        return "Tool is disabled"

    return str(
        get_client().get_unique(
            exp="destination.geo.country_iso_code",
            expression=expression,
            date=hours,
            length=limit,
        )
    )


# ── System Health & Info Tools ──


@get_mcp().tool()
def capture_status() -> str:
    """
    Get current Arkime capture health.

    Returns:
        JSON string with cluster status, node count, shard health, and OpenSearch version
    """
    if not get_config().is_tool_enabled("capture_status"):
        return json.dumps({"error": "Tool is disabled"})

    health = get_client().get_es_health()
    return json.dumps(
        {
            "cluster": health.get("cluster_name"),
            "status": health.get("status"),
            "nodes": health.get("number_of_nodes"),
            "active_shards": health.get("active_shards"),
            "unassigned_shards": health.get("unassigned_shards"),
            "opensearch_version": health.get("version"),
            "arkime_db_version": health.get("molochDbVersion"),
        },
        indent=2,
    )


@get_mcp().tool()
def pcap_files(limit: int = 20) -> str:
    """
    List PCAP capture files with sizes, packet counts, and time ranges.

    Args:
        limit: Max files to return

    Returns:
        JSON string with PCAP file information
    """
    if not get_config().is_tool_enabled("pcap_files"):
        return json.dumps({"error": "Tool is disabled"})

    result = get_client().get_files(length=limit)
    files = [
        {
            "name": str(f.get("name", "")).split("/")[-1],
            "size": format_bytes(f.get("filesize", 0)),
            "packets": f.get("packets", 0),
            "compression": f.get("compression", "none"),
            "ratio": f"{f.get('cratio', 0):.1f}x",
            "first": format_timestamp(f.get("first")),
            "last": format_timestamp(f.get("lastTimestamp")),
        }
        for f in result.get("data", [])
    ]

    return json.dumps({"total_files": result.get("recordsTotal", 0), "files": files}, indent=2)


@get_mcp().tool()
def list_fields(group: Optional[str] = None) -> str:
    """
    List available Arkime session fields for use in search expressions.

    Args:
        group: Filter by field group (e.g., 'dns', 'http', 'email', 'general')

    Returns:
        JSON string with available fields and their metadata
    """
    if not get_config().is_tool_enabled("list_fields"):
        return json.dumps({"error": "Tool is disabled"})

    fields = get_client().get_fields()
    filtered = [
        {
            "expression": f.get("exp"),
            "name": f.get("friendlyName"),
            "type": f.get("type"),
            "group": f.get("group"),
        }
        for f in fields
        if not group or f.get("group") == group
    ]

    return json.dumps(filtered, indent=2)


@get_mcp().tool()
def get_field_values(field: str, expression: Optional[str] = None) -> str:
    """
    Get possible values for a specific field.

    Args:
        field: Field name to get values for
        expression: Optional filter expression

    Returns:
        JSON string with possible field values
    """
    if not get_config().is_tool_enabled("get_field_values"):
        return json.dumps({"error": "Tool is disabled"})

    values = get_client().get_field_values(field, expression)
    return json.dumps(values, indent=2)


# ── User & Settings Tools ──


@get_mcp().tool()
def get_current_user() -> str:
    """
    Get information about the current authenticated user.

    Returns:
        JSON string with user information
    """
    if not get_config().is_tool_enabled("get_current_user"):
        return json.dumps({"error": "Tool is disabled"})

    user = get_client().get_current_user()
    return json.dumps(user, indent=2)


@get_mcp().tool()
def get_settings() -> str:
    """
    Get Arkime viewer settings.

    Returns:
        JSON string with viewer settings
    """
    if not get_config().is_tool_enabled("get_settings"):
        return json.dumps({"error": "Tool is disabled"})

    settings = get_client().get_settings()
    return json.dumps(settings, indent=2)


# ── Tags & Annotations Tools ──


@get_mcp().tool()
def add_tags(tags: str, node: str, session_id: str, segments: str = "all") -> str:
    """
    Add tags to a session.

    Args:
        tags: Comma-separated list of tags to add
        node: Node name (from session search results)
        session_id: Session ID (from session search results)
        segments: Which segments to tag ('all', 'src', 'dst')

    Returns:
        JSON string with success message
    """
    if not get_config().is_tool_enabled("add_tags"):
        return json.dumps({"error": "Tool is disabled"})

    result = get_client().add_tags(tags, node, session_id, segments)
    return json.dumps(result, indent=2)


@get_mcp().tool()
def remove_tags(tags: str, node: str, session_id: str, segments: str = "all") -> str:
    """
    Remove tags from a session.

    Args:
        tags: Comma-separated list of tags to remove
        node: Node name (from session search results)
        session_id: Session ID (from session search results)
        segments: Which segments to remove tags from ('all', 'src', 'dst')

    Returns:
        JSON string with success message
    """
    if not get_config().is_tool_enabled("remove_tags"):
        return json.dumps({"error": "Tool is disabled"})

    result = get_client().remove_tags(tags, node, session_id, segments)
    return json.dumps(result, indent=2)


# ── Statistics Tools ──


@get_mcp().tool()
def get_stats() -> str:
    """
    Get Arkime statistics.

    Returns:
        JSON string with Arkime statistics
    """
    if not get_config().is_tool_enabled("get_stats"):
        return json.dumps({"error": "Tool is disabled"})

    stats = get_client().get_stats()
    return json.dumps(stats, indent=2)


@get_mcp().tool()
def get_es_stats() -> str:
    """
    Get Elasticsearch/OpenSearch indices statistics.

    Returns:
        JSON string with index statistics
    """
    if not get_config().is_tool_enabled("get_es_stats"):
        return json.dumps({"error": "Tool is disabled"})

    stats = get_client().get_es_indices()
    return json.dumps(stats, indent=2)


# ── Hunt Tools ──


@get_mcp().tool()
def create_hunt(
    name: str,
    search: str,
    hunt_type: str = "raw",
    src: bool = True,
    dst: bool = True,
) -> str:
    """
    Create a hunt job to search packet payloads.

    Args:
        name: Hunt name
        search: Search string or regex to hunt for
        hunt_type: Type of hunt ('raw', 'reassembled', 'both')
        src: Search source packets
        dst: Search destination packets

    Returns:
        JSON string with hunt creation result
    """
    if not get_config().is_tool_enabled("create_hunt"):
        return json.dumps({"error": "Tool is disabled"})

    result = get_client().create_hunt(name, search, hunt_type, src, dst)
    return json.dumps(result, indent=2)


@get_mcp().tool()
def get_hunts() -> str:
    """
    Get list of hunt jobs.

    Returns:
        JSON string with list of hunts
    """
    if not get_config().is_tool_enabled("get_hunts"):
        return json.dumps({"error": "Tool is disabled"})

    hunts = get_client().get_hunts()
    return json.dumps(hunts, indent=2)


@get_mcp().tool()
def delete_hunt(hunt_id: str) -> str:
    """
    Delete a hunt job.

    Args:
        hunt_id: Hunt ID to delete

    Returns:
        JSON string with deletion result
    """
    if not get_config().is_tool_enabled("delete_hunt"):
        return json.dumps({"error": "Tool is disabled"})

    result = get_client().delete_hunt(hunt_id)
    return json.dumps(result, indent=2)


# ── View Tools ──


@get_mcp().tool()
def create_view(name: str, expression: str) -> str:
    """
    Create a saved view (search query).

    Args:
        name: View name
        expression: Arkime search expression to save

    Returns:
        JSON string with view creation result
    """
    if not get_config().is_tool_enabled("create_view"):
        return json.dumps({"error": "Tool is disabled"})

    result = get_client().create_view(name, expression)
    return json.dumps(result, indent=2)


@get_mcp().tool()
def get_views() -> str:
    """
    Get list of saved views.

    Returns:
        JSON string with list of views
    """
    if not get_config().is_tool_enabled("get_views"):
        return json.dumps({"error": "Tool is disabled"})

    views = get_client().get_views()
    return json.dumps(views, indent=2)


@get_mcp().tool()
def delete_view(view_id: str) -> str:
    """
    Delete a saved view.

    Args:
        view_id: View ID to delete

    Returns:
        JSON string with deletion result
    """
    if not get_config().is_tool_enabled("delete_view"):
        return json.dumps({"error": "Tool is disabled"})

    result = get_client().delete_view(view_id)
    return json.dumps(result, indent=2)


# ── Notifier Tools ──


@get_mcp().tool()
def get_notifiers() -> str:
    """
    Get list of configured notifiers.

    Returns:
        JSON string with list of notifiers
    """
    if not get_config().is_tool_enabled("get_notifiers"):
        return json.dumps({"error": "Tool is disabled"})

    notifiers = get_client().get_notifiers()
    return json.dumps(notifiers, indent=2)


# ── Parliament (Multi-cluster) Tools ──


@get_mcp().tool()
def get_parliament() -> str:
    """
    Get parliament (multi-cluster) information.

    Returns:
        JSON string with parliament configuration and cluster status
    """
    if not get_config().is_tool_enabled("get_parliament"):
        return json.dumps({"error": "Tool is disabled"})

    parliament = get_client().get_parliament()
    return json.dumps(parliament, indent=2)


# ── Main entry point ──


def main():
    """Main entry point for the MCP server."""
    get_mcp().run()


if __name__ == "__main__":
    main()
