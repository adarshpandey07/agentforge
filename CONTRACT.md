# AgentForge — Architecture Contract (v1)

**This file is the single source of truth for all build agents. Follow it exactly. Do not write files outside your ownership boundary.**

AgentForge is a production SaaS: an Agent-as-a-Service platform ("Shopify of AI Agents") where an agency operator creates business projects, enters customer requirements, and auto-generates + deploys LangGraph-powered AI agents for any SMB (bakery, barber, gym, dentist, etc).

## Monorepo layout & ownership

```
agentforge/
├── CONTRACT.md                  # this file (do not edit)
├── backend/                     # FastAPI (Python 3.11+)
│   ├── requirements.txt         # ALREADY WRITTEN (do not edit)
│   ├── Dockerfile               # owner: DEVOPS
│   ├── alembic/ alembic.ini     # owner: BACKEND-CORE
│   ├── tests/                   # owner: BACKEND-CORE
│   └── app/
│       ├── main.py              # owner: BACKEND-CORE
│       ├── core/                # owner: BACKEND-CORE (config, security, deps, logging)
│       ├── db/                  # owner: BACKEND-CORE (session, base)
│       ├── models/              # owner: BACKEND-CORE (SQLAlchemy)
│       ├── schemas/             # owner: BACKEND-CORE (Pydantic v2)
│       ├── api/v1/              # owner: BACKEND-CORE (routers)
│       ├── services/            # owner: BACKEND-CORE
│       ├── workers/             # owner: BACKEND-CORE (celery app + tasks)
│       └── ai/                  # owner: AI-ENGINE (ONLY the ai/ subtree)
│           ├── router/          # model router
│           ├── factory/         # LangGraph agent factory
│           ├── memory/          # 5 memory types
│           ├── rag/             # ingestion + retrieval + vector store adapters
│           ├── tools/           # plugin tool registry + builtin integrations
│           ├── generator/       # business requirement generator
│           ├── multi_agent/     # supervisor / agent teams
│           ├── prompts/         # prompt template engine
│           └── templates/       # business template AgentSpec JSONs
├── frontend/                    # owner: FRONTEND (entire dir except Dockerfile)
│   └── Dockerfile               # owner: DEVOPS
├── deploy/                      # owner: DEVOPS (k8s/, monitoring/, scripts/)
├── docs/                        # owner: DEVOPS
├── docker-compose.yml           # owner: DEVOPS
├── Makefile .env.example README.md   # owner: DEVOPS
```

## Services & ports
- frontend (Next.js 14 App Router): **3000**
- backend (FastAPI/uvicorn): **8000**, API prefix **`/api/v1`**, OpenAPI at `/api/v1/openapi.json`, health `/health`
- postgres (image `pgvector/pgvector:pg16`): **5432**, db `agentforge`, user `agentforge`, pass `agentforge`
- redis: **6379** · rabbitmq: **5672** (mgmt 15672) · prometheus: **9090** · grafana: **3001**

## Env vars (read via pydantic-settings, class `Settings` in `app/core/config.py`)
`DATABASE_URL` (postgresql+asyncpg://agentforge:agentforge@localhost:5432/agentforge), `REDIS_URL`, `RABBITMQ_URL`, `JWT_SECRET`, `JWT_ALGORITHM=HS256`, `ACCESS_TOKEN_EXPIRE_MINUTES=30`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, `OLLAMA_BASE_URL`, `LANGSMITH_API_KEY`, `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `ENVIRONMENT=development`, `CORS_ORIGINS=http://localhost:3000`

## Conventions
- Python: SQLAlchemy 2.0 async (`mapped_column`, `Mapped[]`), asyncpg, Pydantic v2, UUID(v4) string PKs, `created_at`/`updated_at` on every table, structlog for logging, full type hints. Routers thin → logic in services.
- Multi-tenancy: every domain table has `tenant_id` FK → `tenants.id`. JWT claims: `sub` (user id), `tenant_id`, `role`. RBAC roles: `owner`, `admin`, `member`, `viewer`. Dependency `get_current_user` + `require_role(...)` in `app/core/deps.py`.
- Frontend: Next.js 14 App Router, TypeScript strict, Tailwind CSS 3.4, hand-written shadcn-style components in `components/ui/`, `@xyflow/react` for the visual builder, `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`. JWT stored in localStorage via `lib/auth.ts`; API client `lib/api.ts`.

## Database tables (BACKEND-CORE implements all)
`tenants`, `users`, `clients`, `projects` (FK client), `agents` (FK project, `spec` JSONB = AgentSpec, `status`), `workflows` (FK agent, `graph` JSONB, `version`), `prompts` (FK project) + `prompt_versions` (content, version, notes), `knowledge_bases` (FK project, vector_store, embedding_model) + `documents` (FK kb, source_type, status, metadata), `tools` (FK tenant, name, type, config JSONB), `integrations` (provider, credentials JSONB-encrypted), `conversations` (FK agent, session_id, channel) + `messages` (role, content, tokens, cost), `llm_calls` (model, provider, prompt_tokens, completion_tokens, cost, latency_ms), `tool_calls` (tool_name, input, output, duration_ms, error), `api_keys` (hashed_key, scopes), `audit_logs` (actor, action, resource, detail JSONB), `deployments` (FK agent, mode, status, url), `templates` (business_type, name, spec JSONB, is_public)

## API routes (`/api/v1/...`) — BACKEND-CORE
- `POST /auth/register` (creates tenant+owner), `POST /auth/login` → `{access_token}`, `GET /auth/me`
- Full CRUD + list/search/filter (query params `q`, `skip`, `limit`): `/clients`, `/projects`, `/agents`, `/workflows`, `/prompts` (+ `POST /prompts/{id}/versions`, `POST /prompts/{id}/test`), `/knowledge-bases` (+ `POST /knowledge-bases/{id}/documents` upload/url), `/tools`, `/integrations`, `/templates`, `/deployments`, `/api-keys`
- `POST /generate` `{prompt, business_type?}` → calls AI generator → creates project+agent+workflow+prompts, returns full AgentSpec
- `POST /agents/{id}/chat` `{message, session_id}` → runs agent via AI runtime, persists conversation/messages/llm_calls
- `POST /agents/{id}/simulate` `{scenario}` → automated eval run
- `POST /templates/{id}/instantiate` `{client_id, customizations?}` → clone template into new project/agent
- `GET /analytics/overview` (counts, cost totals, token usage), `GET /logs/llm-calls`, `GET /logs/tool-calls`, `GET /audit-logs`
- `POST /deployments` `{agent_id, mode: docker|cloud|vps|local}` → generates deploy artifacts, returns status/url
- Prometheus metrics at `/metrics` (prometheus-client)

## AI Public Interface (AI-ENGINE implements; BACKEND-CORE imports ONLY these)
```python
from app.ai.generator import generate_agent_spec        # async (prompt: str, business_type: str | None = None) -> dict  # returns AgentSpec
from app.ai.runtime import run_agent                    # async (spec: dict, message: str, session_id: str, context: dict | None = None) -> dict  # {"reply": str, "llm_calls": [...], "tool_calls": [...], "tokens": {...}, "cost": float}
from app.ai.rag.ingest import ingest_source             # async (kb_id: str, source_type: str, content: bytes | str, metadata: dict) -> dict  # {"chunks": int, "status": "indexed"}
from app.ai.rag.retrieve import retrieve                # async (kb_id: str, query: str, k: int = 5) -> list[dict]
from app.ai.router.model_router import select_model     # (task: str, constraints: dict | None = None) -> dict  # {"provider", "model", "reason", "est_cost_per_1k"}
from app.ai.templates import list_templates, get_template  # () -> list[dict] / (business_type: str) -> dict
from app.ai.evaluate import simulate_agent              # async (spec: dict, scenario: str, turns: int = 5) -> dict  # eval report
```
All AI functions must degrade gracefully: if no API key configured, return deterministic stub responses (clearly marked `"stub": true`) so the platform works end-to-end without keys.

## AgentSpec JSON (the core artifact — generator/templates produce it, factory/runtime consume it)
```json
{
  "version": 1, "name": "Bakery Assistant", "business_type": "bakery", "description": "...",
  "model_policy": {"preferred": "auto", "constraints": {"max_cost_per_1k_tokens": 0.01, "min_context": 32000, "priority": "balanced|cost|latency|accuracy"}},
  "agents": [{"id": "receptionist", "role": "Receptionist", "system_prompt": "...", "tools": ["faq_rag", "booking"], "memory": ["session", "customer"], "model": "auto"}],
  "supervisor": {"enabled": true, "routing_prompt": "..."},
  "workflow": {"nodes": [{"id": "n1", "type": "agent|tool|condition|input|output", "ref": "receptionist", "position": {"x": 0, "y": 0}}], "edges": [{"source": "n1", "target": "n2", "condition": null}]},
  "tools": [{"name": "booking", "type": "builtin|api|webhook|mcp", "provider": "google_calendar", "config": {}}],
  "rag": {"enabled": true, "vector_store": "pgvector", "embedding_model": "text-embedding-3-small", "sources": []},
  "memory": {"short_term": true, "long_term": true, "vector": true, "session": true, "customer": true},
  "integrations": ["whatsapp", "gmail"],
  "deployment": {"mode": "docker", "channels": ["web"]}
}
```
`workflow.nodes[].position` must be present (frontend React Flow renders it directly).

## Business templates (AI-ENGINE ships ≥12 as JSON AgentSpecs in `app/ai/templates/`)
bakery, barber, salon, restaurant, gym, dentist, clinic, lawyer, real_estate, car_dealer, travel_agency, hotel, retail, ecommerce, coaching_institute — each with realistic multi-agent teams (receptionist/booking/support/sales), industry prompts, tools, memory, rag config.

## Frontend pages (FRONTEND)
`/login`, `/register`, `/dashboard` (overview cards: clients, agents, cost, tokens + recent activity), `/clients` (+detail), `/projects` (+detail), `/agents/[id]/builder` (React Flow canvas: node palette agent/tool/condition, drag-drop, save graph), `/agents/[id]/chat` (test playground), `/prompts` (versions list, diff-ish view, test button), `/knowledge` (upload UI, sources table, status), `/tools` (integration catalog grid: Gmail, GCal, Maps, WhatsApp, Slack, Twilio, Stripe, Shopify, HubSpot, Salesforce, Zapier, n8n, custom API, webhook), `/templates` (marketplace grid, one-click "Use template"), `/generate` (single textarea "Create an AI agent for a bakery" → shows generated spec + workflow preview), `/logs` (llm calls, tool calls, cost table), `/deployments`, `/settings` (API keys, team, tenant). Dark professional theme, sidebar layout.

## Quality bar
Production-grade structure, typed, documented, extensible plugin patterns (tool registry, provider registry, vector-store adapter registry). No TODO-stubs for core paths; graceful stubs only where external creds are missing.
