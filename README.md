# AgentForge

**The Shopify of AI Agents.** AgentForge is a production Agent-as-a-Service platform: describe a business in plain English, and it generates, customizes, and deploys a LangGraph-powered multi-agent AI team for any SMB — bakery, barber, gym, dentist, law firm, hotel, and more.

> "Create an AI agent for a bakery" → a full receptionist/booking/support agent team with RAG, memory, tools, and a visual workflow — deployed in minutes.

## Features

- **Natural-language agent generation** — one prompt → validated AgentSpec (agents, workflow, tools, RAG, memory, integrations)
- **Visual workflow builder** — React Flow canvas: drag-drop agent/tool/condition nodes, save versioned graphs
- **15+ business templates** — bakery, barber, salon, restaurant, gym, dentist, clinic, lawyer, real estate, car dealer, travel, hotel, retail, ecommerce, coaching — one-click instantiate per client
- **Multi-agent teams** — supervisor routing across receptionist / booking / support / sales agents
- **Smart model router** — auto-selects OpenAI / Anthropic / Google / DeepSeek / Ollama per task by cost, latency, context, and accuracy constraints
- **RAG out of the box** — pgvector by default, pluggable vector-store adapters, document upload + URL ingestion
- **5 memory types** — short-term, long-term, vector, session, customer
- **Integration catalog** — Gmail, Google Calendar, WhatsApp, Slack, Twilio, Stripe, Shopify, HubSpot, Salesforce, Zapier, n8n, custom API/webhook/MCP
- **Multi-tenant SaaS core** — tenants, RBAC (owner/admin/member/viewer), JWT + scoped API keys, audit logs
- **Full observability** — per-call token/cost/latency tracking, Prometheus metrics, provisioned Grafana dashboards
- **Deploy anywhere** — Docker Compose, single VPS, or Kubernetes (manifests included); agents deploy as docker/cloud/vps/local
- **Works without API keys** — every AI path degrades to deterministic stubs (`"stub": true`) so you can evaluate end-to-end for free

## Architecture

Next.js 14 frontend → FastAPI backend (`/api/v1`) → AI engine (`app/ai`: generator → AgentSpec → LangGraph factory → runtime) with Postgres+pgvector, Redis, RabbitMQ + Celery workers, and Prometheus/Grafana monitoring. Everything is multi-tenant and extended via plugin registries (tools, LLM providers, vector stores, templates).

Full diagrams and data flow: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Quickstart

```bash
git clone <repo-url> agentforge && cd agentforge
make setup   # creates .env (add LLM API keys if you have them — optional)
make up      # builds + starts the full stack
```

Open **http://localhost:3000**, register (creates your tenant), then hit **Generate** and type: *"Create an AI agent for a bakery."*

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |
| RabbitMQ mgmt | http://localhost:15672 (guest/guest) |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 (admin/admin) |

Dev loop: `make backend-dev`, `make frontend-dev`, `make migrate`, `make test`, `make seed`. Run `make help` for everything.

## Stack

`FastAPI` · `Python 3.11` · `SQLAlchemy 2.0 async` · `Pydantic v2` · `LangGraph` · `Celery` · `Next.js 14` · `TypeScript` · `Tailwind CSS` · `React Flow` · `PostgreSQL 16 + pgvector` · `Redis 7` · `RabbitMQ 3` · `Prometheus` · `Grafana` · `Docker` · `Kubernetes`

## Documentation

| Doc | What's inside |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System diagram, components, requirement→agent data flow, multi-tenancy, plugin extension points |
| [docs/API.md](docs/API.md) | Every `/api/v1` endpoint with request/response examples |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Local, Docker, VPS, Kubernetes, cloud — plus full env var reference |
| [docs/EXTENDING.md](docs/EXTENDING.md) | Add a tool plugin, LLM provider, vector store, or business template |
| [docs/SECURITY.md](docs/SECURITY.md) | Tenancy isolation, RBAC, JWT, API keys, secrets, audit logging |

## Screenshots

> _Coming soon: dashboard, visual builder, chat playground, template marketplace._

## License

MIT — see [LICENSE](LICENSE).
