#!/usr/bin/env node

/**
 * Arkime MCP server — investigation-oriented tools for full packet capture analysis.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { ArkimeClient } from "./arkime-client.js";

// ── Environment ──

const url = process.env.ARKIME_URL ?? "http://192.168.5.176:8005";
const user = process.env.ARKIME_USER ?? "mcp";
const password = process.env.ARKIME_PASSWORD;
if (!password) {
  console.error("Error: ARKIME_PASSWORD environment variable is required");
  process.exit(1);
}

const client = new ArkimeClient(url, user, password);

// ── Helpers ──

function formatTs(epochMs: number | null | undefined): string {
  if (!epochMs) return "—";
  return new Date(epochMs).toISOString().replace("T", " ").replace(/\.\d+Z$/, " UTC");
}

function formatBytes(b: number | null | undefined): string {
  if (!b) return "0 B";
  let val = b;
  for (const unit of ["B", "KB", "MB", "GB", "TB"]) {
    if (Math.abs(val) < 1024) return `${val.toFixed(1)} ${unit}`;
    val /= 1024;
  }
  return `${val.toFixed(1)} PB`;
}

function protoName(proto: number | null | undefined): string {
  const map: Record<number, string> = { 1: "ICMP", 6: "TCP", 17: "UDP" };
  return map[proto ?? 0] ?? String(proto);
}

interface SessionData {
  id?: string;
  node?: string;
  ipProtocol?: number;
  source?: { ip?: string; port?: number; geo?: { country_iso_code?: string }; as?: { full?: string } };
  destination?: { ip?: string; port?: number; geo?: { country_iso_code?: string }; as?: { full?: string } };
  totDataBytes?: number;
  network?: { packets?: number };
  firstPacket?: number;
  lastPacket?: number;
}

function summarizeSession(s: SessionData) {
  const src = s.source ?? {};
  const dst = s.destination ?? {};
  return {
    id: s.id,
    node: s.node,
    protocol: protoName(s.ipProtocol),
    source: `${src.ip ?? "?"}:${src.port ?? "?"}`,
    destination: `${dst.ip ?? "?"}:${dst.port ?? "?"}`,
    source_geo: src.geo?.country_iso_code ?? "",
    destination_geo: dst.geo?.country_iso_code ?? "",
    source_as: src.as?.full ?? "",
    destination_as: dst.as?.full ?? "",
    bytes: formatBytes(s.totDataBytes ?? 0),
    packets: s.network?.packets ?? 0,
    first_packet: formatTs(s.firstPacket),
    last_packet: formatTs(s.lastPacket),
  };
}

function json(data: unknown): string {
  return JSON.stringify(data, null, 2);
}

// ── Server ──

const server = new McpServer({
  name: "arkime",
  version: "1.0.0",
  description:
    "MCP server for Arkime full packet capture system. " +
    "Provides tools for searching network sessions, investigating traffic patterns, " +
    "identifying anomalous connections, and monitoring capture health. " +
    "The system captures all traffic between the home router and core switch.",
});

// ── Session Search & Analysis ──

server.tool(
  "search_sessions",
  "Search Arkime sessions with optional filtering. Returns summarized session data " +
    "including source/destination IPs, ports, protocols, bytes, geo, and AS info.",
  {
    expression: z
      .string()
      .optional()
      .describe(
        "Arkime search expression (e.g. 'ip.src==192.168.1.101', 'port.dst==443', " +
          "'host.dns==example.com'). Leave empty for all sessions."
      ),
    hours: z
      .number()
      .default(1)
      .describe("Time range in hours from now. Use -1 for all available data."),
    limit: z.number().default(50).describe("Max sessions to return (1-200)."),
    order: z
      .string()
      .optional()
      .describe(
        "Sort order as 'field:dir' (e.g. 'totDataBytes:desc', 'firstPacket:desc')."
      ),
  },
  async ({ expression, hours, limit, order }) => {
    const len = Math.min(Math.max(limit, 1), 200);
    const result = await client.sessions({ expression, date: hours, length: len, order });
    const data = (result.data as SessionData[]) ?? [];
    const sessions = data.map(summarizeSession);
    return {
      content: [
        {
          type: "text" as const,
          text: json({
            total_matching: result.recordsFiltered ?? 0,
            returned: sessions.length,
            sessions,
          }),
        },
      ],
    };
  }
);

server.tool(
  "get_session_detail",
  "Get full detail for a single session including decoded protocol information.",
  {
    node: z.string().describe("Node name (from session search results)."),
    session_id: z.string().describe("Session ID (from session search results)."),
  },
  async ({ node, session_id }) => {
    const detail = await client.sessionDetail(node, session_id);
    return {
      content: [{ type: "text" as const, text: typeof detail === "string" ? detail : json(detail) }],
    };
  }
);

server.tool(
  "get_session_packets",
  "Get decoded packet data for a session. Returns packet contents.",
  {
    node: z.string().describe("Node name (from session search results)."),
    session_id: z.string().describe("Session ID (from session search results)."),
  },
  async ({ node, session_id }) => {
    const packets = await client.sessionPackets(node, session_id);
    return {
      content: [{ type: "text" as const, text: typeof packets === "string" ? packets : json(packets) }],
    };
  }
);

// ── Network Investigation ──

server.tool(
  "top_talkers",
  "Get top N values for a field by session count. Useful for finding the most " +
    "active hosts, most-contacted destinations, busiest ports, or most queried domains.",
  {
    field: z
      .string()
      .default("source.ip")
      .describe(
        "Field to aggregate: 'source.ip', 'destination.ip', 'destination.port', " +
          "'host.dns', 'http.uri'."
      ),
    expression: z.string().optional().describe("Optional Arkime filter expression."),
    hours: z.number().default(1).describe("Time range in hours from now."),
    limit: z.number().default(20).describe("Number of top entries to return."),
  },
  async ({ field, expression, hours, limit }) => {
    const result = await client.unique({ exp: field, expression, date: hours, length: limit });
    return { content: [{ type: "text" as const, text: String(result) }] };
  }
);

server.tool(
  "connections_graph",
  "Get network connection graph — nodes and links between sources and destinations. " +
    "Shows who is talking to whom with byte/packet/session counts.",
  {
    expression: z.string().optional().describe("Optional Arkime filter expression."),
    hours: z.number().default(1).describe("Time range in hours from now."),
    src_field: z.string().default("source.ip").describe("Source field."),
    dst_field: z.string().default("ip.dst:port").describe("Destination field."),
    limit: z.number().default(50).describe("Max connections to return."),
  },
  async ({ expression, hours, src_field, dst_field, limit }) => {
    const result = await client.connections({
      expression,
      date: hours,
      srcField: src_field,
      dstField: dst_field,
      length: limit,
    });
    const rawNodes = (result.nodes as Array<Record<string, unknown>>) ?? [];
    const nodes = rawNodes.map((n) => ({
      id: n.id,
      sessions: n.sessions ?? 0,
      bytes: formatBytes(n.totDataBytes as number),
      packets: n["network.packets"] ?? 0,
      type: n.type === 1 ? "source" : "destination",
    }));
    const rawLinks = (result.links as Array<Record<string, unknown>>) ?? [];
    const links = rawLinks.map((link) => {
      const srcIdx = (link.source as number) ?? 0;
      const dstIdx = (link.target as number) ?? 0;
      return {
        source: srcIdx < rawNodes.length ? rawNodes[srcIdx].id : "?",
        target: dstIdx < rawNodes.length ? rawNodes[dstIdx].id : "?",
        sessions: link.value ?? 0,
        bytes: formatBytes(link.totDataBytes as number),
      };
    });
    return {
      content: [{ type: "text" as const, text: json({ nodes, links }) }],
    };
  }
);

server.tool(
  "unique_destinations",
  "List distinct external destination IPs contacted by an internal host. " +
    "Useful for answering 'what is this device talking to?'",
  {
    source_ip: z.string().describe("Internal IP address to investigate."),
    hours: z.number().default(1).describe("Time range in hours from now."),
    limit: z.number().default(50).describe("Max destinations to return."),
  },
  async ({ source_ip, hours, limit }) => {
    const expr =
      `ip.src==${source_ip} && ip.dst!=10.0.0.0/8 && ip.dst!=192.168.0.0/16 && ip.dst!=172.16.0.0/12`;
    const result = await client.unique({
      exp: "destination.ip",
      expression: expr,
      date: hours,
      length: limit,
    });
    return { content: [{ type: "text" as const, text: String(result) }] };
  }
);

server.tool(
  "dns_lookups",
  "Search DNS queries captured in network traffic. Filter by domain name pattern " +
    "or source IP to see what a device is resolving.",
  {
    domain: z
      .string()
      .optional()
      .describe(
        "Domain to search for (supports wildcards like '*.example.com'). " +
          "Omit to see all DNS lookups."
      ),
    source_ip: z
      .string()
      .optional()
      .describe("Only show DNS queries from this source IP."),
    hours: z.number().default(1).describe("Time range in hours from now."),
    limit: z.number().default(30).describe("Max results to return."),
  },
  async ({ domain, source_ip, hours, limit }) => {
    const parts: string[] = [];
    if (domain) parts.push(`host.dns==${domain}`);
    if (source_ip) parts.push(`ip.src==${source_ip}`);
    const expr = parts.length > 0 ? parts.join(" && ") : undefined;
    const result = await client.unique({
      exp: "host.dns",
      expression: expr,
      date: hours,
      length: limit,
    });
    return { content: [{ type: "text" as const, text: String(result) }] };
  }
);

server.tool(
  "reverse_dns",
  "Get PTR/reverse DNS records for an IP address.",
  {
    ip: z.string().describe("IP address to look up."),
  },
  async ({ ip }) => {
    const result = await client.reverseDns(ip);
    return {
      content: [{ type: "text" as const, text: typeof result === "string" ? result : json(result) }],
    };
  }
);

// ── Security & Anomaly ──

server.tool(
  "external_connections",
  "Find sessions going to external (non-RFC1918) destinations. Useful for " +
    "seeing what traffic is leaving your network.",
  {
    source_ip: z
      .string()
      .optional()
      .describe("Internal IP to filter on. Omit for all internal hosts."),
    hours: z.number().default(1).describe("Time range in hours from now."),
    limit: z.number().default(50).describe("Max sessions to return."),
  },
  async ({ source_ip, hours, limit }) => {
    const parts = [
      "ip.dst!=10.0.0.0/8",
      "ip.dst!=192.168.0.0/16",
      "ip.dst!=172.16.0.0/12",
      "ip.dst!=224.0.0.0/4",
      "ip.dst!=255.255.255.255",
    ];
    if (source_ip) parts.push(`ip.src==${source_ip}`);
    const expr = parts.join(" && ");
    const result = await client.sessions({
      expression: expr,
      date: hours,
      length: limit,
      order: "totDataBytes:desc",
    });
    const data = (result.data as SessionData[]) ?? [];
    const sessions = data.map(summarizeSession);
    return {
      content: [
        {
          type: "text" as const,
          text: json({
            total_matching: result.recordsFiltered ?? 0,
            returned: sessions.length,
            sessions,
          }),
        },
      ],
    };
  }
);

server.tool(
  "geo_summary",
  "Breakdown of destination traffic by country. Highlights where your traffic " +
    "is going geographically.",
  {
    expression: z.string().optional().describe("Optional Arkime filter expression."),
    hours: z.number().default(1).describe("Time range in hours from now."),
    limit: z.number().default(30).describe("Max countries to return."),
  },
  async ({ expression, hours, limit }) => {
    const result = await client.unique({
      exp: "destination.geo.country_iso_code",
      expression,
      date: hours,
      length: limit,
    });
    return { content: [{ type: "text" as const, text: String(result) }] };
  }
);

// ── System Health ──

server.tool(
  "capture_status",
  "Get current Arkime capture health — cluster status, node count, shard health, " +
    "and OpenSearch version.",
  {},
  async () => {
    const health = await client.esHealth();
    return {
      content: [
        {
          type: "text" as const,
          text: json({
            cluster: health.cluster_name,
            status: health.status,
            nodes: health.number_of_nodes,
            active_shards: health.active_shards,
            unassigned_shards: health.unassigned_shards,
            opensearch_version: health.version,
            arkime_db_version: health.molochDbVersion,
          }),
        },
      ],
    };
  }
);

server.tool(
  "pcap_files",
  "List PCAP capture files with sizes, packet counts, and time ranges.",
  {
    limit: z.number().default(20).describe("Max files to return."),
  },
  async ({ limit }) => {
    const result = await client.files(limit);
    const data = (result.data as Array<Record<string, unknown>>) ?? [];
    const files = data.map((f) => ({
      name: String(f.name ?? "").split("/").pop(),
      size: formatBytes(f.filesize as number),
      packets: f.packets ?? 0,
      compression: f.compression ?? "none",
      ratio: `${((f.cratio as number) ?? 0).toFixed(1)}x`,
      first: formatTs(f.first as number),
      last: formatTs(f.lastTimestamp as number),
    }));
    return {
      content: [
        {
          type: "text" as const,
          text: json({ total_files: result.recordsTotal ?? 0, files }),
        },
      ],
    };
  }
);

server.tool(
  "list_fields",
  "List available Arkime session fields. Use these field names in search expressions. " +
    "Filter by group to narrow results (dns, http, email, tls, etc.).",
  {
    group: z
      .string()
      .optional()
      .describe("Filter by field group (e.g. 'dns', 'http', 'email', 'general')."),
  },
  async ({ group }) => {
    const fields = (await client.fields()) as Array<Record<string, unknown>>;
    const result = fields
      .filter((f) => !group || f.group === group)
      .map((f) => ({
        expression: f.exp,
        name: f.friendlyName,
        type: f.type,
        group: f.group,
      }));
    return { content: [{ type: "text" as const, text: json(result) }] };
  }
);

// ── Start ──

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
