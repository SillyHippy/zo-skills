#!/usr/bin/env bash
# OmniRoute verification — reverse-proxy + BASE_PATH deployment.
# Exits non-zero on any failure.
set -u
export PATH=/usr/bin:/bin:/usr/local/bin:$PATH

PORT="20128"
BASE="/omniroute"
PROXY_LOCAL="http://127.0.0.1:9190${BASE}"
PROXY_PUBLIC="https://zo-reverse-proxy-sillyhippy.zocomputer.io${BASE}"
API_LOCAL="http://127.0.0.1:${PORT}${BASE}/v1/models"
API_KEY="${OMNIROUTE_API_KEY:-omniroute}"

pass=0; fail=0
ok()   { echo "  PASS $1"; pass=$((pass+1)); }
bad()  { echo "  FAIL $1"; fail=$((fail+1)); }

echo "=== OmniRoute verification (proxy + BASE_PATH) ==="

# 1. Supervisor
status=$(supervisorctl -s http://127.0.0.1:29011 status omniroute 2>&1 || true)
if echo "$status" | grep -q "RUNNING"; then
  ok "supervisor: $status"
else
  bad "supervisor: $status"
fi

# 2. BASE_PATH + PRODUCTION pins (dev/HMR behind proxy = stuck Login Loading...)
if grep -q '^OMNIROUTE_BASE_PATH=/omniroute' /home/workspace/Projects/omniroute/.env; then
  ok ".env has OMNIROUTE_BASE_PATH=/omniroute"
else
  bad ".env missing OMNIROUTE_BASE_PATH=/omniroute"
fi

if grep -q '^NEXT_PUBLIC_BASE_URL=https://zo-reverse-proxy-sillyhippy.zocomputer.io/omniroute' /home/workspace/Projects/omniroute/.env; then
  ok ".env has NEXT_PUBLIC_BASE_URL with /omniroute subpath"
else
  bad ".env NEXT_PUBLIC_BASE_URL must be https://zo-reverse-proxy-sillyhippy.zocomputer.io/omniroute"
fi

if grep -q '^AUTH_COOKIE_SECURE=true' /home/workspace/Projects/omniroute/.env; then
  ok ".env AUTH_COOKIE_SECURE=true (HTTPS proxy)"
else
  bad ".env AUTH_COOKIE_SECURE must be true behind HTTPS reverse proxy"
fi

block=$(grep -A12 '\[program:omniroute\]' /etc/zo/supervisord-user.conf || true)
if echo "$block" | grep -q 'OMNIROUTE_BASE_PATH="/omniroute"'; then
  ok "supervisor env pins OMNIROUTE_BASE_PATH"
else
  bad "supervisor env missing OMNIROUTE_BASE_PATH"
fi
if echo "$block" | grep -q 'run-standalone.mjs' \
   && ! echo "$block" | grep -qE 'command=npm (run )?dev|command=npm start|command=node .build/next/standalone/server.js'; then
  ok "supervisor command=run-standalone.mjs (production wrapper)"
else
  bad "supervisor must be run-standalone.mjs (not npm start, not npm run dev, not bare server.js)"
fi
if echo "$block" | grep -q 'NODE_ENV="production"'; then
  ok "supervisor NODE_ENV=production"
else
  bad "supervisor missing NODE_ENV=production"
fi
bp=$(python3 -c 'import json;print(json.load(open("/home/workspace/Projects/omniroute/.build/next/routes-manifest.json")).get("basePath",""))' 2>/dev/null || echo "")
if [ "$bp" = "/omniroute" ]; then
  ok "production build routes-manifest basePath=/omniroute"
else
  bad "production build missing basePath=/omniroute (got '${bp:-missing}'; run update script rebuild)"
fi

# 3. proxy.ts route
if grep -q 'prefix: "/omniroute"' /home/workspace/Projects/zo-reverse-proxy/proxy.ts \
   && grep -q 'preservePrefix: true' /home/workspace/Projects/zo-reverse-proxy/proxy.ts; then
  ok "proxy.ts has /omniroute preservePrefix route"
else
  bad "proxy.ts missing /omniroute preservePrefix route"
fi

# 4. Local API under basePath (THIS is what Hermes uses)
code=$(curl -s -o /dev/null -m 20 -w "%{http_code}" "$API_LOCAL" -H "Authorization: Bearer $API_KEY" 2>/dev/null || echo 000)
if [ "$code" = "200" ] || [ "$code" = "401" ]; then
  ok "localhost API $API_LOCAL → HTTP $code"
else
  bad "localhost API $API_LOCAL → HTTP $code (expected 200/401)"
fi

# 5. Root /v1 without basePath must NOT be the Hermes target anymore
code=$(curl -s -o /dev/null -m 10 -w "%{http_code}" "http://127.0.0.1:${PORT}/v1/models" 2>/dev/null || echo 000)
if [ "$code" = "404" ]; then
  ok "root /v1/models correctly 404 under basePath (use ${BASE}/v1)"
else
  echo "  NOTE root /v1/models → HTTP $code (ok only if BASE_PATH empty)"
fi

# 6. Local proxy UI + API
code=$(curl -s -o /dev/null -m 20 -L -w "%{http_code}" "${PROXY_LOCAL}/" 2>/dev/null || echo 000)
if [ "$code" = "200" ]; then
  ok "local proxy UI ${PROXY_LOCAL}/ → HTTP 200"
else
  bad "local proxy UI ${PROXY_LOCAL}/ → HTTP $code"
fi

code=$(curl -s -o /dev/null -m 20 -w "%{http_code}" "${PROXY_LOCAL}/v1/models" 2>/dev/null || echo 000)
if [ "$code" = "200" ] || [ "$code" = "401" ]; then
  ok "local proxy API → HTTP $code"
else
  bad "local proxy API → HTTP $code"
fi

# 7. Public proxy
code=$(curl -s -o /dev/null -m 25 -L -w "%{http_code}" "${PROXY_PUBLIC}/" 2>/dev/null || echo 000)
if [ "$code" = "200" ]; then
  ok "public proxy UI ${PROXY_PUBLIC}/ → HTTP 200"
else
  bad "public proxy UI → HTTP $code"
fi

code=$(curl -s -o /dev/null -m 20 -w "%{http_code}" "https://zo-reverse-proxy-sillyhippy.zocomputer.io/v1/models" 2>/dev/null || echo 000)
if [ "$code" = "404" ]; then
  ok "wrong public API /v1/models → 404 (must use /omniroute/v1)"
else
  bad "wrong public API /v1/models → HTTP $code (expected 404)"
fi

code=$(curl -s -o /dev/null -m 20 -w "%{http_code}" "${PROXY_PUBLIC}/v1/models" -H "Authorization: Bearer $API_KEY" 2>/dev/null || echo 000)
if [ "$code" = "200" ] || [ "$code" = "401" ]; then
  ok "public proxy API ${PROXY_PUBLIC}/v1/models → HTTP $code"
else
  bad "public proxy API ${PROXY_PUBLIC}/v1/models → HTTP $code"
fi

code=$(curl -s -o /dev/null -m 20 -w "%{http_code}" "${PROXY_PUBLIC}/callback" 2>/dev/null || echo 000)
if [ "$code" = "200" ] || [ "$code" = "302" ] || [ "$code" = "307" ]; then
  ok "OAuth callback path ${PROXY_PUBLIC}/callback → HTTP $code"
else
  bad "OAuth callback ${PROXY_PUBLIC}/callback → HTTP $code (expected 200/302)"
fi

# 8. Hermes config pin
if grep -q 'http://127.0.0.1:20128/omniroute/v1' /root/.hermes/config.yaml; then
  ok "Hermes omniroute/venice URL uses localhost+basePath"
else
  bad "Hermes config missing http://127.0.0.1:20128/omniroute/v1"
fi

# 9. Browser login hydrate (curl 200 lies — catches stuck Loading...)
if node /home/workspace/Skills/omniroute-maintain/scripts/verify-login.mjs; then
  ok "browser login form hydrates via public proxy"
else
  bad "browser login stuck/broken via public proxy (see verify-login.mjs)"
fi

# 10. RAM note
rss=$(ps -o rss= -C node 2>/dev/null | sort -n | tail -1 | tr -d ' ')
if [ -n "${rss:-}" ]; then
  ok "largest node RSS ~$((rss/1024)) MB (informational)"
fi

echo ""
echo "=== Result: $pass passed, $fail failed ==="
echo "Browser URL: ${PROXY_PUBLIC}/"
echo "Hermes API:  http://127.0.0.1:${PORT}${BASE}/v1"
exit $fail
