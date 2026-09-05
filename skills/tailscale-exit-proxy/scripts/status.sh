#!/bin/bash
# tailscale-exit-proxy: Check status of all proxy instances
# Usage: status.sh

echo "=== Tailscale Exit Proxy Status ==="
echo ""

# Check each known proxy
declare -A PROXIES=(
  [1055]="Galaxy S26 Ultra"
  [1056]="Work Phone"
  [1057]="VPS Direct (microsocks)"
)

for PORT in 1055 1056 1057; do
  NAME="${PROXIES[$PORT]}"
  IP=$(curl -s --max-time 8 --socks5-hostname "127.0.0.1:${PORT}" https://ifconfig.me 2>/dev/null)
  if [ -n "${IP}" ]; then
    echo "✅ Port ${PORT} (${NAME}): ${IP}"
  else
    echo "❌ Port ${PORT} (${NAME}): FAILED"
  fi
done

echo ""
echo "=== VPS Direct IP ==="
VPS_IP=$(curl -s --max-time 5 https://ifconfig.me 2>/dev/null)
echo "VPS: ${VPS_IP}"

echo ""
echo "=== Managed Services ==="
# Show tailscaled processes
pgrep -af tailscaled 2>/dev/null | grep -v "sudo" || echo "No tailscaled processes"
pgrep -af microsocks 2>/dev/null || echo "No microsocks processes"
