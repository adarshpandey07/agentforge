# AgentForge — Deployment Guide

Four ways to run AgentForge: local dev, Docker Compose, single VPS, Kubernetes. Cloud notes at the end.

## 1. Local development (hot reload)

Prereqs: Python 3.11+, Node 20+, Docker (for postgres/redis/rabbitmq).

```bash
make setup                      # copies .env.example -> .env
docker compose up -d postgres redis rabbitmq
cd backend && pip install -r requirements.txt && cd ..
make migrate                    # alembic upgrade head
make backend-dev                # uvicorn app.main:app --reload  (terminal 1)
make frontend-dev               # npm run dev                    (terminal 2)
```

- Frontend: http://localhost:3000 · API docs: http://localhost:8000/docs
- Optional: `make seed` for demo data, `make test` for the backend suite.

## 2. Docker Compose (full stack)

```bash
make setup   # then edit .env: set JWT_SECRET, optionally LLM API keys
make up      # builds and starts everything
```

Services: frontend :3000, backend :8000, postgres :5432, redis :6379, rabbitmq :5672 (mgmt :15672), prometheus :9090, grafana :3001 (admin/admin).

Useful:
```bash
make logs                 # tail all services
make down                 # stop (data kept)
make clean                # stop + wipe volumes
bash deploy/scripts/dev.sh          # up + wait for health + open browser
bash deploy/scripts/backup-db.sh    # pg_dump to ./backups
```

Without LLM API keys the platform still works end-to-end using deterministic stub responses (`"stub": true`).

## 3. Single VPS

Prereqs on the server: Docker + compose plugin, SSH key auth. From your machine:

```bash
DEPLOY_HOST=user@your-vps DEPLOY_PATH=/opt/agentforge make deploy-prod
# or directly: DEPLOY_HOST=... bash deploy/scripts/deploy-vps.sh
```

The script rsyncs the repo (excluding `.env`, `node_modules`, `.git`), then runs `docker compose up -d --build` remotely. On first deploy it creates `.env` from the example — **SSH in and set `JWT_SECRET`, API keys, and `CORS_ORIGINS` to your real domain** before serving traffic. Put a reverse proxy (Caddy/nginx) with TLS in front of ports 3000/8000.

## 4. Kubernetes

Manifests live in `deploy/k8s/` (namespace, secrets template, configmap, postgres StatefulSet+PVC, redis, rabbitmq, backend Deployment+Service+HPA, celery, frontend, ingress).

```bash
# 1. Build & push images, then update image refs in 20-backend.yaml / 21-celery.yaml / 22-frontend.yaml
docker build -t <registry>/agentforge-backend:latest backend/
docker build -t <registry>/agentforge-frontend:latest frontend/
docker push <registry>/agentforge-backend:latest <registry>/agentforge-frontend:latest

# 2. Fill secrets (copy 01-secrets.yaml, edit values, keep out of git)
kubectl apply -f deploy/k8s/00-namespace.yaml
kubectl apply -f my-secrets.yaml

# 3. Everything else
make k8s-apply        # kubectl apply -f deploy/k8s/

# 4. Migrations (one-off job or exec)
kubectl -n agentforge exec deploy/backend -- alembic upgrade head
```

Notes:
- Ingress assumes nginx ingress controller + cert-manager; edit host `agentforge.example.com` in `30-ingress.yaml` and `NEXT_PUBLIC_API_URL` in `02-configmap.yaml`.
- Backend HPA: 2–10 replicas at 70% CPU / 80% memory. Probes hit `/health`.
- For production Postgres consider a managed service or an operator (CloudNativePG) instead of the bundled StatefulSet.

## 5. Cloud (managed)

- **DB**: RDS/Cloud SQL/Neon with pgvector enabled; set `DATABASE_URL`.
- **Redis/RabbitMQ**: ElastiCache/Memorystore + CloudAMQP; set `REDIS_URL`/`RABBITMQ_URL`.
- **Compute**: the two Dockerfiles run anywhere (ECS/Fargate, Cloud Run, Render, Fly.io). Backend command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`; worker: `celery -A app.workers.celery_app worker`.
- **Storage**: any S3-compatible store via `S3_ENDPOINT/S3_ACCESS_KEY/S3_SECRET_KEY/S3_BUCKET`.

## Environment variable reference

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` / `production` |
| `DATABASE_URL` | `postgresql+asyncpg://agentforge:agentforge@localhost:5432/agentforge` | Async SQLAlchemy DSN (pgvector Postgres 16) |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache, memory, celery results |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672//` | Celery broker |
| `JWT_SECRET` | — **required, CHANGE-ME** | HMAC secret for access tokens (`openssl rand -hex 32`) |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `OPENAI_API_KEY` | empty | Optional — stubs without it |
| `ANTHROPIC_API_KEY` | empty | Optional |
| `GOOGLE_API_KEY` | empty | Optional |
| `DEEPSEEK_API_KEY` | empty | Optional |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Optional local models |
| `LANGSMITH_API_KEY` | empty | Optional LangSmith tracing |
| `S3_ENDPOINT` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `S3_BUCKET` | empty / `agentforge` | S3-compatible document storage |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Frontend → API base URL (build-time for Next.js) |

## Monitoring

Prometheus scrapes `backend:8000/metrics` (`deploy/monitoring/prometheus.yml`). Grafana auto-provisions the Prometheus datasource and the **AgentForge Overview** dashboard (request rate, LLM cost, token usage, latency percentiles) from `deploy/monitoring/grafana/`.
