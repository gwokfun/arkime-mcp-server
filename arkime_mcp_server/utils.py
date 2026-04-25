"""
Utility functions for Arkime MCP Server.
"""

from datetime import datetime
from typing import Any, Dict, Optional


def format_timestamp(epoch_ms: Optional[int]) -> str:
    """
    Format Unix timestamp (milliseconds) to human-readable string.

    Args:
        epoch_ms: Unix timestamp in milliseconds

    Returns:
        Formatted timestamp string or "—" if None
    """
    if not epoch_ms:
        return "—"
    dt = datetime.fromtimestamp(epoch_ms / 1000.0)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def format_bytes(bytes_count: Optional[int]) -> str:
    """
    Format byte count to human-readable string with units.

    Args:
        bytes_count: Number of bytes

    Returns:
        Formatted byte string (e.g., "1.5 MB")
    """
    if not bytes_count:
        return "0 B"

    val = float(bytes_count)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(val) < 1024:
            return f"{val:.1f} {unit}"
        val /= 1024.0

    return f"{val:.1f} PB"


def protocol_name(proto_num: Optional[int]) -> str:
    """
    Convert IP protocol number to name.

    Args:
        proto_num: IP protocol number

    Returns:
        Protocol name or number as string
    """
    proto_map = {1: "ICMP", 6: "TCP", 17: "UDP"}
    if proto_num is None:
        return "?"
    return proto_map.get(proto_num, str(proto_num))


def summarize_session(session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a summary of a session for display.

    Args:
        session: Full session data from Arkime

    Returns:
        Summarized session data
    """
    src = session.get("source", {})
    dst = session.get("destination", {})
    network = session.get("network", {})

    return {
        "id": session.get("id"),
        "node": session.get("node"),
        "protocol": protocol_name(session.get("ipProtocol")),
        "source": f"{src.get('ip', '?')}:{src.get('port', '?')}",
        "destination": f"{dst.get('ip', '?')}:{dst.get('port', '?')}",
        "source_geo": src.get("geo", {}).get("country_iso_code", ""),
        "destination_geo": dst.get("geo", {}).get("country_iso_code", ""),
        "source_as": src.get("as", {}).get("full", ""),
        "destination_as": dst.get("as", {}).get("full", ""),
        "bytes": format_bytes(session.get("totDataBytes", 0)),
        "packets": network.get("packets", 0),
        "first_packet": format_timestamp(session.get("firstPacket")),
        "last_packet": format_timestamp(session.get("lastPacket")),
    }
