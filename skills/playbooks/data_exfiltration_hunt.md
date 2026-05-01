# Data Exfiltration Hunt Playbook

**Use Case:** Threat Hunting
**Skills Used:** `external_connections`, `geo_summary`, `top_talkers`, `connections_graph`, `create_hunt`

## Overview

This playbook guides threat hunters through a systematic search for potential data exfiltration activity across the network. It identifies unusual outbound traffic patterns that may indicate data theft.

## Scenario

A threat hunter suspects that an insider or compromised account may be exfiltrating sensitive data. This playbook helps identify suspicious external transfers and trace them back to the source.

## Hunting Hypothesis

"If data is being exfiltrated, we will observe:
- Unusually large outbound transfers to external IPs
- Traffic to unexpected geographic locations
- Connections to non-standard services or ports
- Encrypted tunnels or obfuscated protocols"

## Steps

### 1. Identify High-Volume External Connections
**Skill:** `external_connections`

```
Find all sessions to external IPs, sorted by bytes transferred.

Parameters:
- hours: 24  # Look back 24 hours
- limit: 100
```

**Analysis Questions:**
- Are there any outlier sessions with >100 MB transferred?
- Are these transfers to known cloud services or suspicious IPs?
- What protocols were used?

### 2. Geographic Anomaly Detection
**Skill:** `geo_summary`

```
Break down external traffic by destination country.

Parameters:
- hours: 24
- limit: 30
```

**Analysis Questions:**
- Are there connections to countries where we don't have business operations?
- Are there unexpected changes from baseline (e.g., sudden spike to a new country)?
- Are high-risk countries (known for hosting malware infrastructure) present?

### 3. Identify Heavy Uploaders
**Skill:** `top_talkers`

```
Find the top internal IPs by outbound bytes.

Parameters:
- field: "source.ip"
- expression: "ip.dst!=10.0.0.0/8 && ip.dst!=172.16.0.0/12 && ip.dst!=192.168.0.0/16"
- hours: 24
- limit: 20
```

**Analysis Questions:**
- Are the top uploaders expected (e.g., proxy servers, backup servers)?
- Are any workstations in the top list?
- Compare against baseline - any new heavy uploaders?

### 4. Analyze External Communication Patterns
**Skill:** `connections_graph`

```
Generate a network graph of internal to external connections.

Parameters:
- expression: "ip.dst!=10.0.0.0/8 && ip.dst!=172.16.0.0/12 && ip.dst!=192.168.0.0/16"
- hours: 24
- src_field: "source.ip"
- dst_field: "ip.dst:port"
- limit: 100
```

**Analysis Questions:**
- Are there internal hosts connecting to many external destinations (possible C2)?
- Are there external IPs receiving connections from many internal hosts (possible data collection point)?
- Are there unusual port combinations?

### 5. Hunt for Specific IoCs
**Skill:** `create_hunt`

If suspicious patterns are found, create hunt jobs to search packet payloads.

```
Search for sensitive data patterns in packet payloads.

Parameters:
- name: "SSN Pattern Hunt"
- search: "\\d{3}-\\d{2}-\\d{4}"  # Social Security Number pattern
- hunt_type: "raw"
- src: true
- dst: false
```

Other hunt targets:
- Credit card patterns: `\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}`
- Internal domain names: `(confidential|internal|secret)\\.company\\.com`
- File signatures: `MZ\\x90\\x00` (PE executable), `%PDF` (PDF files)

### 6. Investigate Encryption Tunnels
**Skill:** `top_talkers`

```
Look for non-standard TLS usage or VPN tunnels.

Parameters:
- field: "destination.port"
- expression: "port.dst!=443 && port.dst!=22 && tls.ja3!=*"
- hours: 24
- limit: 20
```

**Analysis Questions:**
- Are there unexpected ports using TLS?
- Are there VPN connections that aren't to authorized VPN gateways?

## Indicators of Data Exfiltration

High-confidence indicators:
1. **Large single session** (>1 GB) to an external IP, especially outside business hours
2. **Sustained upload** to a single external destination over multiple sessions
3. **Unusual protocols** - Non-HTTP/HTTPS traffic on port 443, DNS tunneling
4. **Encrypted transfer** to a previously unseen external IP
5. **Geographic anomaly** - First connection to a high-risk country

Medium-confidence indicators:
1. Multiple smaller transfers to the same external IP
2. Connections to cloud storage services (Dropbox, Google Drive, AWS S3) from non-authorized users
3. Encrypted traffic without proper TLS certificates

## Response Actions

### Immediate (High-Confidence Detection)
1. **Isolate the source host** from the network
2. **Block the external destination** IP at the firewall
3. **Preserve evidence** - Tag all sessions, export PCAPs
4. **Escalate to incident response team**

### Investigation (Medium-Confidence Detection)
1. **Tag sessions** for tracking: `potential-exfil`, `needs-review`
2. **Gather more context** - User activity logs, endpoint logs
3. **Compare with baseline** - Is this user's typical behavior?
4. **Interview the user** (if appropriate)

### Proactive Hunting
1. **Create scheduled hunts** for known IoC patterns
2. **Establish baselines** for normal external traffic volume by user/host
3. **Set up alerts** for statistical anomalies (e.g., >5 GB outbound in 1 hour)

## Example AI Agent Workflow

```
User: "Hunt for potential data exfiltration in the last 24 hours"

Agent: Starting data exfiltration hunt...

Step 1: Finding high-volume external connections...
Identified 12 sessions >100 MB to external IPs.
Top session: 1.8 GB from 192.168.10.55 to 203.0.113.42 (China)

Step 2: Analyzing geographic patterns...
Unusual: 15 sessions to China (CN) - not typical for this network.
Also detected: 8 sessions to Russia (RU), 3 to North Korea (KP)

Step 3: Identifying heavy uploaders...
Top uploader: 192.168.10.55 (2.1 GB outbound)
This host typically uploads <50 MB/day (based on 7-day baseline)
ANOMALY DETECTED: 4200% increase

Step 4: Analyzing connection graph...
192.168.10.55 connected to 8 external IPs in China and Russia
All connections used port 443 with TLS
Certificate check: 5/8 used self-signed certificates (suspicious)

Step 5: Creating hunt for sensitive data...
Created hunt job "SSN-hunt-2024-03-15" to search for Social Security Numbers
Status: Running (will scan all traffic from 192.168.10.55)

CRITICAL FINDING:
Host 192.168.10.55 is exhibiting strong indicators of data exfiltration:
- 4200% increase in outbound traffic
- Connections to high-risk countries (CN, RU, KP)
- Use of self-signed TLS certificates (possible tunneling)
- Sustained large transfers over multiple sessions

RECOMMENDED IMMEDIATE ACTIONS:
1. ISOLATE 192.168.10.55 from network
2. BLOCK external IPs: 203.0.113.42, 198.51.100.15, 198.51.100.89
3. PRESERVE EVIDENCE: Export all PCAPs for 192.168.10.55 sessions
4. ESCALATE to incident response team
5. INVESTIGATE user account on 192.168.10.55 (check AD logs, endpoint logs)

Would you like me to:
- Tag all suspicious sessions?
- Get detailed protocol information for the top 3 sessions?
- Create additional hunt jobs for file signatures?
```

## Integration Examples

### Automated Hunting with LangChain
```python
from langchain_agent import ArkimeSkillsAdapter
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI

adapter = ArkimeSkillsAdapter()
tools = adapter.get_tools_by_use_case("threat_hunting")

agent = initialize_agent(
    tools,
    ChatOpenAI(model="gpt-4"),
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# Run daily exfiltration hunt
result = agent.run("""
Perform a data exfiltration hunt for the last 24 hours:
1. Find high-volume external connections
2. Identify geographic anomalies
3. Find heavy uploaders
4. Generate a summary report with risk assessment
""")

# Could be scheduled via cron or integrated with SIEM
```

### Jupyter Notebook Investigation
```python
import yaml
from arkime_mcp_server.client import ArkimeClient

client = ArkimeClient(url="http://arkime:8005", user="analyst", password="***")

# Step 1: High-volume external connections
external = client.get_sessions(
    expression="ip.dst!=10.0.0.0/8 && ip.dst!=172.16.0.0/12 && ip.dst!=192.168.0.0/16",
    date=24,
    length=100,
    order="totDataBytes:desc"
)

# Analyze and visualize
import pandas as pd
df = pd.DataFrame(external['data'])
df[['source.ip', 'destination.ip', 'totDataBytes', 'destination.geo.country']].head(10)
```

## Tuning and Customization

**For high-traffic networks:**
- Increase the byte threshold for "high-volume" sessions
- Focus on rate of change rather than absolute volume
- Create per-department or per-user baselines

**For low-and-slow exfiltration:**
- Extend the time window to 7 days or 30 days
- Look for sustained small transfers to the same destination
- Track cumulative volume per destination over time

**For cloud-heavy environments:**
- Whitelist known cloud provider IP ranges (AWS, Azure, GCP)
- Focus on unknown cloud services or personal cloud storage
- Monitor for shadow IT usage

## Related Playbooks

- [SOC Alert Triage](alert_triage.md) - Initial triage of exfiltration alerts
- [Host Forensics](host_forensics.md) - Deep dive after detecting exfiltration
- [DNS Tunnel Detection](dns_tunnel_detection.md) - DNS-based exfiltration hunting
- [Cluster Health Report](cluster_health_report.md) - Ensure capture is working during hunts
