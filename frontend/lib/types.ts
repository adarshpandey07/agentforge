// TypeScript interfaces mirroring the AgentForge backend contract (CONTRACT.md).

export type Role = "owner" | "admin" | "member" | "viewer";

export interface Tenant {
  id: string;
  name: string;
  created_at?: string;
  updated_at?: string;
}

export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  role: Role;
  tenant_id: string;
  tenant_name?: string | null;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type?: string;
  user?: User;
}

export interface Client {
  id: string;
  tenant_id?: string;
  name: string;
  email?: string | null;
  phone?: string | null;
  company?: string | null;
  business_type?: string | null;
  notes?: string | null;
  project_count?: number;
  created_at?: string;
  updated_at?: string;
}

export type ProjectStatus = "draft" | "active" | "paused" | "archived";

export interface Project {
  id: string;
  tenant_id?: string;
  client_id: string;
  client_name?: string | null;
  name: string;
  description?: string | null;
  status: ProjectStatus | string;
  agent_count?: number;
  created_at?: string;
  updated_at?: string;
}

// ---------- AgentSpec (the core artifact) ----------

export type WorkflowNodeType = "agent" | "tool" | "condition" | "input" | "output";

export interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  ref?: string | null;
  label?: string | null;
  position: { x: number; y: number };
}

export interface WorkflowEdge {
  source: string;
  target: string;
  condition?: string | null;
}

export interface SpecAgent {
  id: string;
  role: string;
  system_prompt: string;
  tools: string[];
  memory: string[];
  model: string;
}

export interface SpecTool {
  name: string;
  type: "builtin" | "api" | "webhook" | "mcp" | string;
  provider?: string | null;
  config?: Record<string, unknown>;
}

export interface ModelPolicy {
  preferred: string;
  constraints?: {
    max_cost_per_1k_tokens?: number;
    min_context?: number;
    priority?: "balanced" | "cost" | "latency" | "accuracy" | string;
  };
}

export interface AgentSpec {
  version: number;
  name: string;
  business_type?: string | null;
  description?: string | null;
  model_policy?: ModelPolicy;
  agents: SpecAgent[];
  supervisor?: { enabled: boolean; routing_prompt?: string | null };
  workflow: { nodes: WorkflowNode[]; edges: WorkflowEdge[] };
  tools: SpecTool[];
  rag?: {
    enabled: boolean;
    vector_store?: string;
    embedding_model?: string;
    sources?: unknown[];
  };
  memory?: {
    short_term?: boolean;
    long_term?: boolean;
    vector?: boolean;
    session?: boolean;
    customer?: boolean;
  };
  integrations?: string[];
  deployment?: { mode?: string; channels?: string[] };
  stub?: boolean;
}

export interface Agent {
  id: string;
  tenant_id?: string;
  project_id: string;
  project_name?: string | null;
  name: string;
  description?: string | null;
  spec: AgentSpec;
  status: "draft" | "active" | "paused" | "error" | string;
  created_at?: string;
  updated_at?: string;
}

export interface Workflow {
  id: string;
  agent_id: string;
  graph: { nodes: WorkflowNode[]; edges: WorkflowEdge[] };
  version: number;
  created_at?: string;
  updated_at?: string;
}

// ---------- Prompts ----------

export interface PromptVersion {
  id: string;
  prompt_id: string;
  content: string;
  version: number;
  notes?: string | null;
  created_at?: string;
}

export interface Prompt {
  id: string;
  project_id?: string | null;
  name: string;
  description?: string | null;
  versions?: PromptVersion[];
  latest_version?: number;
  created_at?: string;
  updated_at?: string;
}

export interface PromptTestResult {
  output: string;
  model?: string;
  tokens?: { prompt?: number; completion?: number };
  cost?: number;
  latency_ms?: number;
  stub?: boolean;
}

// ---------- Knowledge ----------

export interface KnowledgeBase {
  id: string;
  project_id?: string | null;
  name: string;
  vector_store?: string;
  embedding_model?: string;
  document_count?: number;
  created_at?: string;
}

export interface KbDocument {
  id: string;
  kb_id?: string;
  knowledge_base_id?: string;
  name?: string | null;
  source_type: "file" | "url" | "faq" | string;
  status: "pending" | "processing" | "indexed" | "failed" | string;
  metadata?: Record<string, unknown>;
  chunks?: number;
  created_at?: string;
}

// ---------- Tools / Integrations ----------

export interface Tool {
  id: string;
  tenant_id?: string;
  name: string;
  type: "builtin" | "api" | "webhook" | "mcp" | string;
  provider?: string | null;
  config?: Record<string, unknown>;
  status?: string;
  created_at?: string;
}

export interface Integration {
  id: string;
  provider: string;
  status?: string;
  created_at?: string;
}

// ---------- Templates ----------

export interface Template {
  id: string;
  business_type: string;
  name: string;
  description?: string | null;
  spec: AgentSpec;
  is_public?: boolean;
  agent_count?: number;
  created_at?: string;
}

export interface InstantiateResponse {
  project_id: string;
  agent_id?: string;
  project?: Project;
  agent?: Agent;
}

// ---------- Runtime / Chat ----------

export interface ChatToolCall {
  tool_name: string;
  input?: unknown;
  output?: unknown;
  duration_ms?: number;
  error?: string | null;
}

export interface ChatResponse {
  reply: string;
  session_id?: string;
  tokens?: { prompt?: number; completion?: number; total?: number };
  cost?: number;
  llm_calls?: LlmCall[];
  tool_calls?: ChatToolCall[];
  stub?: boolean;
}

export interface SimulationReport {
  scenario?: string;
  turns?: number;
  passed?: boolean;
  score?: number;
  transcript?: { role: string; content: string }[];
  findings?: string[];
  metrics?: Record<string, number>;
  stub?: boolean;
  [key: string]: unknown;
}

// ---------- Deployments ----------

export type DeploymentMode = "docker" | "cloud" | "vps" | "local";

export interface Deployment {
  id: string;
  agent_id: string;
  agent_name?: string | null;
  mode: DeploymentMode | string;
  status: "pending" | "building" | "running" | "failed" | "stopped" | string;
  url?: string | null;
  created_at?: string;
  updated_at?: string;
}

// ---------- Observability ----------

export interface LlmCall {
  id: string;
  agent_id?: string | null;
  model: string;
  provider: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost: number;
  latency_ms: number;
  created_at?: string;
}

export interface ToolCallLog {
  id: string;
  tool_name: string;
  input?: unknown;
  output?: unknown;
  duration_ms: number;
  error?: string | null;
  created_at?: string;
}

export interface AuditLog {
  id: string;
  actor: string;
  action: string;
  resource: string;
  detail?: Record<string, unknown>;
  created_at?: string;
}

export interface AnalyticsOverview {
  clients: number;
  projects?: number;
  agents: number;
  active_agents?: number;
  deployments?: number;
  total_cost: number;
  total_tokens: number;
  recent_llm_calls?: LlmCall[];
}

// ---------- API keys ----------

export interface ApiKey {
  id: string;
  name?: string | null;
  prefix?: string | null;
  scopes?: string[];
  created_at?: string;
  // Only returned once, on creation:
  key?: string;
}

export interface Paginated<T> {
  items: T[];
  total?: number;
}
