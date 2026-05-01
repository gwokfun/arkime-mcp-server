# Arkime Skills — Design & Implementation Guide

[English](#english) | [中文](#chinese)

---

<a id="english"></a>

## Overview

This document presents the **brainstorming**, **design plan**, and **implementation plan** for exposing Arkime MCP Server capabilities as **agentskills.io**-compliant skills. Both the MCP protocol and the skills specification follow universal principles that make them usable on **any mainstream AI agent platform** (Claude, GPT-4/ChatGPT, Gemini, LangChain, AutoGen, CrewAI, Dify, Coze, etc.).

---

## 1. Brainstorming — Application Directions

The Arkime full-packet capture platform captures and indexes every byte of network traffic. Combining that data richness with AI agent skills opens up the following application directions:

### 1.1 Security Operations Center (SOC) Automation
**Problem:** SOC analysts spend significant time manually triaging alerts, pivoting between tools, and writing repetitive investigation queries.

**Opportunity:** An AI agent equipped with Arkime skills can autonomously:
- Receive a security alert (e.g., from a SIEM) and immediately query relevant sessions
- Enrich an alert with geo-location, protocol details, and top talkers
- Tag sessions as part of an active incident
- Draft a triage report in natural language

### 1.2 Threat Hunting
**Problem:** Threat hunters need to express complex hypotheses in Arkime's query language and iterate quickly.

**Opportunity:** A conversational AI agent lets hunters:
- Describe a hypothesis in plain English ("find hosts doing DNS lookups to newly registered domains")
- Let the agent translate it into an Arkime expression, run the query, and summarise findings
- Follow up with deeper packet inspection or hunt jobs targeting specific strings
- Detect lateral movement via connection-graph analysis

### 1.3 Incident Response & Digital Forensics
**Problem:** During a live incident, responders need to quickly reconstruct a network timeline and extract evidence.

**Opportunity:** An agent can:
- Search for all sessions involving a compromised host across a configurable time window
- Extract raw and decoded packet data for forensic artefacts
- Identify all external IPs the host contacted (data exfiltration candidates)
- Build a chronological session timeline automatically

### 1.4 Network Performance & Anomaly Monitoring
**Problem:** Network engineers need to spot unusual traffic patterns (bandwidth spikes, new services, unexpected protocols) quickly.

**Opportunity:** An agent running on a schedule can:
- Identify top talkers and compare against a baseline
- Report countries with unexpected outbound traffic
- Alert when PCAP storage utilisation crosses a threshold
- Summarise cluster health in a Slack or Teams message

### 1.5 Compliance & Audit
**Problem:** Compliance teams must demonstrate that specific traffic policies are enforced and that logs are retained.

**Opportunity:** An agent can:
- Query for traffic to or from regulated data zones
- Verify no unencrypted (non-TLS) sessions left the network perimeter
- Generate audit reports from session data with proper tagging
- Confirm PCAP retention windows meet regulatory requirements

### 1.6 Multi-Cluster Network Visibility
**Problem:** Large organisations operate multiple Arkime clusters across sites or cloud regions.

**Opportunity:** An agent using the Parliament skill can:
- Provide a unified health dashboard across all clusters
- Correlate sessions across sites during a distributed incident
- Identify which cluster has captured traffic for a given host

---

## 2. Design Plan

### 2.1 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   AI Agent Platform                      │
│   (Claude / GPT-4 / Gemini / LangChain / AutoGen …)     │
│                                                         │
│  ┌───────────────────┐   ┌──────────────────────────┐  │
│  │  Skills Interface │   │   MCP Client Interface   │  │
│  │ (agentskills.io)  │   │  (stdio / HTTP stream)   │  │
│  └────────┬──────────┘   └───────────┬──────────────┘  │
└───────────┼───────────────────────────┼─────────────────┘
            │ HTTP / Function Call       │ MCP Protocol
            ▼                           ▼
┌────────────────────────────────────────────────────────┐
│               arkime-mcp-server                        │
│   arkime_mcp_server/server.py  (FastMCP)               │
│   29 tools identical under both interfaces            │
└───────────────────────────┬────────────────────────────┘
                            │ REST / Digest Auth
                            ▼
┌────────────────────────────────────────────────────────┐
│              Arkime Viewer (v3+ API)                   │
│   /api/sessions  /api/connections  /api/hunt  …        │
└───────────────────────────┬────────────────────────────┘
                            │ Packet Index
                            ▼
┌────────────────────────────────────────────────────────┐
│        OpenSearch / Elasticsearch  +  PCAP Files       │
└────────────────────────────────────────────────────────┘
```

### 2.2 Skills Specification Design Principles

The skills manifest (`skills/arkime_skills.yaml`) follows the **agentskills.io v1.0** specification:

| Field | Purpose |
|-------|---------|
| `name` | Unique, snake_case identifier matching the MCP tool name |
| `display_name` | Human-readable name shown in agent UIs |
| `description` | Detailed description used for LLM tool selection |
| `use_cases` | Semantic tags for scenario-based skill discovery |
| `parameters` | Input parameters with type, required flag, and description |
| `output` | Output schema following JSON Schema conventions |

**Key design decisions:**

1. **1-to-1 mapping with MCP tools** — Each skill corresponds exactly to one MCP tool, so the same capability is accessible through either interface without duplication.
2. **Rich descriptions** — Descriptions are written to guide LLM tool-selection, explaining *when* and *why* to use each skill, not just *what* it does.
3. **Use-case tags** — Six use-case categories (`soc`, `threat_hunting`, `incident_response`, `network_monitoring`, `compliance`, `multi_cluster`) allow agents to filter skills by scenario.
4. **Standard types** — Parameter types use JSON Schema primitives (`string`, `integer`, `boolean`, `array`, `object`) for universal compatibility.
5. **Enum constraints** — Where a parameter has a fixed set of valid values, `enum` is declared so agents can validate inputs.

### 2.3 Skill Categories

| Category | Skills | Primary Use Cases |
|----------|--------|-------------------|
| Session Search & Analysis | `search_sessions`, `get_session_detail`, `get_session_packets`, `get_session_raw` | SOC, IR, Threat Hunting |
| Network Investigation | `top_talkers`, `connections_graph`, `unique_destinations`, `dns_lookups`, `reverse_dns` | Threat Hunting, IR, Monitoring |
| Security & Anomaly | `external_connections`, `geo_summary` | Threat Hunting, SOC, Compliance |
| System Health | `capture_status`, `pcap_files`, `list_fields`, `get_field_values`, `get_current_user`, `get_settings`, `get_stats`, `get_es_stats` | Monitoring, SOC |
| Tags & Annotations | `add_tags`, `remove_tags` | SOC, IR, Compliance |
| Hunt (Payload Search) | `create_hunt`, `get_hunts`, `delete_hunt` | Threat Hunting, IR, SOC |
| Views (Saved Searches) | `create_view`, `get_views`, `delete_view` | SOC, Compliance |
| Advanced | `get_notifiers`, `get_parliament` | SOC, Multi-cluster, Monitoring |

---

## 3. Implementation Plan

### Phase 1 — Skills Manifest ✅
**Deliverable:** `skills/arkime_skills.yaml`

- Define all 29 skills following agentskills.io v1.0 spec
- Include `metadata` block (name, description, provider, tags)
- Annotate every skill with `use_cases` for scenario discovery
- Document all parameters with type, required, default, and enum where applicable
- Provide output schema for each skill

### Phase 2 — Agent Integration Examples
**Deliverable:** `skills/examples/`

Example agent configurations and invocation patterns for popular platforms:

| File | Platform |
|------|----------|
| `openai_functions.json` | OpenAI function calling (GPT-4) |
| `anthropic_tools.json` | Anthropic Claude tool use |
| `langchain_agent.py` | LangChain Tool adapter |
| `autogen_config.py` | Microsoft AutoGen |
| `dify_workflow.yaml` | Dify platform workflow |

> Phase 2 is tracked as a follow-up. The skills manifest in Phase 1 is the single source of truth from which these adapters are generated.

### Phase 3 — Skills Validation & Testing
**Deliverable:** `skills/tests/validate_skills.py`

- Load and validate `arkime_skills.yaml` against the agentskills.io JSON Schema
- Verify every skill name matches an existing MCP tool in `server.py`
- Verify all parameter types are JSON Schema compatible
- Run as part of CI

### Phase 4 — Scenario Playbooks
**Deliverable:** `skills/playbooks/`

Natural-language playbooks that chain multiple skills into automated workflows:

| Playbook | Skills Used | Use Case |
|----------|-------------|----------|
| Alert Triage | `search_sessions` → `get_session_detail` → `add_tags` | SOC |
| Data Exfil Hunt | `external_connections` → `geo_summary` → `top_talkers` → `connections_graph` | Threat Hunting |
| Host Forensics | `unique_destinations` → `dns_lookups` → `get_session_packets` | IR |
| DNS Tunnel Detect | `dns_lookups` → `top_talkers(field=host.dns)` → `create_hunt` | Threat Hunting |
| Cluster Health Report | `capture_status` → `get_stats` → `pcap_files` → `get_parliament` | Monitoring |

---

## 4. Using the Skills

### 4.1 With MCP Clients (existing behaviour)

```json
{
  "mcpServers": {
    "arkime": {
      "command": "python",
      "args": ["-m", "arkime_mcp_server.server"],
      "env": { "ARKIME_PASSWORD": "your-password" }
    }
  }
}
```

### 4.2 With agentskills.io-Compatible Agents

Point your agent at the skills manifest:

```yaml
skills_manifest: skills/arkime_skills.yaml
```

Or load it programmatically:

```python
import yaml

with open("skills/arkime_skills.yaml") as f:
    manifest = yaml.safe_load(f)

skills = manifest["skills"]
# Pass `skills` to your agent framework's tool registry
```

### 4.3 Converting to OpenAI Function-Calling Format

```python
import yaml

def skill_to_openai_function(skill: dict) -> dict:
    properties = {}
    required = []
    for p in skill.get("parameters", []):
        prop = {
            "type": p["type"],
            "description": p.get("description", ""),
        }
        if "enum" in p:
            prop["enum"] = p["enum"]
        if "default" in p:
            prop["default"] = p["default"]
        properties[p["name"]] = prop
        if p.get("required", False):
            required.append(p["name"])

    return {
        "name": skill["name"],
        "description": skill["description"],
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }

with open("skills/arkime_skills.yaml") as f:
    manifest = yaml.safe_load(f)

openai_functions = [
    skill_to_openai_function(s) for s in manifest["skills"]
]
```

---

## 5. Compatibility Matrix

| Agent Platform | Integration Method | Status |
|----------------|--------------------|--------|
| Claude Desktop | MCP stdio | ✅ Supported |
| Claude API (tool use) | Skills → Anthropic tool format | ✅ Compatible |
| OpenAI GPT-4 | Skills → function_call format | ✅ Compatible |
| Google Gemini | Skills → function declarations | ✅ Compatible |
| LangChain | Skills → `Tool` / `StructuredTool` | ✅ Compatible |
| AutoGen | Skills → function map | ✅ Compatible |
| CrewAI | Skills → `Tool` | ✅ Compatible |
| Dify | Skills → custom tool YAML | ✅ Compatible |
| Coze | Skills → plugin manifest | ✅ Compatible |
| Cursor / Zed | MCP stdio | ✅ Supported |

---

<a id="chinese"></a>

## 概述（中文）

本文档介绍了基于 arkime-mcp-server 补充 **agentskills.io** 技能的头脑风暴、设计方案和实施方案。MCP 协议和技能规范均遵循通用原则，可在任意主流 AI Agent 平台上使用（Claude、GPT-4/ChatGPT、Gemini、LangChain、AutoGen、CrewAI、Dify、Coze 等）。

---

## 1. 头脑风暴——应用方向

Arkime 全流量抓包平台捕获并索引网络中的每一个字节。将其与 AI Agent 技能结合，开辟出以下应用方向：

### 1.1 安全运营中心（SOC）自动化
**痛点：** 分析师在手动处理告警分类、工具切换和重复查询上花费大量时间。

**机会：** 配备 Arkime 技能的 AI Agent 可自动完成：
- 接收 SIEM 告警后立即查询相关会话
- 用地理位置、协议详情和流量 Top N 丰富告警上下文
- 将会话标记为活跃事件的一部分
- 自动生成分类报告

### 1.2 威胁狩猎（Threat Hunting）
**痛点：** 猎手需要以 Arkime 查询语言表达复杂假设并快速迭代。

**机会：** 对话式 AI Agent 让猎手能够：
- 用自然语言描述假设，由 Agent 转换为 Arkime 表达式并执行查询
- 通过数据包载荷搜索（Hunt）定位已知恶意字符串
- 通过连接图分析检测横向移动

### 1.3 事件响应与数字取证
**痛点：** 在实时事件中，响应人员需要快速重建网络时间线并提取证据。

**机会：** Agent 可以：
- 搜索失陷主机在指定时间窗口内的所有会话
- 提取原始和解码数据包用于取证分析
- 识别主机与哪些外部 IP 通信（数据外泄候选）

### 1.4 网络性能与异常监控
**痛点：** 网络工程师需要快速发现异常流量模式。

**机会：** 定时调度的 Agent 可以：
- 识别 Top Talker 并与基线对比
- 上报异常出境流量目标国家
- 在存储容量超阈值时发送告警

### 1.5 合规与审计
**痛点：** 合规团队需要证明特定流量策略已落实、日志已保留。

**机会：** Agent 可以：
- 查询进出受监管数据区域的流量
- 验证是否存在非加密（非 TLS）的出口流量
- 生成带标签的审计报告

### 1.6 多集群网络可视化
**痛点：** 大型组织在多站点或多云区域运行多个 Arkime 集群。

**机会：** 使用 Parliament 技能的 Agent 可以：
- 跨集群提供统一健康仪表板
- 在分布式事件期间跨站点关联会话

---

## 2. 设计方案

### 2.1 架构

```
AI Agent 平台（Claude / GPT-4 / Gemini / LangChain / AutoGen …）
        │ 技能接口（agentskills.io）或 MCP 协议
        ▼
arkime-mcp-server（FastMCP）
        │ REST / Digest 认证
        ▼
Arkime Viewer API（v3+）
        │
        ▼
OpenSearch / PCAP 文件
```

### 2.2 技能规范设计原则

1. **与 MCP 工具一一对应** — 每个技能对应一个 MCP 工具，两种接口无需重复实现
2. **富描述** — 描述面向 LLM 工具选择，解释*何时*以及*为何*使用每个技能
3. **用例标签** — 六个用例类别（`soc`、`threat_hunting`、`incident_response`、`network_monitoring`、`compliance`、`multi_cluster`）支持场景化技能发现
4. **标准类型** — 使用 JSON Schema 基础类型，确保跨平台兼容
5. **枚举约束** — 固定值参数声明 `enum`，方便 Agent 输入验证

---

## 3. 实施方案

### 阶段 1 — 技能清单 ✅
**交付物：** `skills/arkime_skills.yaml`

遵循 agentskills.io v1.0 规范，定义全部 29 个技能，包含元数据、用例标签、参数规格和输出模式。

### 阶段 2 — Agent 集成示例（待实施）
**交付物：** `skills/examples/`

为 OpenAI、Anthropic、LangChain、AutoGen、Dify 等平台提供示例配置和调用代码。

### 阶段 3 — 技能验证与测试（待实施）
**交付物：** `skills/tests/validate_skills.py`

- 验证 YAML 符合 agentskills.io 规范
- 确认每个技能名称与 server.py 中的 MCP 工具对应
- 集成到 CI 流水线

### 阶段 4 — 场景化剧本（待实施）
**交付物：** `skills/playbooks/`

将多个技能串联为自动化工作流的自然语言剧本，涵盖 SOC 分类、数据外泄狩猎、主机取证、DNS 隧道检测、集群健康报告等场景。

---

## 文件结构

```
skills/
├── README.md              ← 本文档（设计与实施指南）
└── arkime_skills.yaml     ← agentskills.io v1.0 技能清单（29 个技能）
```
