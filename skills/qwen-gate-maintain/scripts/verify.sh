#!/usr/bin/env bash
#
# Verify qwen-gate is healthy and usable by Hermes
#
set -euo pipefail

echo "=== Health ==="
curl -s http://localhost:26405/health | jq . || curl -s http://localhost:26405/health

echo ""
echo "=== Models (should include qwen3.7-plus) ==="
curl -s http://localhost:26405/v1/models | jq '.data[].id' | head -5 || curl -s http://localhost:26405/v1/models

echo ""
echo "=== Quick Hermes test (qwen3.7-plus) ==="
hermes chat -q "what is 2+2" -m qwen3.7-plus --provider qwen-gate --max-turns 1 2>&1 | tail -10

echo ""
echo "=== Dashboard BASE_PATH test (simulate reverse proxy) ==="
echo "With X-Forwarded-Prefix: /qwen"
curl -s -H "X-Forwarded-Prefix: /qwen" http://localhost:26405/dashboard | grep -o 'window.BASE_PATH = [^;]*' || echo "no BASE_PATH found"

echo ""
echo "Sample rewritten links (should be /qwen/... not /qwen/qwen/...):"
curl -s -H "X-Forwarded-Prefix: /qwen" http://localhost:26405/dashboard | grep -E 'href="|src="' | head -4

echo ""
echo "Verification complete."