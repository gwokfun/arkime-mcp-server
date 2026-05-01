#!/usr/bin/env python3
"""
Convert Arkime skills manifest to Anthropic Claude tool use format.

Usage:
    python anthropic_converter.py > anthropic_tools.json
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Any


def skill_to_anthropic_tool(skill: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a single skill to Anthropic tool use format.

    Anthropic tool format:
    {
        "name": "tool_name",
        "description": "What the tool does",
        "input_schema": {
            "type": "object",
            "properties": {
                "param_name": {
                    "type": "string",
                    "description": "param description",
                    "enum": ["value1", "value2"]  # optional
                }
            },
            "required": ["param1", "param2"]
        }
    }
    """
    properties = {}
    required = []

    for param in skill.get("parameters", []):
        prop = {
            "type": param["type"],
            "description": param.get("description", ""),
        }

        # Add enum if present
        if "enum" in param:
            prop["enum"] = param["enum"]

        properties[param["name"]] = prop

        # Track required parameters
        if param.get("required", False):
            required.append(param["name"])

    tool_def = {
        "name": skill["name"],
        "description": skill["description"],
        "input_schema": {
            "type": "object",
            "properties": properties,
        },
    }

    # Only add required if there are required parameters
    if required:
        tool_def["input_schema"]["required"] = required

    return tool_def


def main():
    # Load the skills manifest
    script_dir = Path(__file__).parent
    manifest_path = script_dir.parent / "arkime_skills.yaml"

    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)

    # Convert all skills to Anthropic format
    anthropic_tools = [
        skill_to_anthropic_tool(skill)
        for skill in manifest["skills"]
    ]

    # Output as JSON
    print(json.dumps(anthropic_tools, indent=2))


if __name__ == "__main__":
    main()
