# ============================================================
# AgentForge — developer workflow
# Run `make help` to list targets.
# ============================================================

.DEFAULT_GOAL := help
COMPOSE := docker compose

.PHONY: help setup up down logs backend-dev frontend-dev migrate test seed deploy-prod k8s-apply clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Copy .env.example -> .env (first-time setup)
	@test -f .env || cp .env.example .env
	@echo ".env ready — edit JWT_SECRET and API keys before production use."

up: ## Start the full stack (docker compose, detached)
	$(COMPOSE) up -d --build
	@echo "Frontend  -> http://localhost:3000"
	@echo "API docs  -> http://localhost:8000/docs"
	@echo "Grafana   -> http://localhost:3001 (admin/admin)"

down: ## Stop the stack (volumes preserved)
	$(COMPOSE) down

logs: ## Tail logs from all services
	$(COMPOSE) logs -f --tail=100

backend-dev: ## Run backend locally with hot reload (needs postgres/redis up)
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend-dev: ## Run frontend locally with hot reload
	cd frontend && npm run dev

migrate: ## Apply database migrations (alembic upgrade head)
	cd backend && alembic upgrade head

test: ## Run backend test suite
	cd backend && pytest -q

seed: ## Seed demo data (tenant, client, template agents)
	cd backend && python -m app.db.seed

deploy-prod: ## Deploy to production VPS via deploy/scripts/deploy-vps.sh
	bash deploy/scripts/deploy-vps.sh

k8s-apply: ## Apply all Kubernetes manifests in deploy/k8s/
	kubectl apply -f deploy/k8s/

clean: ## Stop stack and remove volumes, caches, build artifacts
	$(COMPOSE) down -v --remove-orphans
	rm -rf backend/.pytest_cache backend/.mypy_cache frontend/.next
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
