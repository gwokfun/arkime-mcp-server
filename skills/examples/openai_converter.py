#!/usr/bin/env python3
"""
Convert Arkime skills manifest to OpenAI function calling format.

Usage:
    python openai_converter.py > openai_functions.json
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Any


def skill_to_openai_function(skill: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a single skill to OpenAI function calling format.

    OpenAI function calling format:
    {
        "name": "function_name",
        "description": "What the function does",
        "parameters": {
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

        # Add default if present
        if "default" in param:
            prop["default"] = param["default"]

        properties[param["name"]] = prop

        # Track required parameters
        if param.get("required", False):
            required.append(param["name"])

    function_def = {
        "name": skill["name"],
        "description": skill["description"],
        "parameters": {
            "type": "object",
            "properties": properties,
        },
    }

    # Only add required if there are required parameters
    if required:
        function_def["parameters"]["required"] = required

    return function_def


def main():
    # Load the skills manifest
    script_dir = Path(__file__).parent
    manifest_path = script_dir.parent / "arkime_skills.yaml"

    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)

    # Convert all skills to OpenAI format
    openai_functions = [
        skill_to_openai_function(skill)
        for skill in manifest["skills"]
    ]

    # Output as JSON
    print(json.dumps(openai_functions, indent=2))


if __name__ == "__main__":
    main()
