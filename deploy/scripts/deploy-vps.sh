#!/usr/bin/env bash
# AgentForge — deploy to a single VPS via rsync + docker compose.
#
# Usage:
#   DEPLOY_HOST=user@your-vps DEPLOY_PATH=/opt/agentforge bash deploy/scripts/deploy-vps.sh
#
# Prereqs on the VPS: docker + docker compose plugin installed, SSH key auth.
set -euo pipefail

DEPLOY_HOST="${DEPLOY_HOST:?Set DEPLOY_HOST, e.g. root@1.2.3.4}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/agentforge}"

cd "$(dirname "$0")/../.."

echo "==> Syncing repo to ${DEPLOY_HOST}:${DEPLOY_PATH}"
# Exclude local artifacts; .env is NOT synced — manage it on the server.
rsync -az --delete \
  --exclude '.git' \
  --exclude '.env' \
  --exclude 'node_modules' \
  --exclude '.next' \
  --exclude '__pycache__' \
  --exclude '.venv' \
  ./ "${DEPLOY_HOST}:${DEPLOY_PATH}/"

echo "==> Building and restarting stack on remote"
ssh "${DEPLOY_HOST}" bash -s <<EOF
set -euo pipefail
cd "${DEPLOY_PATH}"
# First deploy: create .env from the example, then EDIT IT (JWT_SECRET, keys, CORS_ORIGINS).
if [ ! -f .env ]; then
  cp .env.example .env
  echo "WARNING: fresh .env created from example — edit it before real traffic."
fi
docker compose pull || true
docker compose up -d --build
docker compose ps
EOF

echo "==> Deploy complete."
