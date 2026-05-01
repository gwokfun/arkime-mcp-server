"""
Unit tests for config module.
"""

import pytest
import os
import tempfile
from pathlib import Path
from arkime_mcp_server.config import Config


class TestConfig:
    """Tests for Config class."""

    def test_config_requires_password(self):
        """Test that config requires ARKIME_PASSWORD."""
        # Clear environment
        env_backup = os.environ.get("ARKIME_PASSWORD")
        if "ARKIME_PASSWORD" in os.environ:
            del os.environ["ARKIME_PASSWORD"]

        try:
            with pytest.raises(ValueError, match="ARKIME_PASSWORD is required"):
                Config()
        finally:
            # Restore environment
            if env_backup:
                os.environ["ARKIME_PASSWORD"] = env_backup

    def test_config_defaults(self):
        """Test default configuration values."""
        os.environ["ARKIME_PASSWORD"] = "test-password"
        try:
            config = Config()
            assert config.arkime_url == "http://your-arkime-server:8005"
            assert config.arkime_user == "mcp"
            assert config.arkime_password == "test-password"
        finally:
            del os.environ["ARKIME_PASSWORD"]

    def test_config_env_override(self):
        """Test environment variable override."""
        os.environ["ARKIME_URL"] = "http://custom.url:9000"
        os.environ["ARKIME_USER"] = "custom-user"
        os.environ["ARKIME_PASSWORD"] = "custom-password"

        try:
            config = Config()
            assert config.arkime_url == "http://custom.url:9000"
            assert config.arkime_user == "custom-user"
            assert config.arkime_password == "custom-password"
        finally:
            del os.environ["ARKIME_URL"]
            del os.environ["ARKIME_USER"]
            del os.environ["ARKIME_PASSWORD"]

    def test_config_yaml_file(self):
        """Test loading configuration from YAML file."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
arkime:
  url: "http://yaml.url:8005"
  user: "yaml-user"

tools:
  search_sessions: false
  get_session_detail: true
""")
            temp_config = f.name

        os.environ["ARKIME_PASSWORD"] = "test-password"

        try:
            config = Config(temp_config)
            assert config.arkime_url == "http://yaml.url:8005"
            assert config.arkime_user == "yaml-user"
            assert config.arkime_password == "test-password"
            assert config.is_tool_enabled("search_sessions") is False
            assert config.is_tool_enabled("get_session_detail") is True
        finally:
            del os.environ["ARKIME_PASSWORD"]
            os.unlink(temp_config)

    def test_config_env_overrides_yaml(self):
        """Test that environment variables override YAML config."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
arkime:
  url: "http://yaml.url:8005"
  user: "yaml-user"
""")
            temp_config = f.name

        os.environ["ARKIME_URL"] = "http://env.url:9000"
        os.environ["ARKIME_PASSWORD"] = "env-password"

        try:
            config = Config(temp_config)
            # Environment should override YAML
            assert config.arkime_url == "http://env.url:9000"
            assert config.arkime_user == "yaml-user"  # Not overridden
            assert config.arkime_password == "env-password"
        finally:
            del os.environ["ARKIME_URL"]
            del os.environ["ARKIME_PASSWORD"]
            os.unlink(temp_config)

    def test_tool_enabled_default(self):
        """Test that tools are enabled by default."""
        os.environ["ARKIME_PASSWORD"] = "test-password"
        try:
            config = Config()
            # Non-configured tools should be enabled by default
            assert config.is_tool_enabled("search_sessions") is True
            assert config.is_tool_enabled("nonexistent_tool") is True
        finally:
            del os.environ["ARKIME_PASSWORD"]

    def test_tool_enabled_configuration(self):
        """Test tool enablement configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
tools:
  search_sessions: false
  get_session_detail: true
  top_talkers: false
""")
            temp_config = f.name

        os.environ["ARKIME_PASSWORD"] = "test-password"

        try:
            config = Config(temp_config)
            assert config.is_tool_enabled("search_sessions") is False
            assert config.is_tool_enabled("get_session_detail") is True
            assert config.is_tool_enabled("top_talkers") is False
            # Unconfigured tool should still be enabled
            assert config.is_tool_enabled("unconfigured_tool") is True
        finally:
            del os.environ["ARKIME_PASSWORD"]
            os.unlink(temp_config)

    def test_get_enabled_tools(self):
        """Test getting all enabled tools configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
tools:
  tool1: true
  tool2: false
  tool3: true
""")
            temp_config = f.name

        os.environ["ARKIME_PASSWORD"] = "test-password"

        try:
            config = Config(temp_config)
            tools = config.get_enabled_tools()
            assert tools["tool1"] is True
            assert tools["tool2"] is False
            assert tools["tool3"] is True
        finally:
            del os.environ["ARKIME_PASSWORD"]
            os.unlink(temp_config)
