// Typed fetch client for the AgentForge backend (/api/v1).
// Attaches Bearer token from localStorage; normalizes list responses.

import type {
  AgentSpec,
  Agent,
  AnalyticsOverview,
  ApiKey,
  AuditLog,
  AuthResponse,
  ChatResponse,
  Client,
  Deployment,
  InstantiateResponse,
  Integration,
  KbDocument,
  KnowledgeBase,
  LlmCall,
  Project,
  Prompt,
  PromptTestResult,
  PromptVersion,
  SimulationReport,
  Template,
  Tool,
  ToolCallLog,
  User,
  Workflow,
} from "@/lib/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export interface ListParams {
  q?: string;
  skip?: number;
  limit?: number;
  [key: string]: string | number | boolean | undefined;
}

function qs(params?: ListParams): string {
  if (!params) return "";
  const search = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") search.set(k, String(v));
  });
  const s = search.toString();
  return s ? `?${s}` : "";
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (typeof window !== "undefined") {
    const token = window.localStorage.getItem("agentforge_token");
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  } catch (e) {
    throw new ApiError(0, "Network error — is the API running?", e);
  }

  if (res.status === 204) return undefined as T;

  let data: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? (data as { detail: unknown }).detail
        : data;
    const message =
      typeof detail === "string" ? detail : `Request failed (${res.status})`;
    if (res.status === 401 && typeof window !== "undefined") {
      window.localStorage.removeItem("agentforge_token");
    }
    throw new ApiError(res.status, message, detail);
  }
  return data as T;
}

/** Backends may return `T[]` or `{items: T[]}` — normalize to `T[]`. */
function asList<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    for (const key of ["items", "results", "data"]) {
      if (Array.isArray(obj[key])) return obj[key] as T[];
    }
  }
  return [];
}

const get = <T>(path: string) => request<T>(path);
const post = <T>(path: string, body?: unknown) =>
  request<T>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
const put = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "PUT", body: JSON.stringify(body ?? {}) });
const del = <T>(path: string) => request<T>(path, { method: "DELETE" });

export const api = {
  auth: {
    register: (body: {
      email: string;
      password: string;
      full_name?: string;
      tenant_name?: string;
    }) => post<AuthResponse>("/auth/register", body),
    login: (body: { email: string; password: string }) =>
      post<AuthResponse>("/auth/login", body),
    me: () => get<User>("/auth/me"),
  },

  clients: {
    list: (params?: ListParams) =>
      get<unknown>(`/clients${qs(params)}`).then((d) => asList<Client>(d)),
    get: (id: string) => get<Client>(`/clients/${id}`),
    create: (body: Partial<Client>) => post<Client>("/clients", body),
    update: (id: string, body: Partial<Client>) =>
      put<Client>(`/clients/${id}`, body),
    remove: (id: string) => del<void>(`/clients/${id}`),
  },

  projects: {
    list: (params?: ListParams) =>
      get<unknown>(`/projects${qs(params)}`).then((d) => asList<Project>(d)),
    get: (id: string) => get<Project>(`/projects/${id}`),
    create: (body: Partial<Project>) => post<Project>("/projects", body),
    update: (id: string, body: Partial<Project>) =>
      put<Project>(`/projects/${id}`, body),
    remove: (id: string) => del<void>(`/projects/${id}`),
  },

  agents: {
    list: (params?: ListParams) =>
      get<unknown>(`/agents${qs(params)}`).then((d) => asList<Agent>(d)),
    get: (id: string) => get<Agent>(`/agents/${id}`),
    create: (body: Partial<Agent>) => post<Agent>("/agents", body),
    update: (id: string, body: Partial<Agent> | { spec: AgentSpec }) =>
      put<Agent>(`/agents/${id}`, body),
    remove: (id: string) => del<void>(`/agents/${id}`),
    chat: (id: string, body: { message: string; session_id: string }) =>
      post<ChatResponse>(`/agents/${id}/chat`, body),
    simulate: (id: string, body: { scenario: string; turns?: number }) =>
      post<SimulationReport>(`/agents/${id}/simulate`, body),
  },

  workflows: {
    list: (params?: ListParams) =>
      get<unknown>(`/workflows${qs(params)}`).then((d) => asList<Workflow>(d)),
    get: (id: string) => get<Workflow>(`/workflows/${id}`),
    create: (body: Partial<Workflow>) => post<Workflow>("/workflows", body),
    update: (id: string, body: Partial<Workflow>) =>
      put<Workflow>(`/workflows/${id}`, body),
    remove: (id: string) => del<void>(`/workflows/${id}`),
  },

  prompts: {
    list: (params?: ListParams) =>
      get<unknown>(`/prompts${qs(params)}`).then((d) => asList<Prompt>(d)),
    get: (id: string) => get<Prompt>(`/prompts/${id}`),
    create: (body: Partial<Prompt> & { content?: string }) =>
      post<Prompt>("/prompts", body),
    update: (id: string, body: Partial<Prompt>) =>
      put<Prompt>(`/prompts/${id}`, body),
    remove: (id: string) => del<void>(`/prompts/${id}`),
    createVersion: (id: string, body: { content: string; notes?: string }) =>
      post<PromptVersion>(`/prompts/${id}/versions`, body),
    test: (id: string, body: { input: string; version?: number }) =>
      post<PromptTestResult>(`/prompts/${id}/test`, body),
  },

  knowledge: {
    list: (params?: ListParams) =>
      get<unknown>(`/knowledge-bases${qs(params)}`).then((d) =>
        asList<KnowledgeBase>(d)
      ),
    get: (id: string) => get<KnowledgeBase>(`/knowledge-bases/${id}`),
    create: (body: Partial<KnowledgeBase>) =>
      post<KnowledgeBase>("/knowledge-bases", body),
    remove: (id: string) => del<void>(`/knowledge-bases/${id}`),
    listDocuments: (id: string) =>
      get<unknown>(`/knowledge-bases/${id}/documents`).then((d) =>
        asList<KbDocument>(d)
      ),
    uploadFile: (id: string, file: File) => {
      const form = new FormData();
      form.append("file", file);
      form.append("source_type", "file");
      return request<KbDocument>(`/knowledge-bases/${id}/documents`, {
        method: "POST",
        body: form,
      });
    },
    addSource: (
      id: string,
      body: { source_type: "url" | "faq"; content: string; name?: string }
    ) => post<KbDocument>(`/knowledge-bases/${id}/documents`, body),
  },

  tools: {
    list: (params?: ListParams) =>
      get<unknown>(`/tools${qs(params)}`).then((d) => asList<Tool>(d)),
    get: (id: string) => get<Tool>(`/tools/${id}`),
    create: (body: Partial<Tool>) => post<Tool>("/tools", body),
    update: (id: string, body: Partial<Tool>) =>
      put<Tool>(`/tools/${id}`, body),
    remove: (id: string) => del<void>(`/tools/${id}`),
  },

  integrations: {
    list: (params?: ListParams) =>
      get<unknown>(`/integrations${qs(params)}`).then((d) =>
        asList<Integration>(d)
      ),
    create: (body: { provider: string; credentials: Record<string, unknown> }) =>
      post<Integration>("/integrations", body),
    remove: (id: string) => del<void>(`/integrations/${id}`),
  },

  templates: {
    list: (params?: ListParams) =>
      get<unknown>(`/templates${qs(params)}`).then((d) => asList<Template>(d)),
    get: (id: string) => get<Template>(`/templates/${id}`),
    instantiate: (
      id: string,
      body: { client_id: string; customizations?: Record<string, unknown> }
    ) => post<InstantiateResponse>(`/templates/${id}/instantiate`, body),
  },

  generate: (body: { prompt: string; business_type?: string }) =>
    post<AgentSpec & { project_id?: string; agent_id?: string }>(
      "/generate",
      body
    ),

  deployments: {
    list: (params?: ListParams) =>
      get<unknown>(`/deployments${qs(params)}`).then((d) =>
        asList<Deployment>(d)
      ),
    get: (id: string) => get<Deployment>(`/deployments/${id}`),
    create: (body: { agent_id: string; mode: string }) =>
      post<Deployment>("/deployments", body),
    remove: (id: string) => del<void>(`/deployments/${id}`),
  },

  apiKeys: {
    list: () => get<unknown>("/api-keys").then((d) => asList<ApiKey>(d)),
    create: (body: { name: string; scopes?: string[] }) =>
      post<ApiKey>("/api-keys", body),
    revoke: (id: string) => del<void>(`/api-keys/${id}`),
  },

  analytics: {
    overview: () => get<AnalyticsOverview>("/analytics/overview"),
  },

  logs: {
    llmCalls: (params?: ListParams) =>
      get<unknown>(`/logs/llm-calls${qs(params)}`).then((d) =>
        asList<LlmCall>(d)
      ),
    toolCalls: (params?: ListParams) =>
      get<unknown>(`/logs/tool-calls${qs(params)}`).then((d) =>
        asList<ToolCallLog>(d)
      ),
    auditLogs: (params?: ListParams) =>
      get<unknown>(`/audit-logs${qs(params)}`).then((d) => asList<AuditLog>(d)),
  },
};
