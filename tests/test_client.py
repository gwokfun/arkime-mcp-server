"""
Unit tests for client module.
"""

import pytest
import httpx
from unittest.mock import Mock, patch, MagicMock
from arkime_mcp_server.client import DigestAuth, ArkimeClient


class TestDigestAuth:
    """Tests for DigestAuth class."""

    def test_initialization(self):
        """Test DigestAuth initialization."""
        auth = DigestAuth("testuser", "testpass")
        assert auth.username == "testuser"
        assert auth.password == "testpass"
        assert auth._challenge is None

    def test_parse_challenge(self):
        """Test parsing WWW-Authenticate header."""
        auth = DigestAuth("testuser", "testpass")
        header = 'Digest realm="Arkime", nonce="abc123", qop="auth", algorithm="MD5"'
        challenge = auth._parse_challenge(header)

        assert challenge["realm"] == "Arkime"
        assert challenge["nonce"] == "abc123"
        assert challenge["qop"] == "auth"
        assert challenge["algorithm"] == "MD5"

    def test_parse_challenge_with_opaque(self):
        """Test parsing WWW-Authenticate header with opaque."""
        auth = DigestAuth("testuser", "testpass")
        header = 'Digest realm="Test", nonce="xyz789", opaque="opaque123"'
        challenge = auth._parse_challenge(header)

        assert challenge["realm"] == "Test"
        assert challenge["nonce"] == "xyz789"
        assert challenge["opaque"] == "opaque123"

    def test_build_digest_header_without_qop(self):
        """Test building digest header without qop."""
        auth = DigestAuth("testuser", "testpass")
        auth._challenge = {
            "realm": "TestRealm",
            "nonce": "testnonce",
            "algorithm": "MD5",
        }

        header = auth._build_digest_header("GET", "/api/test")

        assert "username=\"testuser\"" in header
        assert "realm=\"TestRealm\"" in header
        assert "nonce=\"testnonce\"" in header
        assert "uri=\"/api/test\"" in header
        assert "response=\"" in header
        assert "algorithm=MD5" in header

    def test_build_digest_header_with_qop(self):
        """Test building digest header with qop."""
        auth = DigestAuth("testuser", "testpass")
        auth._challenge = {
            "realm": "TestRealm",
            "nonce": "testnonce",
            "qop": "auth",
            "algorithm": "MD5",
        }

        header = auth._build_digest_header("GET", "/api/test")

        assert "username=\"testuser\"" in header
        assert "qop=auth" in header
        assert "nc=" in header
        assert "cnonce=\"" in header

    def test_build_digest_header_with_opaque(self):
        """Test building digest header with opaque."""
        auth = DigestAuth("testuser", "testpass")
        auth._challenge = {
            "realm": "TestRealm",
            "nonce": "testnonce",
            "algorithm": "MD5",
            "opaque": "opaque123",
        }

        header = auth._build_digest_header("GET", "/api/test")

        assert 'opaque="opaque123"' in header


class TestArkimeClient:
    """Tests for ArkimeClient class."""

    def test_initialization(self):
        """Test ArkimeClient initialization."""
        client = ArkimeClient("http://test.local:8005", "user", "pass")
        assert client.base_url == "http://test.local:8005"
        assert isinstance(client.auth, DigestAuth)
        assert client.auth.username == "user"
        assert client.auth.password == "pass"

    def test_initialization_strips_trailing_slash(self):
        """Test that trailing slashes are removed from base URL."""
        client = ArkimeClient("http://test.local:8005/", "user", "pass")
        assert client.base_url == "http://test.local:8005"

    def test_context_manager(self):
        """Test using client as context manager."""
        with ArkimeClient("http://test.local:8005", "user", "pass") as client:
            assert client is not None

    @patch("arkime_mcp_server.client.httpx.Client")
    def test_get_json_response(self, mock_client_class):
        """Test _get method with JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"test": "data"}

        mock_http_client = Mock()
        mock_http_client.get.return_value = mock_response
        mock_client_class.return_value = mock_http_client

        client = ArkimeClient("http://test.local:8005", "user", "pass")
        result = client._get("test/endpoint", {"param": "value"})

        assert result == {"test": "data"}
        mock_http_client.get.assert_called_once()

    @patch("arkime_mcp_server.client.httpx.Client")
    def test_get_text_response(self, mock_client_class):
        """Test _get method with text response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "plain text response"

        mock_http_client = Mock()
        mock_http_client.get.return_value = mock_response
        mock_client_class.return_value = mock_http_client

        client = ArkimeClient("http://test.local:8005", "user", "pass")
        result = client._get("test/endpoint")

        assert result == "plain text response"

    @patch("arkime_mcp_server.client.httpx.Client")
    def test_get_sessions(self, mock_client_class):
        """Test get_sessions method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "data": [],
            "recordsFiltered": 0,
        }

        mock_http_client = Mock()
        mock_http_client.get.return_value = mock_response
        mock_client_class.return_value = mock_http_client

        client = ArkimeClient("http://test.local:8005", "user", "pass")
        result = client.get_sessions(expression="ip.src==192.168.1.1", length=10)

        assert "data" in result
        assert "recordsFiltered" in result

    @patch("arkime_mcp_server.client.httpx.Client")
    def test_get_es_health(self, mock_client_class):
        """Test get_es_health method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "cluster_name": "test-cluster",
            "status": "green",
        }

        mock_http_client = Mock()
        mock_http_client.get.return_value = mock_response
        mock_client_class.return_value = mock_http_client

        client = ArkimeClient("http://test.local:8005", "user", "pass")
        result = client.get_es_health()

        assert result["cluster_name"] == "test-cluster"
        assert result["status"] == "green"

    @patch("arkime_mcp_server.client.httpx.Client")
    def test_get_connections(self, mock_client_class):
        """Test get_connections method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"nodes": [], "links": []}

        mock_http_client = Mock()
        mock_http_client.get.return_value = mock_response
        mock_client_class.return_value = mock_http_client

        client = ArkimeClient("http://test.local:8005", "user", "pass")
        result = client.get_connections(
            expression="port.dst==443",
            src_field="source.ip",
            dst_field="destination.ip",
        )

        assert "nodes" in result
        assert "links" in result

    @patch("arkime_mcp_server.client.httpx.Client")
    def test_get_unique(self, mock_client_class):
        """Test get_unique method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "192.168.1.1, 10\n192.168.1.2, 5"

        mock_http_client = Mock()
        mock_http_client.get.return_value = mock_response
        mock_client_class.return_value = mock_http_client

        client = ArkimeClient("http://test.local:8005", "user", "pass")
        result = client.get_unique(exp="source.ip", length=10)

        assert "192.168.1.1" in result
        assert "192.168.1.2" in result

    @patch("arkime_mcp_server.client.httpx.Client")
    def test_get_session_detail(self, mock_client_class):
        """Test get_session_detail method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"session": "details"}

        mock_http_client = Mock()
        mock_http_client.get.return_value = mock_response
        mock_client_class.return_value = mock_http_client

        client = ArkimeClient("http://test.local:8005", "user", "pass")
        result = client.get_session_detail("node1", "session123")

        assert result == {"session": "details"}

    @patch("arkime_mcp_server.client.httpx.Client")
    def test_get_fields(self, mock_client_class):
        """Test get_fields method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = [
            {"exp": "source.ip", "friendlyName": "Source IP"},
            {"exp": "destination.ip", "friendlyName": "Destination IP"},
        ]

        mock_http_client = Mock()
        mock_http_client.get.return_value = mock_response
        mock_client_class.return_value = mock_http_client

        client = ArkimeClient("http://test.local:8005", "user", "pass")
        result = client.get_fields()

        assert isinstance(result, list)
        assert len(result) == 2

    @patch("arkime_mcp_server.client.httpx.Client")
    def test_post_method(self, mock_client_class):
        """Test _post method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"success": True}

        mock_http_client = Mock()
        mock_http_client.post.return_value = mock_response
        mock_client_class.return_value = mock_http_client

        client = ArkimeClient("http://test.local:8005", "user", "pass")
        result = client._post("test/endpoint", data={"test": "data"})

        assert result == {"success": True}
        mock_http_client.post.assert_called_once()

    @patch("arkime_mcp_server.client.httpx.Client")
    def test_delete_method(self, mock_client_class):
        """Test _delete method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"deleted": True}

        mock_http_client = Mock()
        mock_http_client.delete.return_value = mock_response
        mock_client_class.return_value = mock_http_client

        client = ArkimeClient("http://test.local:8005", "user", "pass")
        result = client._delete("test/endpoint")

        assert result == {"deleted": True}
        mock_http_client.delete.assert_called_once()
