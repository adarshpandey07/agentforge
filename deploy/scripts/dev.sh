#!/usr/bin/env bash
# AgentForge — local dev bootstrap: bring the stack up and open the UIs.
set -euo pipefail

cd "$(dirname "$0")/../.."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — set JWT_SECRET and API keys as needed."
fi

docker compose up -d --build

echo "Waiting for backend health..."
for i in $(seq 1 60); do
  if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
    echo "Backend healthy."
    break
  fi
  sleep 2
done

echo ""
echo "AgentForge is up:"
echo "  Frontend   http://localhost:3000"
echo "  API docs   http://localhost:8000/docs"
echo "  RabbitMQ   http://localhost:15672 (guest/guest)"
echo "  Prometheus http://localhost:9090"
echo "  Grafana    http://localhost:3001 (admin/admin)"

# Open in browser (macOS `open`, Linux `xdg-open`)
if command -v open >/dev/null 2>&1; then
  open http://localhost:3000
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://localhost:3000
fi
