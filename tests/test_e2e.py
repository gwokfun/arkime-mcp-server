"""
End-to-end tests for Arkime MCP Server.

Tests the full MCP server functionality with mocked Arkime backend.
These tests verify that tools work correctly when invoked through the server.
"""

import json
import pytest
from unittest.mock import Mock, patch

# Import server module to get tools
from arkime_mcp_server import server


@pytest.fixture
def mock_arkime_client():
    """Provide a fully mocked Arkime client for E2E testing."""
    client = Mock()

    # Mock session search responses
    client.get_sessions.return_value = {
        "data": [
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
                "destination.as.full": "AS15169 Google LLC",
            }
        ],
        "recordsFiltered": 1,
        "recordsTotal": 100,
    }

    # Mock session detail
    client.get_session_detail.return_value = {
        "node": "test-node",
        "id": "session123",
        "http": {"uri": ["/api/data"], "method": ["GET"]},
        "dns": {"host": ["example.com"]},
    }

    # Mock session packets
    client.get_session_packets.return_value = {
        "packets": [
            {"index": 0, "data": "packet_data_0"},
            {"index": 1, "data": "packet_data_1"},
        ]
    }

    # Mock session raw data
    client.get_session_raw.return_value = "raw_pcap_data_here"

    # Mock unique values
    client.get_unique.return_value = "192.168.1.100: 10\n192.168.1.101: 5\n8.8.8.8: 3"

    # Mock connections graph
    client.get_connections.return_value = {
        "nodes": [
            {"id": "192.168.1.100", "sessions": 10, "totDataBytes": 50000, "network.packets": 100, "type": 1},
            {"id": "8.8.8.8", "sessions": 5, "totDataBytes": 30000, "network.packets": 60, "type": 2},
        ],
        "links": [
            {"source": 0, "target": 1, "value": 5, "totDataBytes": 30000},
        ],
    }

    # Mock reverse DNS
    client.get_reverse_dns.return_value = {
        "ip": "8.8.8.8",
        "ptr": ["dns.google"],
    }

    # Mock ES health
    client.get_es_health.return_value = {
        "cluster_name": "arkime-cluster",
        "status": "green",
        "number_of_nodes": 3,
        "active_shards": 10,
        "unassigned_shards": 0,
        "version": "7.10.2",
        "molochDbVersion": 73,
    }

    # Mock files
    client.get_files.return_value = {
        "data": [
            {
                "name": "/pcap/capture1.pcap",
                "filesize": 1024000,
                "packets": 1000,
                "compression": "gzip",
                "cratio": 2.5,
                "first": 1609459200000,
                "lastTimestamp": 1609462800000,
            }
        ],
        "recordsTotal": 1,
    }

    # Mock fields
    client.get_fields.return_value = [
        {"exp": "source.ip", "friendlyName": "Source IP", "type": "ip", "group": "general"},
        {"exp": "destination.ip", "friendlyName": "Destination IP", "type": "ip", "group": "general"},
        {"exp": "http.uri", "friendlyName": "HTTP URI", "type": "termfield", "group": "http"},
    ]

    # Mock field values
    client.get_field_values.return_value = ["value1", "value2", "value3"]

    # Mock user info
    client.get_current_user.return_value = {
        "userId": "mcp",
        "userName": "MCP User",
        "enabled": True,
        "createEnabled": True,
    }

    # Mock settings
    client.get_settings.return_value = {
        "timezone": "UTC",
        "ms": False,
    }

    # Mock tags operations
    client.add_tags.return_value = {"success": True, "text": "Tags added"}
    client.remove_tags.return_value = {"success": True, "text": "Tags removed"}

    # Mock stats
    client.get_stats.return_value = {
        "totalPackets": 1000000,
        "totalSessions": 50000,
        "totalBytes": 1073741824,
    }

    # Mock ES indices
    client.get_es_indices.return_value = {
        "indices": [
            {"name": "sessions2-210101", "docs": 10000, "size": "100MB"},
        ]
    }

    # Mock hunt operations
    client.create_hunt.return_value = {"success": True, "huntId": "hunt123"}
    client.get_hunts.return_value = [
        {"id": "hunt123", "name": "Test Hunt", "status": "running"},
    ]
    client.delete_hunt.return_value = {"success": True}

    # Mock view operations
    client.create_view.return_value = {"success": True, "viewId": "view123"}
    client.get_views.return_value = [
        {"id": "view123", "name": "Test View", "expression": "ip.src==192.168.1.1"},
    ]
    client.delete_view.return_value = {"success": True}

    # Mock notifiers
    client.get_notifiers.return_value = [
        {"id": "notifier1", "name": "Email Notifier", "type": "email"},
    ]

    # Mock parliament
    client.get_parliament.return_value = {
        "clusters": [
            {"name": "cluster1", "url": "http://cluster1:8005"},
        ]
    }

    return client


@pytest.fixture
def mock_config():
    """Provide a mock configuration with all tools enabled."""
    config = Mock()
    config.arkime_url = "http://test-arkime:8005"
    config.arkime_user = "test_user"
    config.arkime_password = "test_password"
    config.is_tool_enabled.return_value = True
    return config


class TestE2ESessionSearchTools:
    """Test session search and analysis tools end-to-end."""

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_search_sessions(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test search_sessions tool returns properly formatted results."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.search_sessions(expression="ip.src==192.168.1.100", hours=1, limit=50)
        result_data = json.loads(result)

        assert "total_matching" in result_data
        assert "returned" in result_data
        assert "sessions" in result_data
        assert result_data["total_matching"] == 1
        assert result_data["returned"] == 1
        assert len(result_data["sessions"]) == 1

        # Verify session structure
        session = result_data["sessions"][0]
        assert "node" in session
        assert "id" in session
        assert "source" in session
        assert "destination" in session
        assert "192.168.1.100" in session["source"]
        assert "8.8.8.8" in session["destination"]

        mock_arkime_client.get_sessions.assert_called_once()

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_search_sessions_respects_limit(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test search_sessions respects max limit."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        # Try to request more than MAX_SESSION_LIMIT (200)
        result = server.search_sessions(limit=500)

        # Should clamp to 200
        call_args = mock_arkime_client.get_sessions.call_args
        assert call_args[1]["length"] == 200

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_get_session_detail(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test get_session_detail returns full session information."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.get_session_detail(node="test-node", session_id="session123")
        result_data = json.loads(result)

        assert "node" in result_data
        assert "id" in result_data
        assert "http" in result_data
        assert result_data["node"] == "test-node"
        assert result_data["id"] == "session123"

        mock_arkime_client.get_session_detail.assert_called_once_with("test-node", "session123")

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_get_session_packets(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test get_session_packets returns packet data."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.get_session_packets(node="test-node", session_id="session123")
        result_data = json.loads(result)

        assert "packets" in result_data
        assert len(result_data["packets"]) == 2

        mock_arkime_client.get_session_packets.assert_called_once_with("test-node", "session123")

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_get_session_raw(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test get_session_raw returns raw data."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.get_session_raw(node="test-node", session_id="session123")

        assert "raw_pcap_data_here" in result

        mock_arkime_client.get_session_raw.assert_called_once_with("test-node", "session123")


class TestE2ENetworkInvestigationTools:
    """Test network investigation tools end-to-end."""

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_top_talkers(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test top_talkers returns aggregated results."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.top_talkers(field="source.ip", hours=1, limit=20)

        assert "192.168.1.100: 10" in result
        assert "192.168.1.101: 5" in result

        mock_arkime_client.get_unique.assert_called_once()
        call_args = mock_arkime_client.get_unique.call_args
        assert call_args[1]["exp"] == "source.ip"
        assert call_args[1]["length"] == 20

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_connections_graph(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test connections_graph returns network graph structure."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.connections_graph(hours=1, limit=50)
        result_data = json.loads(result)

        assert "nodes" in result_data
        assert "links" in result_data
        assert len(result_data["nodes"]) == 2
        assert len(result_data["links"]) == 1

        # Verify node structure
        node = result_data["nodes"][0]
        assert "id" in node
        assert "sessions" in node
        assert "bytes" in node
        assert "type" in node

        # Verify link structure
        link = result_data["links"][0]
        assert "source" in link
        assert "target" in link
        assert "sessions" in link

        mock_arkime_client.get_connections.assert_called_once()

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_unique_destinations(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test unique_destinations filters RFC1918 addresses."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.unique_destinations(source_ip="192.168.1.100", hours=1, limit=50)

        assert isinstance(result, str)

        # Verify the expression filters private IPs
        call_args = mock_arkime_client.get_unique.call_args
        expression = call_args[1]["expression"]
        assert "ip.src==192.168.1.100" in expression
        assert "ip.dst!=10.0.0.0/8" in expression
        assert "ip.dst!=192.168.0.0/16" in expression
        assert "ip.dst!=172.16.0.0/12" in expression

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_dns_lookups(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test dns_lookups with domain and source IP filters."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.dns_lookups(domain="example.com", source_ip="192.168.1.100", hours=1)

        assert isinstance(result, str)

        call_args = mock_arkime_client.get_unique.call_args
        assert call_args[1]["exp"] == "host.dns"
        expression = call_args[1]["expression"]
        assert "host.dns==example.com" in expression
        assert "ip.src==192.168.1.100" in expression

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_reverse_dns(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test reverse_dns lookup."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.reverse_dns(ip="8.8.8.8")
        result_data = json.loads(result)

        assert "ip" in result_data
        assert "ptr" in result_data
        assert result_data["ip"] == "8.8.8.8"

        mock_arkime_client.get_reverse_dns.assert_called_once_with("8.8.8.8")


class TestE2ESecurityAndHealthTools:
    """Test security, anomaly detection, and system health tools."""

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_external_connections(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test external_connections filters RFC1918 addresses."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.external_connections(source_ip="192.168.1.100", hours=1, limit=50)
        result_data = json.loads(result)

        assert "total_matching" in result_data
        assert "sessions" in result_data

        # Verify the expression filters private IPs
        call_args = mock_arkime_client.get_sessions.call_args
        expression = call_args[1]["expression"]
        assert "ip.dst!=10.0.0.0/8" in expression
        assert "ip.dst!=192.168.0.0/16" in expression
        assert "ip.src==192.168.1.100" in expression

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_geo_summary(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test geo_summary aggregates by country."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.geo_summary(hours=1, limit=30)

        assert isinstance(result, str)

        call_args = mock_arkime_client.get_unique.call_args
        assert call_args[1]["exp"] == "destination.geo.country_iso_code"

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_capture_status(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test capture_status returns cluster health."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.capture_status()
        result_data = json.loads(result)

        assert "cluster" in result_data
        assert "status" in result_data
        assert "nodes" in result_data
        assert result_data["status"] == "green"
        assert result_data["nodes"] == 3

        mock_arkime_client.get_es_health.assert_called_once()

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_pcap_files(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test pcap_files returns file metadata."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.pcap_files(limit=20)
        result_data = json.loads(result)

        assert "total_files" in result_data
        assert "files" in result_data
        assert len(result_data["files"]) == 1

        file_info = result_data["files"][0]
        assert "name" in file_info
        assert "size" in file_info
        assert "packets" in file_info
        assert file_info["packets"] == 1000

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_list_fields(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test list_fields returns available fields."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.list_fields()
        result_data = json.loads(result)

        assert len(result_data) == 3
        assert result_data[0]["expression"] == "source.ip"
        assert result_data[1]["expression"] == "destination.ip"

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_list_fields_with_group_filter(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test list_fields with group filter."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.list_fields(group="http")
        result_data = json.loads(result)

        assert len(result_data) == 1
        assert result_data[0]["expression"] == "http.uri"
        assert result_data[0]["group"] == "http"

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_get_field_values(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test get_field_values returns possible values."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.get_field_values(field="http.method")
        result_data = json.loads(result)

        assert isinstance(result_data, list)
        assert len(result_data) == 3

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_get_current_user(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test get_current_user returns user info."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.get_current_user()
        result_data = json.loads(result)

        assert "userId" in result_data
        assert "enabled" in result_data
        assert result_data["userId"] == "mcp"

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_get_settings(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test get_settings returns viewer settings."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.get_settings()
        result_data = json.loads(result)

        assert "timezone" in result_data
        assert result_data["timezone"] == "UTC"

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_get_stats(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test get_stats returns statistics."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.get_stats()
        result_data = json.loads(result)

        assert "totalPackets" in result_data
        assert result_data["totalPackets"] == 1000000

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_get_es_stats(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test get_es_stats returns index statistics."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.get_es_stats()
        result_data = json.loads(result)

        assert "indices" in result_data
        assert len(result_data["indices"]) == 1


class TestE2ETagsHuntsViewsTools:
    """Test tags, hunts, views, and advanced tools."""

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_add_tags(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test add_tags operation."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.add_tags(tags="suspicious,malware", node="test-node", session_id="session123")
        result_data = json.loads(result)

        assert "success" in result_data
        assert result_data["success"] is True

        mock_arkime_client.add_tags.assert_called_once_with("suspicious,malware", "test-node", "session123", "all")

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_remove_tags(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test remove_tags operation."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.remove_tags(tags="false-positive", node="test-node", session_id="session123")
        result_data = json.loads(result)

        assert "success" in result_data
        assert result_data["success"] is True

        mock_arkime_client.remove_tags.assert_called_once()

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_create_hunt(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test create_hunt operation."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.create_hunt(name="Test Hunt", search="malware_signature", hunt_type="raw")
        result_data = json.loads(result)

        assert "success" in result_data
        assert "huntId" in result_data
        assert result_data["huntId"] == "hunt123"

        mock_arkime_client.create_hunt.assert_called_once()

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_get_hunts(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test get_hunts returns list of hunts."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.get_hunts()
        result_data = json.loads(result)

        assert isinstance(result_data, list)
        assert len(result_data) == 1
        assert result_data[0]["id"] == "hunt123"

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_delete_hunt(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test delete_hunt operation."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.delete_hunt(hunt_id="hunt123")
        result_data = json.loads(result)

        assert "success" in result_data
        assert result_data["success"] is True

        mock_arkime_client.delete_hunt.assert_called_once_with("hunt123")

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_create_view(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test create_view operation."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.create_view(name="Test View", expression="ip.src==192.168.1.1")
        result_data = json.loads(result)

        assert "success" in result_data
        assert "viewId" in result_data

        mock_arkime_client.create_view.assert_called_once()

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_get_views(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test get_views returns list of views."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.get_views()
        result_data = json.loads(result)

        assert isinstance(result_data, list)
        assert len(result_data) == 1
        assert result_data[0]["expression"] == "ip.src==192.168.1.1"

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_delete_view(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test delete_view operation."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.delete_view(view_id="view123")
        result_data = json.loads(result)

        assert "success" in result_data

        mock_arkime_client.delete_view.assert_called_once_with("view123")

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_get_notifiers(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test get_notifiers returns notifier list."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.get_notifiers()
        result_data = json.loads(result)

        assert isinstance(result_data, list)
        assert len(result_data) == 1
        assert result_data[0]["type"] == "email"

    @patch("arkime_mcp_server.server.get_client")
    @patch("arkime_mcp_server.server.get_config")
    def test_get_parliament(self, mock_get_config, mock_get_client, mock_config, mock_arkime_client):
        """Test get_parliament returns cluster info."""
        mock_get_config.return_value = mock_config
        mock_get_client.return_value = mock_arkime_client

        result = server.get_parliament()
        result_data = json.loads(result)

        assert "clusters" in result_data
        assert len(result_data["clusters"]) == 1


class TestE2EToolConfiguration:
    """Test tool enable/disable configuration."""

    @patch("arkime_mcp_server.server.get_config")
    def test_disabled_tool_returns_error(self, mock_get_config):
        """Test that disabled tools return error message."""
        mock_config = Mock()
        mock_config.is_tool_enabled.return_value = False
        mock_get_config.return_value = mock_config

        result = server.search_sessions()
        result_data = json.loads(result)

        assert "error" in result_data
        assert result_data["error"] == "Tool is disabled"

    @patch("arkime_mcp_server.server.get_config")
    def test_disabled_tool_text_response(self, mock_get_config):
        """Test that text-returning disabled tools return error string."""
        mock_config = Mock()
        mock_config.is_tool_enabled.return_value = False
        mock_get_config.return_value = mock_config

        result = server.top_talkers()

        assert result == "Tool is disabled"
