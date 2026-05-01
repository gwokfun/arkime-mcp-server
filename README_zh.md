# arkime-mcp-server

[English](README.md) | 中文

基于 [FastMCP](https://github.com/jlowin/fastmcp) 和 Python 3 构建的 [Arkime](https://arkime.com) 全流量抓包 [MCP](https://modelcontextprotocol.io) 服务器，让 AI 助手能够搜索网络会话、分析流量模式并监控抓包健康状态。

## 功能特性

- **完整的 Arkime API v3 覆盖**：实现了所有主要的 Arkime Viewer API
- **可配置工具**：通过配置文件启用或禁用特定工具
- **基于环境变量的配置**：支持 `.env` 文件和环境变量
- **30+ 工具**，涵盖：
  - 会话搜索与分析
  - 网络调查与连接图
  - DNS 查询与反向 DNS
  - 安全与异常检测
  - 系统健康监控
  - 标签、追踪、视图等

## 工具列表

### 会话搜索与分析
- `search_sessions` — 使用 Arkime 表达式搜索会话
- `get_session_detail` — 获取会话的完整解码协议详情
- `get_session_packets` — 获取解码后的数据包数据
- `get_session_raw` — 获取原始会话数据

### 网络调查
- `top_talkers` — 任意字段的 Top N 值（主机、端口、域名等）
- `connections_graph` — 包含节点和链路的网络连接图
- `unique_destinations` — 内部主机访问的不同外部 IP
- `dns_lookups` — 流量中捕获的 DNS 查询
- `reverse_dns` — IP 的 PTR/反向 DNS 查询

### 安全与异常
- `external_connections` — 到非 RFC1918 目标的会话
- `geo_summary` — 按国家分类的目标流量统计

### 系统健康与信息
- `capture_status` — Arkime 集群健康状态
- `pcap_files` — 带元数据的 PCAP 抓包文件列表
- `list_fields` — 可用的 Arkime 会话字段
- `get_field_values` — 字段的可能取值
- `get_current_user` — 当前用户信息
- `get_settings` — Arkime Viewer 设置
- `get_stats` — Arkime 统计信息
- `get_es_stats` — Elasticsearch/OpenSearch 索引统计信息

### 标签与注释
- `add_tags` — 为会话添加标签
- `remove_tags` — 从会话移除标签

### 追踪（数据包搜索）
- `create_hunt` — 创建搜索数据包载荷的追踪任务
- `get_hunts` — 列出追踪任务
- `delete_hunt` — 删除追踪任务

### 视图（已保存的搜索）
- `create_view` — 创建保存的视图
- `get_views` — 列出已保存的视图
- `delete_view` — 删除视图

### 高级功能
- `get_notifiers` — 列出已配置的通知器
- `get_parliament` — Parliament（多集群）信息

## 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/gwokfun/arkime-mcp-server.git
cd arkime-mcp-server

# 安装依赖
pip install -r requirements.txt

# 或以开发模式安装
pip install -e .
```

### 使用 pip 安装（发布后）

```bash
pip install arkime-mcp-server
```

## 配置

### 环境变量

设置以下环境变量，或创建 `.env` 文件：

| 变量 | 是否必需 | 默认值 | 描述 |
|------|----------|--------|------|
| `ARKIME_URL` | 否 | `http://192.168.5.176:8005` | Arkime Viewer 地址 |
| `ARKIME_USER` | 否 | `mcp` | Arkime API 用户名 |
| `ARKIME_PASSWORD` | **是** | — | Arkime API 密码 |

### 配置文件

将 `config.example.yaml` 复制为 `config.yaml` 并进行自定义：

```yaml
arkime:
  url: "http://your-arkime-server:8005"
  user: "your-username"
  # 密码应通过 ARKIME_PASSWORD 环境变量设置

tools:
  # 启用/禁用特定工具
  search_sessions: true
  get_session_detail: true
  # ... 等
```

### 工具配置

您可以在 `config.yaml` 文件中启用或禁用单个工具。默认情况下，所有工具均已启用。将任意工具设置为 `false` 即可禁用：

```yaml
tools:
  search_sessions: true
  get_session_detail: false  # 此工具将被禁用
  top_talkers: true
```

## 使用方法

### 启动服务器

```bash
# 直接运行
python -m arkime_mcp_server.server

# 或通过 pip 安装后运行
arkime-mcp-server
```

### 与 Claude Desktop 集成

在 MCP 设置文件中添加配置（例如 `~/Library/Application Support/Claude/claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "arkime": {
      "command": "python",
      "args": ["-m", "arkime_mcp_server.server"],
      "env": {
        "ARKIME_PASSWORD": "your-password"
      }
    }
  }
}
```

### 与其他 MCP 客户端集成

本服务器使用 stdio 传输，遵循 MCP 协议规范，可与任何兼容 MCP 的客户端配合使用。

## 身份认证

Arkime 使用 HTTP Digest 认证。服务器通过 httpx 的认证流系统实现了自定义的 HTTP Digest 认证。

## 开发

### 项目结构

```
arkime_mcp_server/
├── __init__.py       # 包初始化
├── server.py         # 包含所有工具的 FastMCP 服务器
├── client.py         # Arkime API 客户端
├── config.py         # 配置管理
└── utils.py          # 工具函数
```

### 测试

```bash
# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=arkime_mcp_server --cov-report=term-missing

# 运行测试并生成 HTML 覆盖率报告
pytest --cov=arkime_mcp_server --cov-report=html
```

详细测试文档请参阅 [tests/README.md](tests/README.md)。

**测试覆盖率：**
- 46 个单元测试，覆盖核心功能
- utils 和 config 模块 100% 覆盖
- client 模块 67% 覆盖
- 所有测试在约 1.3 秒内通过

## API 覆盖情况

本服务器实现了 [Arkime v3+ API 文档](https://arkime.com/apiv3) 中的以下 API：

- ✅ Sessions API（`/api/sessions`）
- ✅ Session Detail APIs（`/api/session/{node}/{id}/detail`、`/packets`、`/raw`）
- ✅ Connections API（`/api/connections`）
- ✅ Unique API（`/api/unique`）
- ✅ Fields API（`/api/fields`）
- ✅ Health APIs（`/api/eshealth`、`/api/stats`、`/api/esindices`）
- ✅ Files API（`/api/files`）
- ✅ DNS APIs（`/api/reversedns`）
- ✅ User APIs（`/api/user`、`/api/user/settings`）
- ✅ Tags APIs（添加/移除标签）
- ✅ Hunt APIs（`/api/hunt`）
- ✅ View APIs（`/api/view`、`/api/views`）
- ✅ Notifiers API（`/api/notifiers`）
- ✅ Parliament API（`/api/parliament`）

## 从 TypeScript 版本迁移

本项目已从 TypeScript 重构为 Python 3。主要变化：

- **技术栈**：Node.js → Python 3，`@modelcontextprotocol/sdk` → FastMCP
- **配置**：新增 YAML 配置文件和 `.env` 支持
- **工具管理**：新功能，可通过配置文件启用/禁用工具
- **API 覆盖**：从 12 个工具扩展到 30+ 个工具，覆盖所有主要 Arkime API

## 技能（agentskills.io）

除 MCP 协议外，Arkime 工具还以 **agentskills.io** 兼容技能的形式暴露，可在任意主流 AI Agent 平台上使用（Claude、GPT-4、Gemini、LangChain、AutoGen、CrewAI、Dify、Coze 等）。

技能清单位于 [`skills/arkime_skills.yaml`](skills/arkime_skills.yaml)。  
头脑风暴、设计方案与实施计划详见 [`skills/README.md`](skills/README.md)。

**技能覆盖的应用场景：**

| 场景 | 核心技能 |
|------|---------|
| SOC 自动化 | `search_sessions`, `add_tags`, `geo_summary` |
| 威胁狩猎 | `dns_lookups`, `connections_graph`, `create_hunt`, `external_connections` |
| 事件响应 | `get_session_detail`, `unique_destinations`, `get_session_packets` |
| 网络监控 | `top_talkers`, `capture_status`, `get_stats` |
| 合规与审计 | `external_connections`, `pcap_files`, `get_current_user` |
| 多集群运维 | `get_parliament`, `capture_status` |

## 许可证

MIT

## 贡献

欢迎贡献！请随时提交 Pull Request。
