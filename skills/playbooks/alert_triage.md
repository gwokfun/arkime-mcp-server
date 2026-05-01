# SOC Alert Triage Playbook

**Use Case:** Security Operations Center (SOC) automation
**Skills Used:** `search_sessions`, `get_session_detail`, `add_tags`, `geo_summary`, `top_talkers`

## Overview

This playbook automates the initial triage of security alerts by enriching them with network context from Arkime. It helps SOC analysts quickly determine the severity and scope of an alert.

## Scenario

A SIEM alert fires indicating suspicious activity from an internal IP address. Instead of manually pivoting through multiple tools, an AI agent equipped with Arkime skills can automatically gather context and generate a triage report.

## Steps

### 1. Gather Alert Context
**Input:** Alert with IP address and timestamp
**Skill:** `search_sessions`

```
Search for all network sessions involving the IP address in the alert time window.

Parameters:
- expression: "ip.src=={alert_ip} || ip.dst=={alert_ip}"
- hours: {alert_time_window}
- limit: 100
- order: "totDataBytes:desc"
```

**Output:** List of sessions showing who the host communicated with, protocols used, and data volume.

### 2. Identify External Destinations
**Skill:** `geo_summary`

```
Get a geographic breakdown of where this host sent traffic.

Parameters:
- expression: "ip.src=={alert_ip}"
- hours: {alert_time_window}
- limit: 20
```

**Output:** List of destination countries ranked by session count.

### 3. Find Top Communication Partners
**Skill:** `top_talkers`

```
Identify the top external IPs this host communicated with.

Parameters:
- field: "destination.ip"
- expression: "ip.src=={alert_ip}"
- hours: {alert_time_window}
- limit: 10
```

**Output:** Top 10 destination IPs by session count.

### 4. Inspect High-Volume Sessions
**Skill:** `get_session_detail`

```
For the top 3 sessions by bytes transferred, get full protocol details.

Parameters:
- node: {session_node}
- session_id: {session_id}
```

**Output:** Full decoded protocol information including HTTP headers, DNS queries, TLS certificates, etc.

### 5. Tag Sessions for Investigation
**Skill:** `add_tags`

```
Tag all sessions from this alert for tracking.

Parameters:
- tags: "alert-{alert_id},triage-{date},needs-review"
- node: {session_node}
- session_id: {session_id}
- segments: "all"
```

**Output:** Confirmation that sessions are tagged.

## Triage Report Template

The AI agent should synthesize the gathered data into a structured report:

```markdown
# Alert Triage Report: {alert_id}

## Summary
- **Alert IP:** {alert_ip}
- **Time Window:** {start} to {end}
- **Total Sessions:** {session_count}
- **Data Transferred:** {total_bytes}
- **Risk Level:** [Low/Medium/High]

## Network Activity
- **Top Destinations:** {top_destinations}
- **Geographic Spread:** {countries_contacted}
- **Protocols Used:** {protocols}
- **Unusual Ports:** {non_standard_ports}

## Key Findings
1. [Finding 1 with session reference]
2. [Finding 2 with session reference]
3. [Finding 3 with session reference]

## Indicators of Compromise (IoCs)
- External IPs: {ioc_ips}
- Domains: {ioc_domains}
- File Hashes: {file_hashes_if_any}

## Recommended Actions
- [ ] Escalate to Tier 2 (Yes/No and why)
- [ ] Block external IPs: {ips_to_block}
- [ ] Isolate host: {alert_ip} (Yes/No and why)
- [ ] Create threat hunt: {hunt_criteria}

## Session Tags
All sessions tagged with: alert-{alert_id}, triage-{date}
```

## Example Conversation

**Alert Input:**
```
SIEM Alert: Possible data exfiltration
Source IP: 192.168.10.55
Timestamp: 2024-03-15 14:30 UTC
Bytes Out: 2.5 GB over 10 minutes
```

**AI Agent Response:**
```
Triaging alert for 192.168.10.55...

Step 1: Searching sessions for 192.168.10.55 in the last hour...
Found 43 sessions, total 2.8 GB transferred.

Step 2: Analyzing geographic destinations...
Top countries: CN (China) - 38 sessions, RU (Russia) - 5 sessions

Step 3: Identifying top communication partners...
Top destination: 203.0.113.42 (38 sessions, 2.5 GB)
Domain: suspicious-cdn.example.com

Step 4: Inspecting high-volume session to 203.0.113.42...
Protocol: HTTPS (port 443)
TLS: Self-signed certificate, issuer: unknown
No HTTP host header detected (suspicious)

Step 5: Tagging sessions...
Tagged 43 sessions with: alert-2024-031501, triage-2024-03-15, needs-review

Risk Assessment: HIGH
Reasons:
1. Large volume to single external IP in China
2. Self-signed TLS certificate
3. No valid HTTP headers (possible tunneling)
4. Atypical for this host (baseline: <50MB/day)

RECOMMENDED ACTIONS:
- IMMEDIATE: Isolate 192.168.10.55 from network
- IMMEDIATE: Block egress to 203.0.113.42
- Create hunt job for TLS self-signed certs to detect similar activity
- Escalate to IR team for host forensics
```

## Integration Examples

### With Claude Desktop (MCP)
The Arkime MCP server is already configured. Just describe the alert in natural language.

### With OpenAI GPT-4
```python
import openai
import json

# Load Arkime function definitions
with open("skills/examples/openai_functions.json") as f:
    functions = json.load(f)

messages = [
    {"role": "system", "content": "You are a SOC analyst. Use Arkime skills to triage alerts."},
    {"role": "user", "content": "Triage this alert: Source IP 192.168.10.55 sent 2.5 GB to external IPs in the last 10 minutes"}
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

agent = initialize_agent(
    tools,
    ChatOpenAI(model="gpt-4"),
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

alert = """
SIEM Alert: Possible data exfiltration
Source IP: 192.168.10.55
Timestamp: 2024-03-15 14:30 UTC
Bytes Out: 2.5 GB over 10 minutes
"""

result = agent.run(f"Triage this security alert:\n{alert}")
print(result)
```

## Customization

Adapt this playbook by:
- Adjusting time windows based on alert retention
- Modifying tagging conventions to match your SOC
- Adding additional enrichment steps (e.g., threat intel lookups)
- Integrating with ticketing systems (JIRA, ServiceNow)
- Customizing risk scoring based on your environment

## Related Playbooks

- [Data Exfiltration Hunt](data_exfiltration_hunt.md) - Follow-up hunting after triage
- [Host Forensics](host_forensics.md) - Deep dive on a compromised host
- [DNS Tunnel Detection](dns_tunnel_detection.md) - Specialized playbook for DNS-based exfiltration
