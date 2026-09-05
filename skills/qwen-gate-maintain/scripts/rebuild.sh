#!/usr/bin/env bash
#
# Safe rebuild + restart for qwen-gate
# Usage: ./rebuild.sh
#
set -euo pipefail

SKILL_DIR="/home/workspace/Skills/qwen-gate-maintain"
PROJECT="/home/workspace/Projects/qwen-gate"
SUPERVISOR_CONF="/etc/zo/supervisord-user.conf"

echo "=== Stopping qwen-gate ==="
supervisorctl -c "$SUPERVISOR_CONF" stop qwen-gate || true

echo "=== Killing any leftover processes ==="
pkill -9 -f "bun src/index.tsx" 2>/dev/null || true
sleep 2

echo "=== Entering project ==="
cd "$PROJECT"

echo "=== Building ==="
bun run build

echo "=== Starting via supervisor ==="
supervisorctl -c "$SUPERVISOR_CONF" start qwen-gate

echo "=== Waiting for startup ==="
sleep 8

echo "=== Status ==="
supervisorctl -c "$SUPERVISOR_CONF" status qwen-gate

echo "=== Health check ==="
curl -s http://localhost:26405/health | jq . || curl -s http://localhost:26405/health

echo "Done."