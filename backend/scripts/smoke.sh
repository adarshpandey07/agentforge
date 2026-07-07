#!/usr/bin/env bash
# AgentForge backend end-to-end smoke test.
# Boots the real server against sqlite, exercises the core product flow, and
# fails fast on any non-2xx response. Verified sequence — keep in sync with CONTRACT.md.
#
# Usage: ./scripts/smoke.sh            (from backend/, requires .venv with core deps)
set -euo pipefail

cd "$(dirname "$0")/.."
PORT="${PORT:-8010}"
BASE="http://127.0.0.1:${PORT}"
DB_FILE="./smoke.db"
EMAIL="smoke+$(date +%s)@test.dev"
PASSWORD='Passw0rd!123'

command -v jq >/dev/null || { echo "jq is required"; exit 1; }
[ -x .venv/bin/uvicorn ] || { echo "missing .venv — create it and install core deps first"; exit 1; }

rm -f "$DB_FILE"
DATABASE_URL="sqlite+aiosqlite:///${DB_FILE}" JWT_SECRET=devsecret \
  .venv/bin/uvicorn app.main:app --port "$PORT" >/tmp/agentforge-smoke.log 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true; rm -f "$DB_FILE"' EXIT

step() { echo; echo "==> $*"; }
req() { # req METHOD PATH [JSON_BODY] [AUTH]
  local method=$1 path=$2 body=${3:-} auth=${4:-}
  local args=(-s -X "$method" "$BASE$path" -H 'Content-Type: application/json' -w $'\n%{http_code}')
  [ -n "$body" ] && args+=(-d "$body")
  [ -n "$auth" ] && args+=(-H "Authorization: Bearer $auth")
  local out; out=$(curl "${args[@]}")
  local code=${out##*$'\n'}
  RESPONSE=${out%$'\n'*}
  case "$code" in 2*) echo "    $method $path -> $code" ;; *) echo "    $method $path -> $code FAILED"; echo "$RESPONSE"; exit 1 ;; esac
}

step "waiting for /health"
for _ in $(seq 1 50); do curl -sf "$BASE/health" >/dev/null 2>&1 && break; sleep 0.2; done
req GET /health

step "auth: register + login"
req POST /api/v1/auth/register "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"tenant_name\":\"SmokeCo\"}"
req POST /api/v1/auth/login "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"
TOKEN=$(jq -r .access_token <<<"$RESPONSE")
[ -n "$TOKEN" ] && [ "$TOKEN" != null ]

step "clients: create + search"
req POST /api/v1/clients '{"name":"Sunrise Bakery","business_type":"bakery","contact_email":"owner@sunrise.example"}' "$TOKEN"
req GET '/api/v1/clients?q=Sunrise' '' "$TOKEN"
[ "$(jq 'length' <<<"$RESPONSE")" -ge 1 ]

step "templates: 15 built-in business templates seeded"
req GET /api/v1/templates '' "$TOKEN"
COUNT=$(jq 'length' <<<"$RESPONSE")
echo "    templates: $COUNT"
[ "$COUNT" -ge 15 ]

step "generate: prompt -> AgentSpec + project + agent (stub mode)"
req POST /api/v1/generate '{"prompt":"Create an AI agent for a bakery"}' "$TOKEN"
AGENT_ID=$(jq -r .agent_id <<<"$RESPONSE")
jq -e '.spec.agents | length >= 1' >/dev/null <<<"$RESPONSE"
echo "    agent_id: $AGENT_ID"

step "chat: stub reply + llm_calls persisted"
req POST "/api/v1/agents/$AGENT_ID/chat" '{"message":"I want to book a cake","session_id":"s1"}' "$TOKEN"
jq -e '.reply and .stub == true' >/dev/null <<<"$RESPONSE"
echo "    reply: $(jq -r .reply <<<"$RESPONSE" | head -c 120)..."

step "analytics: counts and costs"
req GET /api/v1/analytics/overview '' "$TOKEN"
echo "    $(jq -c '{clients,projects,agents,conversations,llm_calls,tokens,total_cost}' <<<"$RESPONSE")"
jq -e '.agents >= 1 and .llm_calls >= 1' >/dev/null <<<"$RESPONSE"

echo
echo "SMOKE OK"
