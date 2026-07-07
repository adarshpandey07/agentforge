#!/usr/bin/env bash
# AgentForge — dump the postgres database from the running compose stack.
# Usage: bash deploy/scripts/backup-db.sh [output-dir]
set -euo pipefail

cd "$(dirname "$0")/../.."

OUT_DIR="${1:-./backups}"
mkdir -p "${OUT_DIR}"
STAMP="$(date +%Y%m%d-%H%M%S)"
FILE="${OUT_DIR}/agentforge-${STAMP}.sql.gz"

echo "==> Dumping database agentforge to ${FILE}"
docker compose exec -T postgres pg_dump -U agentforge -d agentforge | gzip > "${FILE}"

echo "==> Done: $(du -h "${FILE}" | cut -f1)"
echo "Restore with:"
echo "  gunzip -c ${FILE} | docker compose exec -T postgres psql -U agentforge -d agentforge"
