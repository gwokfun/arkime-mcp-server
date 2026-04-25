"""
Unit tests for utils module.
"""

import pytest
from datetime import datetime
from arkime_mcp_server.utils import (
    format_bytes,
    format_timestamp,
    protocol_name,
    summarize_session,
)


class TestFormatBytes:
    """Tests for format_bytes function."""

    def test_zero_bytes(self):
        """Test formatting zero bytes."""
        assert format_bytes(0) == "0 B"
        assert format_bytes(None) == "0 B"

    def test_bytes(self):
        """Test formatting bytes."""
        assert format_bytes(100) == "100.0 B"
        assert format_bytes(512) == "512.0 B"

    def test_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(2048) == "2.0 KB"
        assert format_bytes(1536) == "1.5 KB"

    def test_megabytes(self):
        """Test formatting megabytes."""
        assert format_bytes(1048576) == "1.0 MB"
        assert format_bytes(2097152) == "2.0 MB"
        assert format_bytes(5242880) == "5.0 MB"

    def test_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_bytes(1073741824) == "1.0 GB"
        assert format_bytes(2147483648) == "2.0 GB"

    def test_terabytes(self):
        """Test formatting terabytes."""
        assert format_bytes(1099511627776) == "1.0 TB"

    def test_petabytes(self):
        """Test formatting petabytes."""
        assert format_bytes(1125899906842624) == "1.0 PB"


class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_none_timestamp(self):
        """Test formatting None timestamp."""
        assert format_timestamp(None) == "—"

    def test_zero_timestamp(self):
        """Test formatting zero timestamp."""
        assert format_timestamp(0) == "—"

    def test_valid_timestamp(self):
        """Test formatting valid timestamps."""
        # 2001-09-09 01:46:40 UTC = 1000000000000 milliseconds
        result = format_timestamp(1000000000000)
        assert result != "—"
        assert "2001-09-09" in result
        assert "UTC" in result

    def test_recent_timestamp(self):
        """Test formatting recent timestamp."""
        # Current time in milliseconds
        now_ms = int(datetime.now().timestamp() * 1000)
        result = format_timestamp(now_ms)
        assert result != "—"
        assert "UTC" in result


class TestProtocolName:
    """Tests for protocol_name function."""

    def test_tcp(self):
        """Test TCP protocol."""
        assert protocol_name(6) == "TCP"

    def test_udp(self):
        """Test UDP protocol."""
        assert protocol_name(17) == "UDP"

    def test_icmp(self):
        """Test ICMP protocol."""
        assert protocol_name(1) == "ICMP"

    def test_unknown_protocol(self):
        """Test unknown protocol number."""
        assert protocol_name(99) == "99"

    def test_none_protocol(self):
        """Test None protocol."""
        assert protocol_name(None) == "?"


class TestSummarizeSession:
    """Tests for summarize_session function."""

    def test_basic_session(self):
        """Test summarizing a basic session."""
        session = {
            "id": "test-id-123",
            "node": "node1",
            "ipProtocol": 6,
            "source": {
                "ip": "192.168.1.100",
                "port": 54321,
                "geo": {"country_iso_code": "US"},
                "as": {"full": "AS12345 Example ISP"},
            },
            "destination": {
                "ip": "8.8.8.8",
                "port": 443,
                "geo": {"country_iso_code": "US"},
                "as": {"full": "AS15169 Google LLC"},
            },
            "totDataBytes": 1024,
            "network": {"packets": 10},
            "firstPacket": 1000000000000,
            "lastPacket": 1000000001000,
        }

        result = summarize_session(session)

        assert result["id"] == "test-id-123"
        assert result["node"] == "node1"
        assert result["protocol"] == "TCP"
        assert result["source"] == "192.168.1.100:54321"
        assert result["destination"] == "8.8.8.8:443"
        assert result["source_geo"] == "US"
        assert result["destination_geo"] == "US"
        assert result["bytes"] == "1.0 KB"
        assert result["packets"] == 10

    def test_minimal_session(self):
        """Test summarizing session with minimal data."""
        session = {}
        result = summarize_session(session)

        assert result["id"] is None
        assert result["node"] is None
        assert result["protocol"] == "?"
        assert result["source"] == "?:?"
        assert result["destination"] == "?:?"
        assert result["source_geo"] == ""
        assert result["destination_geo"] == ""
        assert result["bytes"] == "0 B"
        assert result["packets"] == 0

    def test_partial_session(self):
        """Test summarizing session with partial data."""
        session = {
            "id": "partial-123",
            "ipProtocol": 17,
            "source": {"ip": "10.0.0.1"},
            "destination": {"port": 53},
        }

        result = summarize_session(session)

        assert result["id"] == "partial-123"
        assert result["protocol"] == "UDP"
        assert result["source"] == "10.0.0.1:?"
        assert result["destination"] == "?:53"
