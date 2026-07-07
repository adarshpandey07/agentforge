# AgentForge — API Reference

Base URL: `http://localhost:8000/api/v1` · OpenAPI: `/api/v1/openapi.json` · Health: `/health` · Metrics: `/metrics`

**Auth:** all endpoints except `/auth/register` and `/auth/login` require `Authorization: Bearer <access_token>`. JWT claims carry `sub` (user id), `tenant_id`, `role`. Machine access alternatively via API keys (`X-API-Key`).

**List conventions:** collection endpoints support `?q=<search>&skip=0&limit=50` plus resource-specific filters.

---

## Auth

### `POST /auth/register`
Creates a tenant and its owner user.
```json
// request
{ "email": "owner@agency.com", "password": "s3cret!", "tenant_name": "Acme Agency" }
// 201 response
{ "id": "3f6e...", "email": "owner@agency.com", "tenant_id": "9a1b...", "role": "owner" }
```

### `POST /auth/login`
```json
// request
{ "email": "owner@agency.com", "password": "s3cret!" }
// 200 response
{ "access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "bearer" }
```

### `GET /auth/me`
```json
{ "id": "3f6e...", "email": "owner@agency.com", "tenant_id": "9a1b...", "role": "owner" }
```

---

## CRUD resources

Full CRUD + list/search/filter on:
`/clients`, `/projects`, `/agents`, `/workflows`, `/prompts`, `/knowledge-bases`, `/tools`, `/integrations`, `/templates`, `/deployments`, `/api-keys`

Standard shape (example: clients):

| Method | Path | Description |
|---|---|---|
| GET | `/clients?q=&skip=&limit=` | List/search |
| POST | `/clients` | Create |
| GET | `/clients/{id}` | Retrieve |
| PATCH | `/clients/{id}` | Update |
| DELETE | `/clients/{id}` | Delete |

```json
// POST /clients
{ "name": "Sunrise Bakery", "business_type": "bakery", "contact_email": "hello@sunrise.example" }
// 201
{ "id": "c1d2...", "tenant_id": "9a1b...", "name": "Sunrise Bakery", "business_type": "bakery",
  "created_at": "2026-07-07T10:00:00Z", "updated_at": "2026-07-07T10:00:00Z" }
```

Notable fields:
- **agents** — `spec` (JSONB AgentSpec, see CONTRACT.md), `status`, FK `project_id`.
- **workflows** — `graph` (JSONB React Flow nodes/edges), `version`, FK `agent_id`.
- **knowledge-bases** — `vector_store` (`pgvector` default), `embedding_model`.
- **tools** — `name`, `type` (`builtin|api|webhook|mcp`), `config` JSONB.
- **integrations** — `provider`, `credentials` (encrypted at rest, never returned).

### Prompts extras

`POST /prompts/{id}/versions`
```json
// request
{ "content": "You are the Sunrise Bakery receptionist...", "notes": "friendlier tone" }
// 201
{ "id": "pv9...", "prompt_id": "p1...", "version": 3, "content": "...", "notes": "friendlier tone" }
```

`POST /prompts/{id}/test`
```json
// request
{ "input": "Do you have gluten-free bread?", "version": 3 }
// 200
{ "output": "Yes! Our gluten-free sourdough...", "tokens": {"prompt": 182, "completion": 44}, "cost": 0.0009, "latency_ms": 812 }
```

### Knowledge base extras

`POST /knowledge-bases/{id}/documents` — multipart file upload or `{ "url": "https://..." }`
```json
// 202
{ "id": "d7...", "kb_id": "kb1...", "source_type": "pdf", "status": "processing" }
// later: GET /knowledge-bases/{id} shows documents with status "indexed" and chunk counts
```

---

## AI endpoints

### `POST /generate`
Natural-language requirement → full AgentSpec + persisted project/agent/workflow/prompts.
```json
// request
{ "prompt": "Create an AI agent for a bakery that answers FAQs and takes cake orders", "business_type": "bakery" }
// 200
{ "project_id": "pr1...", "agent_id": "ag1...",
  "spec": { "version": 1, "name": "Bakery Assistant", "business_type": "bakery",
            "agents": [{ "id": "receptionist", "role": "Receptionist", "tools": ["faq_rag", "booking"], "memory": ["session", "customer"], "model": "auto", "system_prompt": "..." }],
            "supervisor": { "enabled": true, "routing_prompt": "..." },
            "workflow": { "nodes": [{"id": "n1", "type": "agent", "ref": "receptionist", "position": {"x": 0, "y": 0}}], "edges": [] },
            "tools": [...], "rag": {...}, "memory": {...}, "integrations": ["whatsapp"], "deployment": {"mode": "docker", "channels": ["web"]} } }
```

### `POST /agents/{id}/chat`
```json
// request
{ "message": "Can I order a birthday cake for Saturday?", "session_id": "sess-42" }
// 200
{ "reply": "Absolutely! What size and flavor would you like?",
  "llm_calls": [{ "model": "gpt-4o-mini", "provider": "openai", "prompt_tokens": 512, "completion_tokens": 38, "cost": 0.0011, "latency_ms": 640 }],
  "tool_calls": [{ "tool_name": "booking", "duration_ms": 120, "error": null }],
  "tokens": { "prompt": 512, "completion": 38 }, "cost": 0.0011 }
```
Persists to `conversations`, `messages`, `llm_calls`, `tool_calls`. Without API keys the reply is a deterministic stub with `"stub": true`.

### `POST /agents/{id}/simulate`
```json
// request
{ "scenario": "An angry customer whose cake was late" }
// 200 — automated multi-turn eval report
{ "turns": 5, "passed": true, "transcript": [...], "scores": { "helpfulness": 0.9, "tone": 0.85 }, "cost": 0.004 }
```

### `POST /templates/{id}/instantiate`
```json
// request
{ "client_id": "c1d2...", "customizations": { "name": "Sunrise Bakery Bot" } }
// 201
{ "project_id": "pr2...", "agent_id": "ag2...", "spec": { ... } }
```

---

## Deployments

### `POST /deployments`
```json
// request
{ "agent_id": "ag1...", "mode": "docker" }   // mode: docker | cloud | vps | local
// 202
{ "id": "dep1...", "agent_id": "ag1...", "mode": "docker", "status": "building", "url": null }
// later: GET /deployments/{id} → { "status": "running", "url": "https://agent-ag1.example.com" }
```

---

## Analytics & logs

| Endpoint | Returns |
|---|---|
| `GET /analytics/overview` | `{ "clients": 12, "agents": 34, "conversations": 210, "total_cost": 12.42, "tokens": { "prompt": 1200000, "completion": 240000 } }` |
| `GET /logs/llm-calls?skip=&limit=` | Rows: model, provider, prompt/completion tokens, cost, latency_ms |
| `GET /logs/tool-calls?skip=&limit=` | Rows: tool_name, input, output, duration_ms, error |
| `GET /audit-logs?skip=&limit=` | Rows: actor, action, resource, detail |

## Errors

Standard FastAPI shape: `{ "detail": "..." }` with 400 (validation), 401 (missing/invalid token), 403 (RBAC), 404, 409, 422 (Pydantic), 429 (rate limits).
