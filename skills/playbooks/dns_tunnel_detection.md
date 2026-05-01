# DNS Tunnel Detection Playbook

**Use Case:** Threat Hunting
**Skills Used:** `dns_lookups`, `top_talkers`, `create_hunt`, `get_session_detail`

## Overview

DNS tunneling is a technique where attackers exfiltrate data or establish C2 communication by encoding information in DNS queries and responses. This playbook helps detect DNS tunneling activity.

## DNS Tunneling Indicators

**Query Patterns:**
- Unusually long subdomain names (>50 characters)
- High entropy in subdomain strings (random-looking)
- Large number of queries to the same domain
- CNAME, TXT, or NULL record types (less common)
- Queries with base32/base64 encoded patterns

**Volume Patterns:**
- High query rate from a single host
- Many unique subdomains under one domain
- Regular intervals between queries (beaconing)

**Response Patterns:**
- Large TXT records (>255 bytes)
- Suspicious A record patterns (data encoded in IPs)
- CNAME chains

## Steps

### 1. Identify High-Volume DNS Query Sources
**Skill:** `top_talkers`

```
Find hosts making the most DNS queries.

Parameters:
- field: "source.ip"
- expression: "port.dst==53"
- hours: 24
- limit: 20
```

**Baseline comparison:**
Normal workstation: 100-500 DNS queries/day
Suspicious: >5,000 queries/day

### 2. Find Domains with Many Subdomains
**Skill:** `top_talkers`

```
Identify domains with many unique queries.

Parameters:
- field: "host.dns"
- hours: 24
- limit: 50
```

**Analysis:**
- Look for domains with >100 unique subdomains
- Check domain registration date (newly registered = suspicious)
- Verify domain is not a legitimate CDN or cloud service

### 3. Analyze Query Patterns
**Skill:** `dns_lookups`

```
Get detailed DNS queries for suspicious domains.

Parameters:
- domain: "*.suspicious-domain.com"
- hours: 24
- limit: 100
```

**Pattern analysis:**
```
Normal:      www.example.com, api.example.com, cdn.example.com
Suspicious:  a8f3d9e2c1b7.example.com, x7f2k9m4n8p1.example.com
```

### 4. Hunt for Base64/Base32 Patterns
**Skill:** `create_hunt`

```
Search for base64/base32 encoded data in DNS queries.

Parameters:
- name: "DNS-Base64-Hunt"
- search: "([A-Za-z0-9+/]{4}){10,}="  # Base64 pattern
- hunt_type: "raw"
- src: true
- dst: false
```

### 5. Inspect Suspicious Sessions
**Skill:** `get_session_detail`

```
Get full details of suspicious DNS sessions.

Parameters:
- node: {session_node}
- session_id: {dns_session_id}
```

**Look for:**
- Query types: TXT, NULL, CNAME (uncommon but used for tunneling)
- Response sizes: Large TXT records (>512 bytes)
- TTL values: Very low TTL (rapid cache expiration)

## Detection Rules

### High-Entropy Subdomains
```python
import math
from collections import Counter

def calculate_entropy(string):
    """Calculate Shannon entropy of a string."""
    if not string:
        return 0
    entropy = 0
    for count in Counter(string).values():
        p = count / len(string)
        entropy -= p * math.log2(p)
    return entropy

# Thresholds:
# Normal domain: entropy < 3.5
# Suspicious: entropy > 4.0
# High confidence tunnel: entropy > 4.5

subdomain = "a8f3d9e2c1b7k9m4n8p1"
if calculate_entropy(subdomain) > 4.0:
    print("Possible DNS tunnel")
```

### Query Rate Anomaly
```python
# Normal rate: <10 queries/minute
# Beaconing: 20-60 queries/minute (regular intervals)
# Exfil: >100 queries/minute (burst pattern)

if queries_per_minute > 100:
    alert("Possible DNS tunneling - high query rate")
```

### Subdomain Length
```python
# Normal: <30 characters
# Suspicious: >50 characters
# High confidence: >100 characters

if len(subdomain) > 50:
    alert("Unusually long DNS query")
```

## Example Investigation

**Scenario:** SOC analyst notices abnormal DNS traffic from 192.168.10.77

```
User: "Investigate DNS activity from 192.168.10.77 for possible tunneling"

Agent: Starting DNS tunnel investigation for 192.168.10.77...

Step 1: Analyzing DNS query volume...
Host 192.168.10.77 made 12,456 DNS queries in the last 24 hours.
ANOMALY: Normal baseline for this host is ~300 queries/day.
4,056% increase detected.

Step 2: Identifying queried domains...
Top domains by query count:
1. tunnel-exfil.xyz - 11,923 queries (96% of traffic)
2. google.com - 245 queries
3. microsoft.com - 178 queries
4. cloudflare.com - 110 queries

CRITICAL: tunnel-exfil.xyz accounts for 96% of DNS traffic.
Domain registered: 3 days ago (newly registered)
Registrar: Privacy Protected

Step 3: Analyzing query patterns for tunnel-exfil.xyz...
Sample queries:
- a8f3d9e2c1b7k9m4n8p1q5r2s6t3u7v4.tunnel-exfil.xyz
- w1x5y9z2a6b3c7d4e8f1g5h9i2j6k3l7.tunnel-exfil.xyz
- m8n4o7p1q5r9s2t6u3v7w4x8y1z5a9b2.tunnel-exfil.xyz

Entropy analysis: 4.72 (HIGH - strong indicator of tunneling)
Average subdomain length: 84 characters (EXTREME)
Pattern: Base32-like encoding detected

Step 4: Inspecting DNS session details...
Query type breakdown:
- TXT records: 89% (unusual, typically <5%)
- A records: 11%

TXT record sizes:
- Average: 487 bytes (very large for TXT)
- Max: 512 bytes (maximum UDP size)

Step 5: Timeline analysis...
Query intervals: 1-2 seconds (highly regular)
Pattern: Continuous for last 18 hours with no gaps
Assessment: Active exfiltration in progress

CONFIRMED DNS TUNNEL DETECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Host: 192.168.10.77
C2 Domain: tunnel-exfil.xyz
Method: TXT record exfiltration
Confidence: HIGH (multiple strong indicators)

Indicators:
✓ 4,056% increase in DNS queries
✓ 96% of queries to single newly-registered domain
✓ High entropy subdomains (4.72)
✓ Unusually long subdomains (84 chars avg)
✓ TXT record abuse (89% of queries)
✓ Large TXT responses (avg 487 bytes)
✓ Regular beaconing (1-2 second intervals)

Estimated data exfiltrated: ~5.8 MB over 18 hours

IMMEDIATE ACTIONS:
1. BLOCK domain: tunnel-exfil.xyz at DNS level
2. ISOLATE host: 192.168.10.77
3. BLOCK egress DNS: Configure firewall to only allow DNS to authorized resolvers
4. INVESTIGATE: Check endpoint for malware
5. HUNT: Search for other hosts querying tunnel-exfil.xyz
6. PRESERVE: Export all DNS PCAPs for forensics
```

## Prevention & Detection

### DNS Firewall Rules
```
# Block suspicious patterns at DNS resolver
- Block newly registered domains (<7 days)
- Block domains with high subdomain entropy
- Rate limit DNS queries per host (>1000/hour = block)
- Block TXT/NULL queries to non-enterprise domains
```

### SIEM Detection Rules

**Splunk:**
```spl
index=arkime sourcetype=arkime_sessions port.dst=53
| stats count by source.ip, host.dns
| where count > 1000
| table source.ip, host.dns, count
| sort -count
```

**Elastic:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"port.dst": 53}},
        {"range": {"@timestamp": {"gte": "now-24h"}}}
      ]
    }
  },
  "aggs": {
    "by_host": {
      "terms": {"field": "source.ip", "size": 100},
      "aggs": {
        "query_count": {"value_count": {"field": "host.dns"}}
      }
    }
  }
}
```

### Hunting Queries

```python
from arkime_mcp_server.client import ArkimeClient

client = ArkimeClient(...)

# Hunt for high-volume DNS sources
result = client.get_unique(
    field="source.ip",
    expression="port.dst==53",
    date=24
)

for ip, count in result.items():
    if count > 5000:
        print(f"Investigate {ip}: {count} DNS queries")
```

## Known DNS Tunneling Tools

Be aware of these common tools:
- **Iodine** - IPv4 over DNS tunnel
- **Dnscat2** - C2 over DNS
- **DNSExfiltrator** - PowerShell-based data exfil
- **Cobalt Strike DNS Beacon** - Commercial C2
- **dns2tcp** - TCP over DNS tunnel

Each has signature patterns that can be detected.

## Response Playbook

**Confirmed Tunneling:**
1. Block the domain at authoritative DNS
2. Isolate the source host
3. Restrict DNS to approved resolvers only
4. Perform endpoint forensics
5. Reset user credentials
6. Hunt for additional compromised hosts

**Suspected but Unconfirmed:**
1. Tag sessions for monitoring
2. Increase DNS logging verbosity
3. Deploy DNS query analytics
4. Monitor for pattern evolution

## Integration Examples

### Automated Daily Hunt
```python
from langchain_agent import ArkimeSkillsAdapter
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI

adapter = ArkimeSkillsAdapter()
tools = adapter.get_tools_by_use_case("threat_hunting")

agent = initialize_agent(tools, ChatOpenAI(model="gpt-4"))

# Daily scheduled job
result = agent.run("""
Perform a DNS tunneling hunt:
1. Find top DNS query sources
2. Identify domains with >100 unique subdomains
3. Calculate entropy for top domains
4. Flag any with entropy >4.0
5. Generate investigation report
""")

# Email to SOC
send_email(to="soc@company.com", subject="DNS Tunnel Hunt Results", body=result)
```

## Related Playbooks

- [Data Exfiltration Hunt](data_exfiltration_hunt.md) - Broader exfiltration detection
- [Host Forensics](host_forensics.md) - Deep dive on compromised hosts
- [SOC Alert Triage](alert_triage.md) - Initial triage of DNS alerts
