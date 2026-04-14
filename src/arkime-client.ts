/**
 * Arkime viewer API client with Digest authentication.
 */

import DigestFetch from "digest-fetch";

export class ArkimeClient {
  private baseUrl: string;
  private client: DigestFetch;

  constructor(url: string, user: string, password: string) {
    this.baseUrl = url.replace(/\/+$/, "");
    this.client = new DigestFetch(user, password);
  }

  private async get(
    endpoint: string,
    params?: Record<string, string | number>
  ): Promise<unknown> {
    const url = new URL(`${this.baseUrl}/api/${endpoint}`);
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null) {
          url.searchParams.set(k, String(v));
        }
      }
    }
    const resp = await this.client.fetch(url.toString());
    if (!resp.ok) {
      throw new Error(`Arkime API error: ${resp.status} ${resp.statusText}`);
    }
    const ct = resp.headers.get("content-type") ?? "";
    if (ct.includes("application/json")) {
      return resp.json();
    }
    return resp.text();
  }

  async esHealth(): Promise<Record<string, unknown>> {
    return (await this.get("eshealth")) as Record<string, unknown>;
  }

  async sessions(opts: {
    expression?: string;
    date?: number | string;
    length?: number;
    start?: number;
    fields?: string;
    order?: string;
    startTime?: number;
    stopTime?: number;
  }): Promise<Record<string, unknown>> {
    const params: Record<string, string | number> = {
      date: opts.date ?? 1,
      length: opts.length ?? 50,
      start: opts.start ?? 0,
    };
    if (opts.expression) params.expression = opts.expression;
    if (opts.fields) params.fields = opts.fields;
    if (opts.order) params.order = opts.order;
    if (opts.startTime !== undefined) {
      params.startTime = opts.startTime;
      delete params.date;
    }
    if (opts.stopTime !== undefined) params.stopTime = opts.stopTime;
    return (await this.get("sessions", params)) as Record<string, unknown>;
  }

  async connections(opts: {
    expression?: string;
    date?: number | string;
    srcField?: string;
    dstField?: string;
    length?: number;
  }): Promise<Record<string, unknown>> {
    const params: Record<string, string | number> = {
      date: opts.date ?? 1,
      srcField: opts.srcField ?? "source.ip",
      dstField: opts.dstField ?? "ip.dst:port",
      length: opts.length ?? 50,
    };
    if (opts.expression) params.expression = opts.expression;
    return (await this.get("connections", params)) as Record<string, unknown>;
  }

  async unique(opts: {
    exp: string;
    expression?: string;
    date?: number | string;
    counts?: number;
    length?: number;
  }): Promise<string> {
    const params: Record<string, string | number> = {
      exp: opts.exp,
      date: opts.date ?? 1,
      counts: opts.counts ?? 1,
      length: opts.length ?? 20,
    };
    if (opts.expression) params.expression = opts.expression;
    return (await this.get("unique", params)) as string;
  }

  async sessionDetail(node: string, sessionId: string): Promise<unknown> {
    return this.get(`session/${node}/${sessionId}/detail`);
  }

  async sessionPackets(node: string, sessionId: string): Promise<unknown> {
    return this.get(`session/${node}/${sessionId}/packets`);
  }

  async files(length = 20, start = 0): Promise<Record<string, unknown>> {
    return (await this.get("files", { length, start })) as Record<
      string,
      unknown
    >;
  }

  async fields(): Promise<unknown[]> {
    return (await this.get("fields", { array: "true" })) as unknown[];
  }

  async reverseDns(ip: string): Promise<unknown> {
    return this.get("reversedns", { ip });
  }
}
