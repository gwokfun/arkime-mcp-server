#!/usr/bin/env python3
"""
LangChain Tool Adapter for Arkime Skills

This module provides adapters to use Arkime skills with LangChain agents.

Example usage:
    from langchain_agent import ArkimeSkillsAdapter

    # Initialize the adapter
    adapter = ArkimeSkillsAdapter()

    # Get LangChain tools
    tools = adapter.get_langchain_tools()

    # Use with a LangChain agent
    from langchain.agents import initialize_agent, AgentType
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4")
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True
    )

    result = agent.run("Search for sessions from IP 192.168.1.10 in the last hour")
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional

try:
    from langchain.tools import StructuredTool
    from pydantic import BaseModel, Field, create_model
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseModel = None
    Field = None
    create_model = None
    StructuredTool = None
    print("Warning: langchain not installed. Install with: pip install langchain")


class ArkimeSkillsAdapter:
    """Adapter to convert Arkime skills to LangChain tools."""

    def __init__(self, manifest_path: Optional[Path] = None):
        """
        Initialize the adapter.

        Args:
            manifest_path: Path to arkime_skills.yaml. If None, auto-detects.
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is required. Install with: pip install langchain"
            )

        if manifest_path is None:
            # Auto-detect path
            manifest_path = Path(__file__).parent.parent / "arkime_skills.yaml"

        with open(manifest_path, 'r') as f:
            self.manifest = yaml.safe_load(f)

        self.skills = self.manifest["skills"]

    def _create_pydantic_model(self, skill: Dict[str, Any]) -> type[BaseModel]:
        """Create a Pydantic model for skill parameters."""
        fields = {}

        for param in skill.get("parameters", []):
            param_name = param["name"]
            param_type = param["type"]
            param_desc = param.get("description", "")
            param_default = param.get("default")
            is_required = param.get("required", False)

            # Map JSON Schema types to Python types
            type_map = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
            }

            python_type = type_map.get(param_type, str)

            # Handle optional parameters
            if not is_required:
                python_type = Optional[python_type]
                if param_default is None:
                    param_default = None

            # Create field with description
            if param_default is not None:
                fields[param_name] = (python_type, Field(default=param_default, description=param_desc))
            elif not is_required:
                fields[param_name] = (python_type, Field(default=None, description=param_desc))
            else:
                fields[param_name] = (python_type, Field(description=param_desc))

        # Create dynamic Pydantic model
        model_name = f"{skill['name']}_input"
        return create_model(model_name, **fields)

    def _create_tool_function(self, skill: Dict[str, Any]) -> Callable:
        """
        Create a callable function for a skill.

        Note: This returns a stub function. In a real implementation,
        you would connect this to the actual Arkime MCP server.
        """
        skill_name = skill["name"]

        def tool_func(**kwargs) -> str:
            """Stub function that needs to be connected to MCP server."""
            return f"Called {skill_name} with params: {kwargs}"

        tool_func.__name__ = skill_name
        tool_func.__doc__ = skill["description"]

        return tool_func

    def get_langchain_tools(self) -> List[StructuredTool]:
        """
        Convert all skills to LangChain StructuredTool instances.

        Returns:
            List of LangChain StructuredTool objects
        """
        tools = []

        for skill in self.skills:
            # Create Pydantic input model
            args_schema = self._create_pydantic_model(skill)

            # Create tool function
            func = self._create_tool_function(skill)

            # Create StructuredTool
            tool = StructuredTool(
                name=skill["name"],
                description=skill["description"],
                func=func,
                args_schema=args_schema,
            )

            tools.append(tool)

        return tools

    def get_tools_by_use_case(self, use_case: str) -> List[StructuredTool]:
        """
        Get tools filtered by use case.

        Args:
            use_case: One of: soc, threat_hunting, incident_response,
                     network_monitoring, compliance, multi_cluster

        Returns:
            List of LangChain StructuredTool objects for the use case
        """
        filtered_skills = [
            skill for skill in self.skills
            if use_case in skill.get("use_cases", [])
        ]

        tools = []
        for skill in filtered_skills:
            args_schema = self._create_pydantic_model(skill)
            func = self._create_tool_function(skill)
            tool = StructuredTool(
                name=skill["name"],
                description=skill["description"],
                func=func,
                args_schema=args_schema,
            )
            tools.append(tool)

        return tools


def main():
    """Example usage."""
    adapter = ArkimeSkillsAdapter()

    # Get all tools
    all_tools = adapter.get_langchain_tools()
    print(f"Total tools: {len(all_tools)}")

    # Get SOC-specific tools
    soc_tools = adapter.get_tools_by_use_case("soc")
    print(f"\nSOC tools: {len(soc_tools)}")
    for tool in soc_tools[:5]:  # Show first 5
        print(f"  - {tool.name}: {tool.description[:60]}...")

    # Get threat hunting tools
    hunting_tools = adapter.get_tools_by_use_case("threat_hunting")
    print(f"\nThreat hunting tools: {len(hunting_tools)}")


if __name__ == "__main__":
    main()
