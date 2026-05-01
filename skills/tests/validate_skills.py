#!/usr/bin/env python3
"""
Skills Validation Script

Validates that the skills manifest (arkime_skills.yaml) conforms to the
agentskills.io v1.0 specification and that every skill name corresponds to
an existing MCP tool in the server.py implementation.

This script is designed to run as part of CI/CD to ensure consistency between
the skills manifest and the actual MCP server implementation.
"""

import sys
import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Set


# JSON Schema primitive types allowed in agentskills.io
VALID_TYPES = {"string", "integer", "number", "boolean", "array", "object"}

# Valid use cases as defined in the README
VALID_USE_CASES = {
    "soc",
    "threat_hunting",
    "incident_response",
    "network_monitoring",
    "compliance",
    "multi_cluster"
}


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def load_skills_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load and parse the skills YAML manifest."""
    if not manifest_path.exists():
        raise ValidationError(f"Skills manifest not found: {manifest_path}")

    try:
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValidationError(f"Failed to parse YAML: {e}")

    return manifest


def extract_mcp_tools(server_py_path: Path) -> Set[str]:
    """Extract all MCP tool names from server.py by parsing function definitions."""
    if not server_py_path.exists():
        raise ValidationError(f"server.py not found: {server_py_path}")

    tools = set()

    with open(server_py_path, 'r') as f:
        content = f.read()

    # Find all function definitions that are decorated with @get_mcp().tool()
    # Pattern matches: @get_mcp().tool()\ndef function_name(
    pattern = r'@get_mcp\(\)\.tool\(\)\s+def\s+(\w+)\s*\('
    matches = re.findall(pattern, content)

    tools.update(matches)

    if not tools:
        raise ValidationError("No MCP tools found in server.py. Check the parsing logic.")

    return tools


def validate_manifest_structure(manifest: Dict[str, Any]) -> None:
    """Validate the top-level structure of the manifest."""
    # Check required top-level fields
    if "version" not in manifest:
        raise ValidationError("Missing required field: 'version'")

    if manifest["version"] != "1.0":
        raise ValidationError(f"Expected version '1.0', got '{manifest['version']}'")

    if "metadata" not in manifest:
        raise ValidationError("Missing required field: 'metadata'")

    if "skills" not in manifest:
        raise ValidationError("Missing required field: 'skills'")

    if not isinstance(manifest["skills"], list):
        raise ValidationError("'skills' must be a list")

    # Validate metadata structure
    metadata = manifest["metadata"]
    required_metadata_fields = ["name", "display_name", "description", "provider"]
    for field in required_metadata_fields:
        if field not in metadata:
            raise ValidationError(f"Missing required metadata field: '{field}'")


def validate_skill(skill: Dict[str, Any], index: int) -> None:
    """Validate a single skill definition."""
    # Check required fields
    required_fields = ["name", "display_name", "description"]
    for field in required_fields:
        if field not in skill:
            raise ValidationError(f"Skill at index {index} missing required field: '{field}'")

    skill_name = skill["name"]

    # Validate name is snake_case
    if not re.match(r'^[a-z][a-z0-9_]*$', skill_name):
        raise ValidationError(
            f"Skill '{skill_name}' has invalid name format. "
            "Must be snake_case starting with a letter."
        )

    # Validate use_cases if present
    if "use_cases" in skill:
        if not isinstance(skill["use_cases"], list):
            raise ValidationError(f"Skill '{skill_name}': use_cases must be a list")

        for use_case in skill["use_cases"]:
            if use_case not in VALID_USE_CASES:
                raise ValidationError(
                    f"Skill '{skill_name}': invalid use_case '{use_case}'. "
                    f"Valid values are: {', '.join(sorted(VALID_USE_CASES))}"
                )

    # Validate parameters
    if "parameters" in skill:
        if not isinstance(skill["parameters"], list):
            raise ValidationError(f"Skill '{skill_name}': parameters must be a list")

        for i, param in enumerate(skill["parameters"]):
            validate_parameter(param, skill_name, i)

    # Validate output schema if present
    if "output" in skill:
        validate_output(skill["output"], skill_name)


def validate_parameter(param: Dict[str, Any], skill_name: str, index: int) -> None:
    """Validate a parameter definition."""
    required_fields = ["name", "type"]
    for field in required_fields:
        if field not in param:
            raise ValidationError(
                f"Skill '{skill_name}', parameter at index {index}: "
                f"missing required field '{field}'"
            )

    param_name = param["name"]
    param_type = param["type"]

    # Validate type
    if param_type not in VALID_TYPES:
        raise ValidationError(
            f"Skill '{skill_name}', parameter '{param_name}': "
            f"invalid type '{param_type}'. Valid types are: {', '.join(sorted(VALID_TYPES))}"
        )

    # Validate required field if present
    if "required" in param:
        if not isinstance(param["required"], bool):
            raise ValidationError(
                f"Skill '{skill_name}', parameter '{param_name}': "
                "'required' must be a boolean"
            )

    # Validate enum if present
    if "enum" in param:
        if not isinstance(param["enum"], list):
            raise ValidationError(
                f"Skill '{skill_name}', parameter '{param_name}': "
                "'enum' must be a list"
            )
        if not param["enum"]:
            raise ValidationError(
                f"Skill '{skill_name}', parameter '{param_name}': "
                "'enum' cannot be empty"
            )


def validate_output(output: Dict[str, Any], skill_name: str) -> None:
    """Validate output schema definition."""
    if "type" not in output:
        raise ValidationError(
            f"Skill '{skill_name}': output schema missing 'type' field"
        )

    output_type = output["type"]
    if output_type not in VALID_TYPES:
        raise ValidationError(
            f"Skill '{skill_name}': invalid output type '{output_type}'. "
            f"Valid types are: {', '.join(sorted(VALID_TYPES))}"
        )


def validate_skill_tool_correspondence(
    skills: List[Dict[str, Any]],
    mcp_tools: Set[str]
) -> None:
    """Validate that every skill name matches an MCP tool."""
    skill_names = {skill["name"] for skill in skills}

    # Check for skills without corresponding tools
    skills_without_tools = skill_names - mcp_tools
    if skills_without_tools:
        raise ValidationError(
            f"Skills defined without corresponding MCP tools: "
            f"{', '.join(sorted(skills_without_tools))}"
        )

    # Report on tools without corresponding skills (informational, not an error)
    tools_without_skills = mcp_tools - skill_names
    if tools_without_skills:
        print(
            f"Note: MCP tools without corresponding skills: "
            f"{', '.join(sorted(tools_without_skills))}",
            file=sys.stderr
        )


def validate_duplicate_names(skills: List[Dict[str, Any]]) -> None:
    """Ensure no duplicate skill names."""
    names = [skill["name"] for skill in skills]
    duplicates = [name for name in names if names.count(name) > 1]

    if duplicates:
        unique_duplicates = set(duplicates)
        raise ValidationError(
            f"Duplicate skill names found: {', '.join(sorted(unique_duplicates))}"
        )


def main():
    """Run all validations."""
    # Determine paths relative to this script
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    manifest_path = repo_root / "skills" / "arkime_skills.yaml"
    server_py_path = repo_root / "arkime_mcp_server" / "server.py"

    print(f"Validating skills manifest: {manifest_path}")
    print(f"Checking against server.py: {server_py_path}")
    print()

    try:
        # Load manifest
        manifest = load_skills_manifest(manifest_path)
        print(f"✓ Loaded manifest (version {manifest['version']})")

        # Validate manifest structure
        validate_manifest_structure(manifest)
        print("✓ Manifest structure is valid")

        # Extract MCP tools
        mcp_tools = extract_mcp_tools(server_py_path)
        print(f"✓ Found {len(mcp_tools)} MCP tools in server.py")

        # Validate skills
        skills = manifest["skills"]
        print(f"✓ Found {len(skills)} skills in manifest")

        # Check for duplicate names
        validate_duplicate_names(skills)
        print("✓ No duplicate skill names")

        # Validate each skill
        for i, skill in enumerate(skills):
            validate_skill(skill, i)
        print(f"✓ All {len(skills)} skills are valid")

        # Validate skill-tool correspondence
        validate_skill_tool_correspondence(skills, mcp_tools)
        print("✓ All skills correspond to MCP tools")

        print()
        print("=" * 60)
        print("SUCCESS: Skills manifest is valid!")
        print("=" * 60)
        return 0

    except ValidationError as e:
        print()
        print("=" * 60)
        print(f"VALIDATION ERROR: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print(f"UNEXPECTED ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
