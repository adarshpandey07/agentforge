# AgentForge — Security Model

## Multi-tenancy isolation

- Every domain table carries a `tenant_id` FK → `tenants.id`. The service layer scopes **every** query by the tenant resolved from the caller's credentials — there is no cross-tenant read path.
- `POST /auth/register` atomically creates a tenant + its `owner` user; all subsequent resources inherit that tenant.
- Vector data (RAG) is isolated per knowledge base, which is tenant-scoped through its project.
- Defense in depth: IDs are UUIDv4 (non-enumerable), and object lookups always filter by `tenant_id`, so a leaked ID from another tenant still 404s.

## Authentication

**JWT (users):**
- `POST /auth/login` issues an HS256 access token (`JWT_ALGORITHM=HS256`) signed with `JWT_SECRET`, expiring after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30).
- Claims: `sub` (user id), `tenant_id`, `role`, `exp`. The backend never trusts client-supplied tenant ids — tenancy always comes from the verified token.
- Passwords are hashed with bcrypt (passlib); plaintext is never stored or logged.
- `JWT_SECRET` **must** be replaced in every environment (`openssl rand -hex 32`); the `.env.example` value is a marked placeholder and unusable as-is by convention.

**API keys (machines):**
- Created via `POST /api/v1/api-keys`; the raw key is shown **once** and only a hash is persisted (`api_keys.hashed_key`).
- Keys carry `scopes` limiting what they may call, and are bound to a tenant. Revocation = row delete/disable; verification is by hash comparison.

## RBAC

Roles, enforced by `require_role(...)` in `app/core/deps.py` (hierarchical — each includes the ones below):

| Role | Typical grants |
|---|---|
| `owner` | Everything, incl. tenant settings, billing, member management, API keys |
| `admin` | Manage clients/projects/agents/integrations/deployments; invite members |
| `member` | Create/edit agents, prompts, knowledge bases; run chats/simulations |
| `viewer` | Read-only: dashboards, logs, analytics |

Routers declare the minimum role per endpoint; 403 on violation is audit-logged.

## Secret handling

- All secrets arrive via environment variables (pydantic-settings) — never hardcoded, never committed (`.env` is gitignored).
- Integration credentials (`integrations.credentials`) are **encrypted at rest** (JSONB, symmetric app-level encryption) and never returned by the API after creation.
- LLM provider keys are server-side only; the frontend never sees them. Tools receive per-tenant `config`, not global secrets.
- Kubernetes: secrets live in the `agentforge-secrets` Secret (see `deploy/k8s/01-secrets.yaml` **template** — commit only the template; prefer SealedSecrets/ExternalSecrets in production).
- Logs are structured (structlog) with key/token redaction; prompts and API keys are never logged verbatim.

## Audit logs

- `audit_logs` table records `actor` (user/api-key id), `action`, `resource`, and a `detail` JSONB payload with `tenant_id` and timestamp on every mutating operation and auth event (login success/failure, key creation, role change, deployment).
- Readable at `GET /api/v1/audit-logs` (admin+). Rows are append-only — no update/delete path is exposed.

## Transport & platform hardening

- TLS terminates at the ingress/reverse proxy (cert-manager in k8s; Caddy/nginx on VPS). Internal traffic stays on the private compose/k8s network.
- CORS is locked to `CORS_ORIGINS` (default `http://localhost:3000`; set to your real origin in production).
- Containers run as **non-root** (backend: `agentforge` user; frontend: `nextjs`), with resource limits and health probes in k8s.
- Postgres/Redis/RabbitMQ are not exposed publicly in production topologies; default dev credentials (`agentforge`/`guest`) must be rotated outside local dev.
- LLM cost abuse is bounded per-tenant via `llm_calls` accounting (dashboards + `GET /analytics/overview`) — alert on anomalies in Grafana.

## Reporting

Found a vulnerability? Open a private security advisory or email the maintainers — do not file public issues for exploitable bugs.
