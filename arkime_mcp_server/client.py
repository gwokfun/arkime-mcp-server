"""
Arkime viewer API client with HTTP Digest authentication.
"""

import hashlib
import secrets
import httpx
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin
import re

# Constants
CNONCE_LENGTH = 8
DEFAULT_TIMEOUT = 30.0
MAX_SESSION_LIMIT = 200


class DigestAuth(httpx.Auth):
    """
    HTTP Digest Authentication handler for httpx.

    Note: Uses MD5 hashing as required by RFC 2617. While MD5 is cryptographically
    weak, it is the standard for HTTP Digest Authentication. Consider using more
    secure authentication methods (e.g., OAuth2, API tokens) when possible.
    """

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self._challenge = None

    def auth_flow(self, request):
        # First, try the request without auth to get the challenge
        response = yield request

        if response.status_code == 401:
            # Parse the WWW-Authenticate header
            auth_header = response.headers.get("www-authenticate", "")
            if "Digest" in auth_header:
                self._challenge = self._parse_challenge(auth_header)

                # Build the Authorization header with full URI (path + query)
                uri = str(request.url.path)
                if request.url.query:
                    uri += f"?{request.url.query.decode() if isinstance(request.url.query, bytes) else request.url.query}"
                auth = self._build_digest_header(request.method, uri)
                request.headers["Authorization"] = auth

                # Retry the request with auth
                yield request

    def _parse_challenge(self, header: str) -> Dict[str, str]:
        """Parse the WWW-Authenticate Digest challenge."""
        challenge = {}
        # Remove 'Digest ' prefix
        header = header.replace("Digest ", "")

        # Parse key=value pairs
        for match in re.finditer(r'(\w+)=(?:"([^"]+)"|([^,\s]+))', header):
            key = match.group(1)
            value = match.group(2) or match.group(3)
            challenge[key] = value

        return challenge

    def _build_digest_header(self, method: str, uri: str) -> str:
        """Build the Authorization header for Digest authentication."""
        realm = self._challenge.get("realm", "")
        nonce = self._challenge.get("nonce", "")
        qop = self._challenge.get("qop", "")
        algorithm = self._challenge.get("algorithm", "MD5")
        opaque = self._challenge.get("opaque", "")

        # Calculate HA1
        ha1 = hashlib.md5(f"{self.username}:{realm}:{self.password}".encode()).hexdigest()

        # Calculate HA2
        ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()

        # Calculate response
        if qop:
            nc = "00000001"
            # Generate random cnonce for security
            cnonce = secrets.token_hex(CNONCE_LENGTH)
            response_hash = hashlib.md5(
                f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}".encode()
            ).hexdigest()

            auth_header = (
                f'Digest username="{self.username}", '
                f'realm="{realm}", '
                f'nonce="{nonce}", '
                f'uri="{uri}", '
                f'qop={qop}, '
                f'nc={nc}, '
                f'cnonce="{cnonce}", '
                f'response="{response_hash}", '
                f'algorithm={algorithm}'
            )
        else:
            response_hash = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()
            auth_header = (
                f'Digest username="{self.username}", '
                f'realm="{realm}", '
                f'nonce="{nonce}", '
                f'uri="{uri}", '
                f'response="{response_hash}", '
                f'algorithm={algorithm}'
            )

        if opaque:
            auth_header += f', opaque="{opaque}"'

        return auth_header


class ArkimeClient:
    """Client for interacting with the Arkime API."""

    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize the Arkime client.

        Args:
            base_url: Base URL of the Arkime viewer
            username: Username for authentication
            password: Password for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.auth = DigestAuth(username, password)
        self.client = httpx.Client(auth=self.auth, timeout=DEFAULT_TIMEOUT)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def _get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], str]:
        """
        Make a GET request to the Arkime API.

        Args:
            endpoint: API endpoint (without /api/ prefix)
            params: Query parameters

        Returns:
            JSON response as dict or text response as str

        Raises:
            httpx.HTTPError: If the request fails
        """
        url = urljoin(f"{self.base_url}/api/", endpoint)

        # Clean up params - remove None values
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        response = self.client.get(url, params=clean_params)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    def _post(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], str]:
        """
        Make a POST request to the Arkime API.

        Args:
            endpoint: API endpoint (without /api/ prefix)
            params: Query parameters
            data: POST body data

        Returns:
            JSON response as dict or text response as str

        Raises:
            httpx.HTTPError: If the request fails
        """
        url = urljoin(f"{self.base_url}/api/", endpoint)

        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        response = self.client.post(url, params=clean_params, json=data)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    def _delete(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], str]:
        """
        Make a DELETE request to the Arkime API.

        Args:
            endpoint: API endpoint (without /api/ prefix)
            params: Query parameters

        Returns:
            JSON response as dict or text response as str

        Raises:
            httpx.HTTPError: If the request fails
        """
        url = urljoin(f"{self.base_url}/api/", endpoint)

        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        response = self.client.delete(url, params=clean_params)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    # ── Session APIs ──

    def get_sessions(
        self,
        expression: Optional[str] = None,
        date: Union[int, str] = 1,
        length: int = 50,
        start: int = 0,
        fields: Optional[str] = None,
        order: Optional[str] = None,
        start_time: Optional[int] = None,
        stop_time: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Search sessions.

        Args:
            expression: Arkime search expression
            date: Time range in hours (or -1 for all)
            length: Max results to return (1-200)
            start: Starting index for pagination (>= 0)
            fields: Comma-separated list of fields to return
            order: Sort order (e.g., "totDataBytes:desc")
            start_time: Unix timestamp in milliseconds
            stop_time: Unix timestamp in milliseconds

        Returns:
            Session search results

        Raises:
            ValueError: If parameters are out of valid range
        """
        # Input validation
        if not 1 <= length <= MAX_SESSION_LIMIT:
            raise ValueError(f"length must be between 1 and {MAX_SESSION_LIMIT}")
        if start < 0:
            raise ValueError("start must be >= 0")

        params: Dict[str, Any] = {"date": date, "length": length, "start": start}

        if expression:
            params["expression"] = expression
        if fields:
            params["fields"] = fields
        if order:
            params["order"] = order
        if start_time is not None:
            params["startTime"] = start_time
            params.pop("date", None)
        if stop_time is not None:
            params["stopTime"] = stop_time

        return self._get("sessions", params)

    def get_session_detail(self, node: str, session_id: str) -> Any:
        """Get detailed information for a single session."""
        return self._get(f"session/{node}/{session_id}/detail")

    def get_session_packets(self, node: str, session_id: str) -> Any:
        """Get decoded packet data for a session."""
        return self._get(f"session/{node}/{session_id}/packets")

    def get_session_pcap(self, node: str, session_id: str) -> bytes:
        """Download PCAP file for a session."""
        url = urljoin(f"{self.base_url}/api/", f"session/{node}/{session_id}/pcap")
        response = self.client.get(url)
        response.raise_for_status()
        return response.content

    def get_session_raw(self, node: str, session_id: str) -> str:
        """Get raw session data."""
        return self._get(f"session/{node}/{session_id}/raw")

    # ── Connections & Aggregations ──

    def get_connections(
        self,
        expression: Optional[str] = None,
        date: Union[int, str] = 1,
        src_field: str = "source.ip",
        dst_field: str = "ip.dst:port",
        length: int = 50,
    ) -> Dict[str, Any]:
        """
        Get network connection graph.

        Args:
            expression: Filter expression
            date: Time range in hours
            src_field: Source field for graph
            dst_field: Destination field for graph
            length: Max connections to return

        Returns:
            Connection graph with nodes and links
        """
        params = {
            "date": date,
            "srcField": src_field,
            "dstField": dst_field,
            "length": length,
        }
        if expression:
            params["expression"] = expression

        return self._get("connections", params)

    def get_unique(
        self,
        exp: str,
        expression: Optional[str] = None,
        date: Union[int, str] = 1,
        counts: int = 1,
        length: int = 20,
    ) -> str:
        """
        Get unique values for a field.

        Args:
            exp: Field expression to get unique values for
            expression: Filter expression
            date: Time range in hours
            counts: Include session counts (1 or 0)
            length: Max unique values to return

        Returns:
            Newline-separated list of unique values with counts
        """
        params = {"exp": exp, "date": date, "counts": counts, "length": length}
        if expression:
            params["expression"] = expression

        return self._get("unique", params)

    # ── Health & Stats ──

    def get_es_health(self) -> Dict[str, Any]:
        """Get Elasticsearch/OpenSearch cluster health."""
        return self._get("eshealth")

    def get_stats(self) -> Dict[str, Any]:
        """Get Arkime statistics."""
        return self._get("stats")

    def get_es_indices(self) -> Dict[str, Any]:
        """Get Elasticsearch indices information."""
        return self._get("esindices/list")

    # ── Files ──

    def get_files(self, length: int = 20, start: int = 0) -> Dict[str, Any]:
        """
        Get list of PCAP files.

        Args:
            length: Max files to return
            start: Starting index for pagination

        Returns:
            List of PCAP files with metadata
        """
        return self._get("files", {"length": length, "start": start})

    # ── Fields ──

    def get_fields(self) -> list:
        """Get list of available session fields."""
        return self._get("fields", {"array": "true"})

    def get_field_values(self, field: str, expression: Optional[str] = None) -> list:
        """
        Get possible values for a field.

        Args:
            field: Field name
            expression: Optional filter expression

        Returns:
            List of possible field values
        """
        params = {"exp": field}
        if expression:
            params["expression"] = expression
        return self._get("field/values", params)

    # ── DNS ──

    def get_reverse_dns(self, ip: str) -> Any:
        """Get reverse DNS (PTR record) for an IP address."""
        return self._get("reversedns", {"ip": ip})

    # ── User & Settings ──

    def get_current_user(self) -> Dict[str, Any]:
        """Get information about the current user."""
        return self._get("user")

    def get_settings(self) -> Dict[str, Any]:
        """Get Arkime viewer settings."""
        return self._get("user/settings")

    # ── Tags ──

    def add_tags(
        self, tags: str, node: str, session_id: str, segments: str = "all"
    ) -> Dict[str, Any]:
        """
        Add tags to a session.

        Args:
            tags: Comma-separated list of tags
            node: Node name
            session_id: Session ID
            segments: Which segments to tag (all, src, dst)

        Returns:
            Success message
        """
        params = {"tags": tags, "segments": segments}
        return self._post(f"session/{node}/{session_id}/tag", params=params)

    def remove_tags(
        self, tags: str, node: str, session_id: str, segments: str = "all"
    ) -> Dict[str, Any]:
        """
        Remove tags from a session.

        Args:
            tags: Comma-separated list of tags
            node: Node name
            session_id: Session ID
            segments: Which segments to remove tags from

        Returns:
            Success message
        """
        params = {"tags": tags, "segments": segments}
        return self._delete(f"session/{node}/{session_id}/tag", params=params)

    # ── Hunts ──

    def create_hunt(
        self,
        name: str,
        search: str,
        hunt_type: str = "raw",
        src: bool = True,
        dst: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a hunt job.

        Args:
            name: Hunt name
            search: Search expression
            hunt_type: Type of hunt (raw, reassembled, etc.)
            src: Search source packets
            dst: Search destination packets

        Returns:
            Hunt creation result
        """
        data = {"name": name, "search": search, "type": hunt_type, "src": src, "dst": dst}
        return self._post("hunt", data=data)

    def get_hunts(self) -> list:
        """Get list of hunts."""
        result = self._get("hunt/list")
        if isinstance(result, dict):
            return result.get("hunts", [])
        return []

    def delete_hunt(self, hunt_id: str) -> Dict[str, Any]:
        """Delete a hunt."""
        return self._delete(f"hunt/{hunt_id}")

    # ── Views ──

    def create_view(self, name: str, expression: str) -> Dict[str, Any]:
        """
        Create a saved view.

        Args:
            name: View name
            expression: Search expression

        Returns:
            View creation result
        """
        data = {"name": name, "expression": expression}
        return self._post("view", data=data)

    def get_views(self) -> list:
        """Get list of views."""
        result = self._get("views")
        if isinstance(result, dict):
            return result.get("views", [])
        return []

    def delete_view(self, view_id: str) -> Dict[str, Any]:
        """Delete a view."""
        return self._delete(f"view/{view_id}")

    # ── Notifiers ──

    def get_notifiers(self) -> list:
        """Get list of configured notifiers."""
        result = self._get("notifiers")
        if isinstance(result, dict):
            return result.get("notifiers", [])
        return []

    # ── Parliament (Multi-cluster) ──

    def get_parliament(self) -> Dict[str, Any]:
        """Get parliament (multi-cluster) information."""
        return self._get("parliament")
