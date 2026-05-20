#!/usr/bin/env bash
# Smoke test for the dashboard sync worker.
#
# Usage:
#   BASE_URL=https://dashboard-sync.you.workers.dev \
#   SYNC_TOKEN=<your-token> \
#   bash scripts/smoke-test.sh

set -euo pipefail

: "${BASE_URL:?Set BASE_URL to your worker base url}"
: "${SYNC_TOKEN:?Set SYNC_TOKEN to the bearer token you configured}"

pass() { printf '  OK  %s\n' "$1"; }
fail() { printf '  FAIL %s\n' "$1" >&2; exit 1; }

echo "-> Health check (no auth)"
code=$(curl -sS -o /dev/null -w '%{http_code}' "$BASE_URL/api/health")
[[ "$code" == "200" ]] && pass "health is 200" || fail "expected 200, got $code"

echo
echo "-> State without auth"
code=$(curl -sS -o /dev/null -w '%{http_code}' "$BASE_URL/api/state")
[[ "$code" == "401" ]] && pass "401 returned for missing auth" || fail "expected 401, got $code"

echo
echo "-> PUT a state blob"
payload='{"queue":[{"title":"smoke test item","url":"https://example.com","src":"smoke","done":false}],"learning":{"learn-1":true},"track":"cyber"}'
resp=$(curl -sS -X PUT \
  -H "Authorization: Bearer $SYNC_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$payload" \
  "$BASE_URL/api/state")
echo "  response: $resp"
echo "$resp" | grep -q '"ok":true' || fail "PUT did not return ok:true"
pass "PUT succeeded"

echo
echo "-> GET it back"
resp=$(curl -sS \
  -H "Authorization: Bearer $SYNC_TOKEN" \
  "$BASE_URL/api/state")
echo "  response: $resp"
echo "$resp" | grep -q '"smoke test item"' || fail "GET did not return the item we just PUT"
echo "$resp" | grep -q '"track":"cyber"' || fail "GET did not return track=cyber"
pass "GET returns the persisted state"

echo
echo "All checks passed."
