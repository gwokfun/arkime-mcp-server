# Host Forensics Playbook

**Use Case:** Incident Response
**Skills Used:** `search_sessions`, `unique_destinations`, `dns_lookups`, `get_session_packets`, `get_session_detail`

## Overview

This playbook guides incident responders through a comprehensive forensic investigation of a potentially compromised host using network traffic captured by Arkime.

## Scenario

A host has been identified as compromised (via EDR alert, SIEM correlation, or threat hunting). This playbook helps reconstruct the network timeline and identify indicators of compromise.

## Investigation Goals

1. **Timeline reconstruction** - When did the compromise occur?
2. **Command & Control (C2)** - What external infrastructure did the attacker use?
3. **Lateral movement** - Did the attacker move to other hosts?
4. **Data exfiltration** - What data was stolen?
5. **Persistence mechanisms** - How did the attacker maintain access?

## Steps

### Phase 1: Initial Scoping

#### 1.1 Gather All Sessions for the Host
**Skill:** `search_sessions`

```
Get complete network activity for the compromised host.

Parameters:
- expression: "ip.src=={compromised_ip} || ip.dst=={compromised_ip}"
- hours: 168  # 7 days (adjust based on incident timeline)
- limit: 200
- order: "firstPacket:asc"  # Chronological order
```

**Analysis:**
- What was the first unusual session?
- What was the last session before isolation?
- Total data volume transferred

#### 1.2 Identify All External Destinations
**Skill:** `unique_destinations`

```
List every external IP the host contacted.

Parameters:
- source_ip: {compromised_ip}
- hours: 168
- limit: 100
```

**Analysis:**
- How many unique external IPs?
- Are any known malicious (check threat intel)?
- Are there unusual ports or protocols?

#### 1.3 DNS Query Analysis
**Skill:** `dns_lookups`

```
Review all DNS queries made by the host.

Parameters:
- source_ip: {compromised_ip}
- hours: 168
- limit: 100
```

**Indicators to look for:**
- DGA (Domain Generation Algorithm) patterns
- Recently registered domains
- Suspicious TLDs (.tk, .ml, .ga, .cf, .pw, .top)
- Domains with high entropy names
- DNS queries to known C2 domains

### Phase 2: C2 Communication Analysis

#### 2.1 Identify Beaconing Behavior
**Skill:** `search_sessions`

```
Look for periodic connections (C2 beacons).

Parameters:
- expression: "ip.src=={compromised_ip}"
- hours: 168
- limit: 200
- order: "firstPacket:asc"
```

**Analysis technique:**
Calculate time deltas between sessions to the same destination:
- Regular intervals (e.g., every 60 seconds) = likely C2 beacon
- Jitter patterns common in malware: 60±5 seconds
- Sleep timers: large gaps followed by bursts of activity

#### 2.2 Inspect C2 Session Details
**Skill:** `get_session_detail`

```
Get full protocol details for suspected C2 sessions.

Parameters:
- node: {session_node}
- session_id: {suspected_c2_session_id}
```

**Look for:**
- HTTP User-Agent strings (generic or unusual)
- TLS certificate details (self-signed, invalid CN)
- HTTP headers (missing standard headers, unusual content-type)
- URI patterns (base64 encoded data, suspicious paths)

#### 2.3 Extract C2 Payloads
**Skill:** `get_session_packets`

```
Retrieve packet-level data for C2 sessions.

Parameters:
- node: {session_node}
- session_id: {c2_session_id}
```

**Extract:**
- Command strings sent to the host
- Malware configuration data
- Encryption keys or parameters
- File downloads or uploads

### Phase 3: Lateral Movement Detection

#### 3.1 Check for Internal Scanning
**Skill:** `search_sessions`

```
Look for scanning activity from the compromised host.

Parameters:
- expression: "ip.src=={compromised_ip} && ip.dst==10.0.0.0/8"
- hours: 168
- limit: 200
```

**Indicators:**
- Many failed connections (RST packets)
- Connections to many sequential IPs
- Port scanning (many different destination ports)
- Common attack ports: 445 (SMB), 3389 (RDP), 22 (SSH), 5985 (WinRM)

#### 3.2 Identify Lateral Movement Destinations
**Skill:** `top_talkers`

```
Find internal hosts the compromised system connected to.

Parameters:
- field: "destination.ip"
- expression: "ip.src=={compromised_ip} && (ip.dst==10.0.0.0/8 || ip.dst==172.16.0.0/12 || ip.dst==192.168.0.0/16)"
- hours: 168
- limit: 50
```

**Prioritize investigation:**
- Servers (especially domain controllers, file servers)
- Unusual ports (e.g., WMI, PS remoting)
- High session counts (active exploitation attempts)

#### 3.3 Check for Credential Theft
**Skill:** `dns_lookups`

```
Look for network-based credential harvesting.

Parameters:
- source_ip: {compromised_ip}
- domain: "*admin*"  # Look for administrative service queries
- hours: 168
```

Also search for:
- LDAP queries (port 389/636)
- Kerberos traffic (port 88)
- NTLM authentication (unusual patterns)

### Phase 4: Data Exfiltration Assessment

#### 4.1 Identify Large Outbound Transfers
**Skill:** `search_sessions`

```
Find sessions with large data transfers.

Parameters:
- expression: "ip.src=={compromised_ip} && ip.dst!=10.0.0.0/8 && ip.dst!=172.16.0.0/12 && ip.dst!=192.168.0.0/16"
- hours: 168
- limit: 100
- order: "totDataBytes:desc"
```

**Analysis:**
- Total data exfiltrated
- Exfiltration targets (IPs, domains, countries)
- Protocols used (HTTPS, DNS, ICMP)

#### 4.2 Analyze Exfiltration Channels
**Skill:** `get_session_detail`

For top outbound sessions, get protocol details to identify:
- Cloud storage uploads (Dropbox, Google Drive, AWS S3)
- Pastebin or file sharing services
- Attacker-controlled servers
- DNS tunneling
- ICMP tunneling

### Phase 5: Timeline Reconstruction

#### 5.1 Build Chronological Session List
**Skill:** `search_sessions`

```
Get all sessions in chronological order.

Parameters:
- expression: "ip.src=={compromised_ip} || ip.dst=={compromised_ip}"
- hours: 168
- limit: 200
- order: "firstPacket:asc"
```

#### 5.2 Correlate with Other Data Sources

Cross-reference Arkime sessions with:
- EDR/Endpoint logs (process execution, file writes)
- Authentication logs (successful/failed logins)
- Firewall logs (blocked connections)
- SIEM alerts

## Timeline Template

```markdown
# Incident Timeline: {compromised_ip}

## Initial Compromise (Estimated)
**{timestamp}**: First suspicious session detected
- Destination: {initial_c2_ip} ({country})
- Protocol: {protocol}
- Evidence: {description}

## Command & Control
**{timestamp}**: C2 beaconing begins
- C2 Server: {c2_domain} / {c2_ip}
- Beacon Interval: {interval} seconds
- Total C2 sessions: {count}

## Reconnaissance
**{timestamp}**: Internal network scanning detected
- Scanned subnets: {subnets}
- Scanned ports: {ports}
- Targets identified: {target_ips}

## Lateral Movement
**{timestamp}**: Lateral movement to {target_ip}
- Protocol: {protocol} (e.g., SMB, RDP, WinRM)
- Credential used: {username} (if known)
- Success: {yes/no}

**{timestamp}**: Lateral movement to {target_ip_2}
...

## Data Exfiltration
**{timestamp}**: Large outbound transfer detected
- Destination: {exfil_ip} ({country})
- Data volume: {bytes}
- Protocol: {protocol}
- Suspected data: {description}

## Persistence Activity
**{timestamp}**: DNS queries to C2 domain resume after reboot
- Evidence: Gap in activity followed by C2 beacon resumption

## Containment
**{timestamp}**: Host isolated from network
- Last C2 beacon: {timestamp}
- Last external connection: {timestamp}
```

## IoC Extraction

Extract and document all IoCs:

**Network IoCs:**
- C2 IP addresses
- C2 domains
- Malicious file download URLs
- Exfiltration destination IPs

**Behavioral IoCs:**
- Beacon intervals
- User-Agent strings
- TLS certificate fingerprints (JA3 hashes)
- HTTP URI patterns
- DNS query patterns

## Response Actions

### Immediate
1. ✅ **Isolate the host** - Already done
2. **Block C2 infrastructure** - Add firewall rules for all C2 IPs/domains
3. **Hunt for other victims** - Search for connections to C2 infrastructure from other hosts
4. **Preserve evidence** - Export PCAPs for all relevant sessions

### Investigation
5. **Endpoint forensics** - Disk image, memory dump, log collection
6. **Credential reset** - Force password reset for all accounts on compromised host
7. **Lateral movement check** - Investigate all hosts the compromised system connected to

### Recovery
8. **Reimage the host** - Do not attempt to clean, rebuild from scratch
9. **Threat intel sharing** - Submit IoCs to threat sharing platforms
10. **Post-incident review** - Document lessons learned

## Example AI Agent Workflow

```
User: "Perform forensic analysis on compromised host 192.168.10.55"

Agent: Starting forensic investigation for 192.168.10.55...

Phase 1: Initial Scoping
━━━━━━━━━━━━━━━━━━━━━━━━━
Gathering all sessions for 192.168.10.55 over last 7 days...
Found 287 total sessions (158 outbound, 129 inbound)
Total data: 3.2 GB out, 890 MB in

Identifying external destinations...
Contacted 43 unique external IPs across 8 countries
Suspicious: 12 IPs have no reverse DNS, 5 self-signed TLS certs

Analyzing DNS queries...
Made 156 DNS queries, including:
- 48 queries to legitimate services (google.com, microsoft.com)
- 23 queries to suspicious domains with high entropy
- 1 query to known malware domain: evil-c2.example.com (CRITICAL)

Phase 2: C2 Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━
Identified beaconing pattern to 203.0.113.42:
- 67 sessions with avg interval: 58 seconds (jitter ±3s)
- Protocol: HTTPS with self-signed certificate
- User-Agent: "Mozilla/5.0" (generic, suspicious)

Extracted C2 command from packet data:
Session 3: "download payload2.exe"
Session 8: "upload C:\Users\*\Documents\*.xlsx"
Session 12: "scan 192.168.10.0/24 port:445"

Phase 3: Lateral Movement
━━━━━━━━━━━━━━━━━━━━━━━━━
Detected internal scanning:
- Scanned 192.168.10.0/24 on port 445 (SMB)
- 254 connection attempts in 2 minutes
- 3 successful connections: .55 → .10, .55 → .15, .55 → .20

Lateral movement confirmed:
- SMB session to 192.168.10.10 (fileserver01)
- RDP session to 192.168.10.15 (workstation02)
- Duration: 45 minutes each, likely successful compromise

Phase 4: Data Exfiltration
━━━━━━━━━━━━━━━━━━━━━━━━━
Large outbound transfers detected:
Session to 198.51.100.15: 2.1 GB over HTTPS
- TLS SNI: "attacker-exfil-server.net"
- Duration: 18 minutes
- Likely exfiltrated data from fileserver01

CRITICAL FINDINGS:
━━━━━━━━━━━━━━━━━━━━━━━━━
1. Host 192.168.10.55 was compromised and established C2 to 203.0.113.42
2. Attacker performed internal scanning and laterally moved to 2 other hosts
3. 2.1 GB of data was exfiltrated to attacker infrastructure
4. Additional hosts compromised: 192.168.10.10, 192.168.10.15

IMMEDIATE ACTIONS REQUIRED:
━━━━━━━━━━━━━━━━━━━━━━━━━
1. ISOLATE hosts: 192.168.10.10, 192.168.10.15 (lateral movement targets)
2. BLOCK IPs: 203.0.113.42, 198.51.100.15
3. BLOCK domain: evil-c2.example.com, attacker-exfil-server.net
4. HUNT for other C2 beacons across network (check all hosts)
5. FORCE password reset for all user accounts
6. EXPORT PCAPs for all sessions (evidence preservation)
7. ESCALATE to incident commander - this is a MAJOR INCIDENT

Timeline and full IoC list generated in incident report.
```

## Integration with SIEM

Export timeline and IoCs to your SIEM:

```python
# Pseudocode
timeline = agent.generate_timeline(compromised_ip)
iocs = agent.extract_iocs(compromised_ip)

# Push to Splunk
splunk.send_event(timeline)
splunk.add_threat_intel(iocs)

# Push to QRadar
qradar.create_offense(timeline, severity="HIGH")
qradar.add_reference_set("arkime_iocs", iocs)
```

## Related Playbooks

- [Data Exfiltration Hunt](data_exfiltration_hunt.md) - Proactive hunting for exfiltration
- [DNS Tunnel Detection](dns_tunnel_detection.md) - DNS-based exfiltration analysis
- [SOC Alert Triage](alert_triage.md) - Initial alert triage before deep forensics
