#!/bin/bash
# tailscale-exit-proxy: Add a new phone as a SOCKS5 exit node
# Usage: add-proxy.sh PORT PHONE_NAME TAILSCALE_IP
# Example: add-proxy.sh 1058 wifi-phone 100.99.99.99

set -e

PORT="${1:?Usage: add-proxy.sh PORT PHONE_NAME TAILSCALE_IP}"
PHONE_NAME="${2:?Usage: add-proxy.sh PORT PHONE_NAME TAILSCALE_IP}"
TAILSCALE_IP="${3:?Usage: add-proxy.sh PORT PHONE_NAME TAILSCALE_IP}"

SOCKET="/tmp/tailscale-proxy-${PHONE_NAME}.sock"
LOG="/dev/shm/tailscale-proxy-${PHONE_NAME}.log"
STATE_DIR="/var/lib/tailscale-proxy-${PHONE_NAME}"
BOOT_SCRIPT="/home/workspace/Scripts/proxy-${PHONE_NAME}.sh"

echo "=== Adding Tailscale exit proxy: ${PHONE_NAME} ==="
echo "Port: ${PORT}"
echo "Phone IP: ${TAILSCALE_IP}"
echo "Socket: ${SOCKET}"
echo ""

# 1. Create state directory
mkdir -p "${STATE_DIR}"
echo "[1/5] State directory: ${STATE_DIR}"

# 2. Copy auth state from main tailscaled
cp /var/lib/tailscale/tailscaled.state "${STATE_DIR}/" 2>/dev/null || true
echo "[2/5] Auth state copied"

# 3. Start tailscaled
echo "[3/5] Starting tailscaled..."
sudo tailscaled \
  --state="${STATE_DIR}/tailscaled.state" \
  --socket="${SOCKET}" \
  --tun=userspace-networking \
  --socks5-server="127.0.0.1:${PORT}" \
  --port=0 \
  2>"${LOG}" &
TAILSCALED_PID=$!
echo "PID: ${TAILSCALED_PID}"

# 4. Wait for startup
echo "[4/5] Waiting for tailscaled to initialize..."
sleep 10

# Check if authenticated
STATUS=$(tailscale --socket="${SOCKET}" status 2>&1)
if echo "${STATUS}" | grep -q "Logged out"; then
  echo ""
  echo "*** AUTHENTICATION REQUIRED ***"
  AUTH_URL=$(grep -oP 'https://login\.tailscale\.com/a/\w+' "${LOG}" | head -1)
  if [ -z "${AUTH_URL}" ]; then
    # Try getting it by running 'up'
    timeout 10 tailscale --socket="${SOCKET}" up --timeout=10s 2>&1 || true
    AUTH_URL=$(grep -oP 'https://login\.tailscale\.com/a/\w+' "${LOG}" | tail -1)
  fi
  echo "Open this URL to authenticate:"
  echo "  ${AUTH_URL}"
  echo ""
  echo "After authenticating, run:"
  echo "  tailscale --socket=${SOCKET} set --exit-node=${TAILSCALE_IP} --exit-node-allow-lan-access"
  echo ""
  exit 0
fi

echo "Already authenticated"

# 5. Set exit node
echo "[5/5] Setting exit node to ${TAILSCALE_IP}..."
tailscale --socket="${SOCKET}" set --exit-node="${TAILSCALE_IP}" --exit-node-allow-lan-access 2>&1

sleep 5

# 6. Verify
echo ""
echo "=== Verification ==="
RESULT=$(curl -s --max-time 10 --socks5-hostname "127.0.0.1:${PORT}" https://ifconfig.me 2>&1)
echo "Exit IP via port ${PORT}: ${RESULT}"

# 7. Create boot script
cat > "${BOOT_SCRIPT}" << BOOT
#!/bin/bash
sudo tailscaled \\
  --state=${STATE_DIR}/tailscaled.state \\
  --socket=${SOCKET} \\
  --tun=userspace-networking \\
  --socks5-server=127.0.0.1:${PORT} \\
  --port=0 \\
  2>/dev/shm/tailscale-proxy-${PHONE_NAME}.log &
TAILSCALED_PID=\$!
sleep 15
tailscale --socket=${SOCKET} set --exit-node=${TAILSCALE_IP} --exit-node-allow-lan-access 2>/dev/null &
wait \$TAILSCALED_PID
BOOT
chmod +x "${BOOT_SCRIPT}"
echo ""
echo "Boot script created: ${BOOT_SCRIPT}"

echo ""
echo "=== 9Router Pool Entry ==="
echo "Name: ${PHONE_NAME}"
echo "Proxy URL: socks5://127.0.0.1:${PORT}"
echo "No Proxy: localhost,127.0.0.1,.internal"
echo ""
echo "Done! Register as managed service:"
echo "  register_user_service label=proxy-${PHONE_NAME} mode=process entrypoint='bash ${BOOT_SCRIPT}'"
