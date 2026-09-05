#!/usr/bin/env bash
# Complete Cloudflare MCP OAuth from a pasted mobile/desktop callback URL.
# Usage: complete-mcp-oauth-callback.sh "http://127.0.0.1:PORT/callback?code=...&state=..."
#
# Prerequisite: PKCE verifier saved at /tmp/cf-oauth-${STATE}.json by the agent
# when the authorize link was issued. Do NOT start a new OAuth session if this file exists.

set -euo pipefail

CALLBACK_URL="${1:-}"
if [[ -z "$CALLBACK_URL" ]]; then
  echo "Usage: $0 'http://127.0.0.1:PORT/callback?code=...&state=...'" >&2
  exit 1
fi

STATE=$(python3 - <<'PY' "$CALLBACK_URL"
import sys, urllib.parse
q = urllib.parse.urlparse(sys.argv[1]).query
print(urllib.parse.parse_qs(q).get("state", [""])[0])
PY
)

VERIFIER_FILE="/tmp/cf-oauth-${STATE}.json"
if [[ ! -f "$VERIFIER_FILE" ]]; then
  echo "ERROR: No verifier file at $VERIFIER_FILE" >&2
  echo "Do not re-authorize yet — agent must issue a NEW link and save verifier first." >&2
  exit 2
fi

echo "Found verifier for state=$STATE"
echo "Hand this callback URL to hermes mcp login completion or agent token exchange:"
echo "$CALLBACK_URL"
echo ""
echo "If hermes mcp login is waiting in another terminal, paste the URL there."
echo "Otherwise agent completes exchange programmatically using saved verifier."
