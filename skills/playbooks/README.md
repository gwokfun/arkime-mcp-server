# Arkime Skills - Scenario Playbooks

This directory contains natural-language playbooks that chain multiple Arkime skills into automated workflows for common security operations, threat hunting, and incident response scenarios.

## Overview

Each playbook provides:
- **Step-by-step investigation workflow** using Arkime skills
- **Analysis questions** to guide the investigation
- **Detection patterns and thresholds** for identifying malicious activity
- **Response actions** for different confidence levels
- **Example AI agent outputs** showing realistic investigations
- **Integration examples** with various agent platforms

## Available Playbooks

### 1. [SOC Alert Triage](alert_triage.md)
**Use Case:** Security Operations Center automation
**Skills:** `search_sessions`, `get_session_detail`, `add_tags`, `geo_summary`, `top_talkers`

Automate the initial triage of security alerts by enriching them with network context. Helps SOC analysts quickly assess alert severity and scope.

**When to use:**
- SIEM alert fires for suspicious activity
- EDR alert requires network context
- IDS/IPS signature match needs investigation
- Anomaly detection system flags unusual behavior

**Typical runtime:** 2-5 minutes (automated)

---

### 2. [Data Exfiltration Hunt](data_exfiltration_hunt.md)
**Use Case:** Threat Hunting
**Skills:** `external_connections`, `geo_summary`, `top_talkers`, `connections_graph`, `create_hunt`

Proactively hunt for data exfiltration activity by identifying unusual outbound traffic patterns, high-volume transfers, and connections to suspicious destinations.

**When to use:**
- Routine threat hunting (weekly/monthly)
- Post-incident sweep for additional compromises
- Insider threat investigation
- Compliance audit preparation

**Typical runtime:** 5-15 minutes (automated)

---

### 3. [Host Forensics](host_forensics.md)
**Use Case:** Incident Response
**Skills:** `search_sessions`, `unique_destinations`, `dns_lookups`, `get_session_packets`, `get_session_detail`

Comprehensive forensic investigation of a compromised host. Reconstructs the network timeline, identifies C2 communication, detects lateral movement, and assesses data exfiltration.

**When to use:**
- Host confirmed compromised (via EDR or other means)
- Deep dive required after initial triage
- Post-mortem analysis of an incident
- Evidence collection for legal proceedings

**Typical runtime:** 15-45 minutes (semi-automated with analyst review)

---

### 4. [DNS Tunnel Detection](dns_tunnel_detection.md)
**Use Case:** Threat Hunting
**Skills:** `dns_lookups`, `top_talkers`, `create_hunt`, `get_session_detail`

Detect DNS tunneling used for C2 communication or data exfiltration. Identifies high-entropy domains, unusual query patterns, and TXT record abuse.

**When to use:**
- Suspicious DNS traffic volume detected
- Investigating potential C2 channels
- Baseline DNS behavior analysis
- Routine hunt for covert channels

**Typical runtime:** 5-10 minutes (automated)

---

## Playbook Structure

Each playbook follows this structure:

```markdown
# Playbook Name

**Use Case:** [soc | threat_hunting | incident_response | network_monitoring | compliance]
**Skills Used:** List of Arkime skills

## Overview
Brief description of the playbook's purpose

## Scenario
Real-world situation when this playbook applies

## Steps
Detailed step-by-step workflow with:
- Skill to use
- Parameters to pass
- Analysis questions
- What to look for

## Response Actions
Recommended actions based on findings:
- Immediate (high-confidence detections)
- Investigation (medium-confidence)
- Proactive (hunting)

## Example AI Agent Workflow
Sample conversation showing realistic agent output

## Integration Examples
Code examples for different platforms

## Related Playbooks
Links to related workflows
```

## Using Playbooks with AI Agents

### With Claude Desktop (MCP)

The Arkime MCP server is already configured. Just describe the scenario in natural language:

```
You: "Use the SOC alert triage playbook to investigate alert #2024-03-15-001 for IP 192.168.10.55"

Claude: I'll follow the SOC alert triage playbook to investigate...
[Agent executes playbook steps automatically]
```

### With OpenAI GPT-4

```python
import openai
import json

# Load skills
with open("../examples/openai_functions.json") as f:
    functions = json.load(f)

# Load playbook
with open("alert_triage.md") as f:
    playbook = f.read()

messages = [
    {"role": "system", "content": f"You are a SOC analyst. Follow this playbook:\n\n{playbook}"},
    {"role": "user", "content": "Triage alert: IP 192.168.10.55 sent 2.5 GB to external IPs"}
]

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=messages,
    functions=functions,
    function_call="auto"
)
```

### With LangChain

```python
from langchain_agent import ArkimeSkillsAdapter
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI

adapter = ArkimeSkillsAdapter()
tools = adapter.get_tools_by_use_case("soc")

# Load playbook as system context
with open("playbooks/alert_triage.md") as f:
    playbook = f.read()

agent = initialize_agent(
    tools,
    ChatOpenAI(model="gpt-4", temperature=0),
    agent=AgentType.OPENAI_FUNCTIONS,
    agent_kwargs={"system_message": f"Follow this playbook:\n{playbook}"}
)

result = agent.run("Triage alert for IP 192.168.10.55")
```

### With Jupyter Notebooks

Load playbooks as investigation templates in Jupyter:

```python
import yaml
from IPython.display import Markdown, display

# Display playbook
with open("playbooks/host_forensics.md") as f:
    display(Markdown(f.read()))

# Follow playbook steps
from arkime_mcp_server.client import ArkimeClient
client = ArkimeClient(...)

# Step 1: Gather all sessions
compromised_ip = "192.168.10.55"
sessions = client.get_sessions(
    expression=f"ip.src=={compromised_ip} || ip.dst=={compromised_ip}",
    date=168,
    length=200
)

# Continue with playbook steps...
```

## Customizing Playbooks

### Adjust for Your Environment

**Time Windows:**
```python
# High-traffic network: shorter windows
hours = 1

# Compliance/audit: longer retention
hours = 168  # 7 days
hours = 720  # 30 days
```

**Thresholds:**
```python
# Adjust based on baseline
NORMAL_DNS_QUERIES_PER_DAY = 300
SUSPICIOUS_MULTIPLIER = 10  # 3000 queries = alert

# Per-department baselines
SALES_DEPT_OUTBOUND_GB_PER_DAY = 2.0
ENGINEERING_DEPT_OUTBOUND_GB_PER_DAY = 10.0
```

**Tag Conventions:**
```python
# Match your SOC tagging standards
tags = "incident-{incident_id},analyst-{analyst_name},severity-{level}"
```

### Create Custom Playbooks

Template for new playbooks:

```markdown
# [Your Playbook Name]

**Use Case:** [soc | threat_hunting | incident_response | network_monitoring | compliance]
**Skills Used:** skill1, skill2, skill3

## Overview
What problem does this solve?

## Scenario
When should someone use this playbook?

## Steps

### 1. [First Step Name]
**Skill:** `skill_name`

\```
Parameters:
- param1: value1
- param2: value2
\```

**Analysis:** What to look for in the results

### 2. [Second Step Name]
...

## Response Actions
What to do based on findings

## Example
Sample agent workflow

## Integration
Code examples
```

## Automated Playbook Execution

### Scheduled Hunting

Run playbooks on a schedule:

```python
import schedule
import time
from langchain_agent import ArkimeSkillsAdapter
from langchain.agents import initialize_agent
from langchain_openai import ChatOpenAI

def run_daily_exfil_hunt():
    adapter = ArkimeSkillsAdapter()
    tools = adapter.get_tools_by_use_case("threat_hunting")
    agent = initialize_agent(tools, ChatOpenAI(model="gpt-4"))

    result = agent.run("Execute the data exfiltration hunt playbook for the last 24 hours")

    # Send to Slack/Email/SIEM
    notify_soc(result)

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(run_daily_exfil_hunt)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Alert-Driven Playbooks

Trigger playbooks from SIEM alerts:

```python
# Listen for SIEM webhooks
from flask import Flask, request
app = Flask(__name__)

@app.route('/siem/alert', methods=['POST'])
def handle_alert():
    alert = request.json

    # Route to appropriate playbook
    if alert['type'] == 'data_exfiltration':
        run_playbook('data_exfiltration_hunt.md', alert)
    elif alert['type'] == 'lateral_movement':
        run_playbook('host_forensics.md', alert)

    return {'status': 'playbook_launched'}
```

## Playbook Metrics

Track playbook effectiveness:

```python
metrics = {
    "playbook": "alert_triage",
    "executions": 142,
    "avg_runtime_seconds": 185,
    "true_positives": 12,
    "false_positives": 8,
    "escalated_to_ir": 4,
    "time_saved_hours": 23.5  # vs manual triage
}
```

## Contributing New Playbooks

To contribute a new playbook:

1. Identify a repeatable security workflow
2. Break it down into Arkime skill calls
3. Write the playbook using the template
4. Test with real or simulated data
5. Document expected outputs and edge cases
6. Add integration examples
7. Submit a pull request

## Related Documentation

- [Skills Manifest](../arkime_skills.yaml) - All available skills
- [Agent Integration Examples](../examples/) - Platform-specific adapters
- [Skills Validation](../tests/validate_skills.py) - Testing tools
- [Main README](../../README.md) - Project overview

## License

MIT License - Same as the parent project
