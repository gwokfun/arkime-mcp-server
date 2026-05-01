# Arkime Skills - Agent Integration Examples

This directory contains examples and adapters for integrating Arkime skills with popular AI agent platforms.

## Overview

The Arkime skills manifest (`../arkime_skills.yaml`) follows the agentskills.io v1.0 specification and can be adapted for use with any mainstream AI agent platform. This directory provides ready-to-use converters and configuration examples.

## Available Examples

### 1. OpenAI Function Calling (`openai_converter.py`)

Convert Arkime skills to OpenAI function calling format for use with GPT-4 and other OpenAI models.

**Usage:**
```bash
python openai_converter.py > openai_functions.json
```

**In your application:**
```python
import json
from openai import OpenAI

with open("openai_functions.json") as f:
    functions = json.load(f)

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Search for sessions from 192.168.1.10"}],
    functions=functions,
    function_call="auto"
)
```

### 2. Anthropic Claude Tool Use (`anthropic_converter.py`)

Convert Arkime skills to Anthropic Claude tool use format.

**Usage:**
```bash
python anthropic_converter.py > anthropic_tools.json
```

**In your application:**
```python
import json
from anthropic import Anthropic

with open("anthropic_tools.json") as f:
    tools = json.load(f)

client = Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "Find all external connections"}]
)
```

### 3. LangChain Integration (`langchain_agent.py`)

Adapter for using Arkime skills with LangChain agents.

**Requirements:**
```bash
pip install langchain langchain-openai pydantic
```

**Usage:**
```python
from langchain_agent import ArkimeSkillsAdapter
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI

# Initialize adapter
adapter = ArkimeSkillsAdapter()

# Get all tools or filter by use case
all_tools = adapter.get_langchain_tools()
soc_tools = adapter.get_tools_by_use_case("soc")

# Create agent
llm = ChatOpenAI(model="gpt-4")
agent = initialize_agent(
    soc_tools,
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

result = agent.run("Investigate traffic from 192.168.1.10 in the last hour")
```

### 4. Microsoft AutoGen (`autogen_config.py`)

Configuration helper for Microsoft AutoGen framework.

**Requirements:**
```bash
pip install pyautogen
```

**Usage:**
```python
from autogen_config import ArkimeAutoGenConfig
import autogen

config = ArkimeAutoGenConfig()

# Get function configs and map
llm_config = {
    "functions": config.get_function_configs(),
    "config_list": [{"model": "gpt-4", "api_key": "your-key"}]
}

function_map = config.get_function_map()

# Create agent
agent = autogen.AssistantAgent(
    name="arkime_analyst",
    llm_config=llm_config,
    function_map=function_map
)
```

### 5. Dify Platform (`dify_workflow.yaml`)

Example configuration for Dify visual workflow platform.

**Setup:**
1. Deploy an HTTP wrapper around the Arkime MCP server
2. Import `dify_workflow.yaml` into Dify custom tools
3. Configure environment variables (e.g., `ARKIME_API_TOKEN`)
4. Build workflows using Dify's visual editor

## Converting to Other Formats

### Google Gemini Function Calling

Similar to OpenAI format but with slight differences:

```python
import yaml
import json

with open("../arkime_skills.yaml") as f:
    manifest = yaml.safe_load(f)

# Gemini uses 'function_declarations' instead of 'functions'
gemini_functions = {
    "function_declarations": [
        {
            "name": skill["name"],
            "description": skill["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    param["name"]: {
                        "type": param["type"],
                        "description": param.get("description", "")
                    }
                    for param in skill.get("parameters", [])
                }
            }
        }
        for skill in manifest["skills"]
    ]
}
```

### CrewAI

CrewAI uses LangChain tools under the hood, so use the `langchain_agent.py` adapter:

```python
from langchain_agent import ArkimeSkillsAdapter
from crewai import Agent, Task, Crew

adapter = ArkimeSkillsAdapter()
tools = adapter.get_tools_by_use_case("threat_hunting")

analyst = Agent(
    role="Network Security Analyst",
    goal="Investigate network threats using Arkime",
    backstory="Expert in network forensics and threat hunting",
    tools=tools,
    verbose=True
)

task = Task(
    description="Analyze external connections from 192.168.1.10",
    agent=analyst
)

crew = Crew(agents=[analyst], tasks=[task])
result = crew.kickoff()
```

## Filtering by Use Case

All adapters support filtering tools by use case:

- `soc` - Security Operations Center automation
- `threat_hunting` - Proactive threat hunting
- `incident_response` - Forensic investigation
- `network_monitoring` - Traffic monitoring and anomaly detection
- `compliance` - Audit trail and regulatory compliance
- `multi_cluster` - Multi-site cluster management

**Example:**
```python
# LangChain
soc_tools = adapter.get_tools_by_use_case("soc")

# AutoGen
config = ArkimeAutoGenConfig()
llm_config = config.create_agent_config(use_case="threat_hunting")
```

## Implementation Notes

### Stub Functions

The example adapters use stub functions that return mock data. In a production deployment, you need to connect these to the actual Arkime MCP server.

**Options:**
1. **MCP stdio** - Use the MCP protocol directly via subprocess
2. **HTTP wrapper** - Deploy an HTTP API wrapper around the MCP server
3. **Direct client** - Use `ArkimeClient` from `arkime_mcp_server.client`

### Connecting to Real Arkime Server

Example using the Arkime client directly:

```python
from arkime_mcp_server.client import ArkimeClient

client = ArkimeClient(
    url="http://your-arkime:8005",
    user="your-user",
    password="your-password"
)

def search_sessions(expression=None, hours=1, limit=50, order=None):
    result = client.get_sessions(
        expression=expression,
        date=hours,
        length=limit,
        order=order
    )
    return result
```

## Testing

Test the converters:

```bash
# Test OpenAI converter
python openai_converter.py | head -20

# Test Anthropic converter
python anthropic_converter.py | head -20

# Test LangChain adapter
python langchain_agent.py

# Test AutoGen config
python autogen_config.py
```

## Contributing

To add support for a new agent platform:

1. Study the platform's tool/function calling format
2. Create a converter script following existing examples
3. Add usage documentation to this README
4. Submit a pull request

## License

MIT License - Same as the parent project
