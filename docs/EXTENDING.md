# AgentForge — Extension Guide

AgentForge is extended through **registries**, not forks. Four extension points: tools, LLM providers, vector stores, business templates. All live under `backend/app/ai/`.

> Signatures below match the AI Public Interface in `CONTRACT.md`. Adjust import paths to the concrete registry modules shipped in `app/ai/`.

## 1. Add a tool plugin

Tools have `type`: `builtin | api | webhook | mcp`. AgentSpecs reference them by **name** only, so registering a tool makes it instantly available to every agent.

```python
# backend/app/ai/tools/plugins/weather.py
from app.ai.tools.registry import register_tool, ToolResult

@register_tool(
    name="weather_lookup",
    type="builtin",
    description="Get current weather for a city. Input: {'city': str}",
)
async def weather_lookup(input: dict, config: dict) -> ToolResult:
    """config comes from the tenant's `tools` row (JSONB) — e.g. API keys."""
    city = input["city"]
    # ... call a weather API using config["api_key"] ...
    return ToolResult(output={"city": city, "temp_c": 21}, error=None)
```

Then reference it in an AgentSpec:

```json
{ "tools": [{ "name": "weather_lookup", "type": "builtin", "provider": null, "config": {} }],
  "agents": [{ "id": "receptionist", "tools": ["weather_lookup"] }] }
```

For `api`/`webhook` tools no code is needed — create a row via `POST /api/v1/tools` with `config` holding url/method/headers; the generic executor handles the call. For `mcp` tools, `config` holds the MCP server endpoint and tool name.

## 2. Add an LLM provider

The model router (`app/ai/router/`) selects providers via a registry keyed by cost/context/latency metadata, honoring each AgentSpec's `model_policy`.

```python
# backend/app/ai/router/providers/mistral.py
from app.ai.router.registry import register_provider, ModelInfo

@register_provider("mistral")
class MistralProvider:
    models = [
        ModelInfo(name="mistral-large-latest", context=128_000,
                  cost_per_1k_input=0.002, cost_per_1k_output=0.006,
                  strengths=["reasoning", "tools"]),
    ]

    def __init__(self, settings):
        self.api_key = settings.MISTRAL_API_KEY  # add to Settings + .env.example

    async def complete(self, model: str, messages: list[dict], **kwargs) -> dict:
        # return {"content": str, "prompt_tokens": int, "completion_tokens": int}
        ...
```

`select_model(task, constraints)` will now consider Mistral models when constraints match (e.g. `{"max_cost_per_1k_tokens": 0.01, "priority": "cost"}`). **Rule:** if the provider's key is missing, the provider must be skipped (never crash) — the router falls back and, with no providers at all, returns stub responses with `"stub": true`.

## 3. Add a vector store

RAG adapters (`app/ai/rag/`) conform to a small interface; pgvector is the default. A knowledge base selects its store via the `vector_store` column.

```python
# backend/app/ai/rag/stores/qdrant_store.py
from app.ai.rag.registry import register_vector_store, VectorStoreAdapter

@register_vector_store("qdrant")
class QdrantStore(VectorStoreAdapter):
    async def upsert(self, kb_id: str, chunks: list[dict]) -> int:
        """chunks: [{'id', 'text', 'embedding', 'metadata'}] → returns count."""
        ...

    async def search(self, kb_id: str, query_embedding: list[float], k: int = 5) -> list[dict]:
        """returns [{'text', 'score', 'metadata'}]"""
        ...

    async def delete(self, kb_id: str, ids: list[str] | None = None) -> None: ...
```

`ingest_source(kb_id, source_type, content, metadata)` and `retrieve(kb_id, query, k)` route to the adapter registered for that KB — no caller changes needed. Create a KB with `POST /api/v1/knowledge-bases {"vector_store": "qdrant", ...}`.

## 4. Add a business template

Templates are plain AgentSpec JSON files in `backend/app/ai/templates/` — one per business type. Discovered automatically by `list_templates()` / `get_template(business_type)` and shown in the frontend marketplace.

```json
// backend/app/ai/templates/florist.json
{
  "version": 1,
  "name": "Florist Assistant",
  "business_type": "florist",
  "description": "Multi-agent team for a flower shop: FAQs, custom bouquet orders, delivery scheduling.",
  "model_policy": { "preferred": "auto", "constraints": { "max_cost_per_1k_tokens": 0.01, "min_context": 32000, "priority": "balanced" } },
  "agents": [
    { "id": "receptionist", "role": "Receptionist", "system_prompt": "You are a friendly florist receptionist...", "tools": ["faq_rag"], "memory": ["session", "customer"], "model": "auto" },
    { "id": "orders", "role": "Order Specialist", "system_prompt": "You take bouquet orders...", "tools": ["booking"], "memory": ["session"], "model": "auto" }
  ],
  "supervisor": { "enabled": true, "routing_prompt": "Route order/delivery questions to orders, everything else to receptionist." },
  "workflow": {
    "nodes": [
      { "id": "n1", "type": "input", "ref": null, "position": { "x": 0, "y": 100 } },
      { "id": "n2", "type": "agent", "ref": "receptionist", "position": { "x": 250, "y": 0 } },
      { "id": "n3", "type": "agent", "ref": "orders", "position": { "x": 250, "y": 200 } },
      { "id": "n4", "type": "output", "ref": null, "position": { "x": 500, "y": 100 } }
    ],
    "edges": [
      { "source": "n1", "target": "n2", "condition": "general" },
      { "source": "n1", "target": "n3", "condition": "order" },
      { "source": "n2", "target": "n4", "condition": null },
      { "source": "n3", "target": "n4", "condition": null }
    ]
  },
  "tools": [
    { "name": "faq_rag", "type": "builtin", "provider": null, "config": {} },
    { "name": "booking", "type": "builtin", "provider": "google_calendar", "config": {} }
  ],
  "rag": { "enabled": true, "vector_store": "pgvector", "embedding_model": "text-embedding-3-small", "sources": [] },
  "memory": { "short_term": true, "long_term": true, "vector": true, "session": true, "customer": true },
  "integrations": ["whatsapp"],
  "deployment": { "mode": "docker", "channels": ["web"] }
}
```

Checklist for a valid template:
- `workflow.nodes[].position` is **required** (React Flow renders it directly).
- Every `agents[].tools` entry must exist in the top-level `tools` array by name.
- Every workflow `agent` node's `ref` must match an `agents[].id`.
- Set `is_public: true` via the `templates` table/API to publish it to the marketplace; operators then use `POST /api/v1/templates/{id}/instantiate`.

## Ground rules for all extensions

1. **Graceful degradation** — missing external credentials must produce a deterministic stub result marked `"stub": true`, never an exception.
2. **Tenancy** — anything persisted must carry `tenant_id`; tools receive per-tenant `config`, never global secrets.
3. **Telemetry** — providers must report token counts so `llm_calls` cost tracking and Grafana dashboards stay accurate; tools should surface `duration_ms` and `error`.
4. **Typing & docs** — full type hints, docstrings, and a test under `backend/tests/`.
