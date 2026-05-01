#!/usr/bin/env python3
"""
Microsoft AutoGen Configuration for Arkime Skills

This module provides configuration helpers for using Arkime skills with
Microsoft AutoGen framework.

Example usage:
    from autogen_config import ArkimeAutoGenConfig

    # Initialize
    config = ArkimeAutoGenConfig()

    # Get function map for AutoGen agent
    function_map = config.get_function_map()

    # Get AutoGen-compatible function configs
    functions = config.get_function_configs()

    # Use with AutoGen
    import autogen

    llm_config = {
        "functions": functions,
        "config_list": [{"model": "gpt-4", "api_key": "your-key"}],
    }

    agent = autogen.AssistantAgent(
        name="arkime_analyst",
        llm_config=llm_config,
        function_map=function_map,
    )
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional


class ArkimeAutoGenConfig:
    """Configuration helper for AutoGen integration with Arkime skills."""

    def __init__(self, manifest_path: Optional[Path] = None):
        """
        Initialize the configuration.

        Args:
            manifest_path: Path to arkime_skills.yaml. If None, auto-detects.
        """
        if manifest_path is None:
            manifest_path = Path(__file__).parent.parent / "arkime_skills.yaml"

        with open(manifest_path, 'r') as f:
            self.manifest = yaml.safe_load(f)

        self.skills = self.manifest["skills"]

    def _skill_to_function_config(self, skill: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a skill to AutoGen function config format.

        AutoGen uses OpenAI function calling format.
        """
        properties = {}
        required = []

        for param in skill.get("parameters", []):
            prop = {
                "type": param["type"],
                "description": param.get("description", ""),
            }

            if "enum" in param:
                prop["enum"] = param["enum"]

            if "default" in param:
                prop["default"] = param["default"]

            properties[param["name"]] = prop

            if param.get("required", False):
                required.append(param["name"])

        config = {
            "name": skill["name"],
            "description": skill["description"],
            "parameters": {
                "type": "object",
                "properties": properties,
            },
        }

        if required:
            config["parameters"]["required"] = required

        return config

    def _create_stub_function(self, skill: Dict[str, Any]) -> Callable:
        """
        Create a stub function for a skill.

        In a real implementation, this would connect to the MCP server.
        """
        skill_name = skill["name"]

        def stub_func(**kwargs) -> str:
            """Stub function - connect to MCP server in production."""
            return f"Called {skill_name} with: {kwargs}"

        stub_func.__name__ = skill_name
        return stub_func

    def get_function_configs(self) -> List[Dict[str, Any]]:
        """
        Get AutoGen-compatible function configurations.

        Returns:
            List of function configs for AutoGen llm_config["functions"]
        """
        return [
            self._skill_to_function_config(skill)
            for skill in self.skills
        ]

    def get_function_map(self) -> Dict[str, Callable]:
        """
        Get function map for AutoGen agent.

        Returns:
            Dictionary mapping function names to callable implementations
        """
        return {
            skill["name"]: self._create_stub_function(skill)
            for skill in self.skills
        }

    def get_functions_by_use_case(self, use_case: str) -> List[Dict[str, Any]]:
        """
        Get function configs filtered by use case.

        Args:
            use_case: One of: soc, threat_hunting, incident_response,
                     network_monitoring, compliance, multi_cluster

        Returns:
            List of function configs for the specified use case
        """
        filtered_skills = [
            skill for skill in self.skills
            if use_case in skill.get("use_cases", [])
        ]

        return [
            self._skill_to_function_config(skill)
            for skill in filtered_skills
        ]

    def create_agent_config(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        use_case: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a complete AutoGen agent configuration.

        Args:
            model: OpenAI model name
            api_key: OpenAI API key (optional)
            use_case: Optional use case filter

        Returns:
            Complete llm_config dictionary for AutoGen agent
        """
        if use_case:
            functions = self.get_functions_by_use_case(use_case)
        else:
            functions = self.get_function_configs()

        config = {
            "functions": functions,
            "config_list": [{"model": model}],
        }

        if api_key:
            config["config_list"][0]["api_key"] = api_key

        return config


def main():
    """Example usage."""
    config = ArkimeAutoGenConfig()

    # Get all function configs
    functions = config.get_function_configs()
    print(f"Total functions: {len(functions)}")

    # Show first function
    print("\nExample function config:")
    import json
    print(json.dumps(functions[0], indent=2))

    # Get function map
    function_map = config.get_function_map()
    print(f"\nFunction map has {len(function_map)} functions")

    # Test a function
    test_func = function_map["search_sessions"]
    result = test_func(expression="ip.src==192.168.1.10", hours=1)
    print(f"\nTest function call result: {result}")

    # Get SOC-specific config
    soc_config = config.create_agent_config(use_case="soc")
    print(f"\nSOC config has {len(soc_config['functions'])} functions")


if __name__ == "__main__":
    main()
