"""
Configuration management for Arkime MCP Server.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration manager for Arkime MCP Server."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to YAML configuration file. If None, looks for
                        config.yaml in current directory or uses defaults.
        """
        # Load environment variables from .env file if present
        load_dotenv()

        # Default configuration
        self.config: Dict[str, Any] = {
            "arkime": {
                "url": "http://your-arkime-server:8005",
                "user": "mcp",
                "password": None,
            },
            "tools": {},
        }

        # Load config file if it exists
        if config_path:
            config_file = Path(config_path)
        else:
            # Try to find config.yaml in current directory
            config_file = Path("config.yaml")

        if config_file.exists():
            with open(config_file, "r") as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    self._merge_config(self.config, file_config)

        # Override with environment variables
        env_url = os.getenv("ARKIME_URL")
        if env_url:
            self.config["arkime"]["url"] = env_url

        env_user = os.getenv("ARKIME_USER")
        if env_user:
            self.config["arkime"]["user"] = env_user

        env_password = os.getenv("ARKIME_PASSWORD")
        if env_password:
            self.config["arkime"]["password"] = env_password

        # Validate required configuration
        if not self.config["arkime"]["password"]:
            raise ValueError(
                "ARKIME_PASSWORD is required. Set it via environment variable or config file."
            )

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge override config into base config."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    @property
    def arkime_url(self) -> str:
        """Get Arkime URL."""
        return self.config["arkime"]["url"]

    @property
    def arkime_user(self) -> str:
        """Get Arkime username."""
        return self.config["arkime"]["user"]

    @property
    def arkime_password(self) -> str:
        """Get Arkime password."""
        return self.config["arkime"]["password"]

    def is_tool_enabled(self, tool_name: str) -> bool:
        """
        Check if a tool is enabled.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool is enabled (or not configured, defaults to enabled)
        """
        return self.config.get("tools", {}).get(tool_name, True)

    def get_enabled_tools(self) -> Dict[str, bool]:
        """
        Get all tool enablement settings.

        Returns:
            Dictionary mapping tool names to enabled status
        """
        return self.config.get("tools", {})
