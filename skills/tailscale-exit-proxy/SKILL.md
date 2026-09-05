---
name: tailscale-exit-proxy
description: Set up Tailscale SOCKS5 exit node proxies for IP rotation via 9Router round-robin. Use when adding a new phone as a proxy exit point, troubleshooting proxy connections, or setting up the proxy infrastructure on a new VPS.
compatibility: Requires Tailscale installed on VPS and Android phones. Zo Computer managed services.
metadata:
  author: sillyhippy.zo.computer
---

# Tailscale Exit Node Proxy

Route outbound traffic through Android phones via Tailscale exit nodes, exposed as local SOCKS5 proxies for 9Router round-robin.

## Architecture

```
9Router / OmniRoute (port 20128/20129)
  ├── Pool 1: socks5://127.0.0.1:1055 → Galaxy S26 Ultra (cellular)
  ├── Pool 2: socks5://127.0.0.1:1056 → Work Phone (cellular)
  ├── Pool 3: socks5://127.0.0.1:1057 → VPS Direct (microsocks)
  ├── Pool 4: socks5://127.0.0.1:1058 → Galaxy Note 9 (home WiFi)
  ├── Pool 5: socks5://127.0.0.1:1059 → Windows Laptop (home WiFi)
  └── Pool 6: socks5://127.0.0.1:1060 → Galaxy S21 (home WiFi)
```

Each tailscaled instance runs in userspace-networking mode with its own SOCKS5 port, routing through a different device as a Tailscale exit node. Exit-node devices can be **Android phones OR Windows laptops** (any device that can run Tailscale and advertise as an exit node).

## Adding a New Phone as a Proxy Exit

### Prerequisites on the Exit-Node Device

**Android phone:**
1. Install Tailscale from Play Store
2. Sign in with the same Tailscale account (`rawr88098809@gmail.com`)
3. Enable "Use as exit node" in Tailscale app settings
4. Approve it in admin console: https://login.tailscale.com/admin/machines → find device → three dots → "Edit route settings" → enable "Use as exit node"
5. If using a VPN (e.g., Premiumize), connect the VPN FIRST, then enable Tailscale exit node

**Windows laptop (added 2026-07-25):**
1. Install Tailscale from https://tailscale.com/download
2. Sign in with the same Tailscale account
3. Open PowerShell **as Administrator** and run:
   ```powershell
   tailscale set --advertise-exit-node
   ```
4. Approve it in the admin console (same path as above — find `laptop-n0h1aj8c` or whatever the hostname is → Edit route settings → enable exit node)

### ⚠️ Tailscale admin console does NOT show SOCKS5 ports
The admin console (login.tailscale.com/admin/machines) and the device detail screen in the Tailscale mobile app show: hostname, MagicDNS, IPv4, IPv6, OS, key expiry, connection status. They do **NOT** show the SOCKS5 proxy port — that port is a local `tailscale serve` / `tailscale funnel` setting configured on the device itself, not synced to the account dashboard. To find an existing device's proxy port, you must look on the device: Tailscale app → device → "Serve" / "Shared internally" section, or `tailscale serve status` in Termux/PowerShell. Don't expect to discover proxy ports from the admin console.

### Steps on the VPS

1. **Pick an available port** — existing: 1055, 1056, 1057, 1058, 1059, 1060. Next available: 1061+

2. **Get the phone's Tailscale IP:**
   ```bash
   tailscale status
   ```
   Note the `100.x.x.x` IP for the phone.

3. **Start a new tailscaled instance:**
   ```bash
   sudo tailscaled \
     --state=/var/lib/tailscale/tailscaled.state \
     --socket=/tmp/tailscale-proxy-N.sock \
     --tun=userspace-networking \
     --socks5-server=127.0.0.1:PORT \
     --port=0 \
     2>/dev/shm/tailscale-proxyN.log &
   ```

4. **Authenticate if needed:**
   ```bash
   tailscale --socket=/tmp/tailscale-proxy-N.sock status
   ```
   If "Logged out", get the auth URL from the log:
   ```bash
   grep "AuthURL" /dev/shm/tailscale-proxyN.log
   ```
   Open the URL in a browser and authenticate.

5. **Set the exit node:**
   ```bash
   tailscale --socket=/tmp/tailscale-proxy-N.sock set --exit-node=PHONE_IP --exit-node-allow-lan-access
   ```

6. **Verify:**
   ```bash
   curl -s --max-time 10 --socks5-hostname 127.0.0.1:PORT https://ifconfig.me
   ```
   The IP should differ from the VPS IP (`144.24.11.83`).

7. **Register as managed service:**
   ```bash
   # Create boot script at /home/workspace/Scripts/proxyN-boot.sh
   # Register with register_user_service (mode=process)
   ```

## Managed Services

| Service | Port | Exit Node | Device Type | Script |
|---------|------|-----------|-------------|--------|
| `tailscale-proxy1-galaxy` | 1055 | Galaxy S26 Ultra (100.101.208.121) | Android phone | `Scripts/proxy1-boot.sh` |
| `tailscale-proxy2-work` | 1056 | Work Phone (100.73.129.59) | Android phone | `Scripts/proxy2-boot.sh` |
| `proxy3-direct-vps` | 1057 | Direct (VPS IP 144.24.11.83) | VPS (microsocks) | `Scripts/proxy3-direct.sh` |
| `tailscale-proxy4-note9` | 1058 | Galaxy Note 9 (home WiFi) | Android phone | `Scripts/proxy4-boot.sh` |
| `tailscale-proxy5-laptop` | 1059 | Windows Laptop `laptop-n0h1aj8c` (100.75.93.105) | Windows laptop | `Scripts/proxy5-boot.sh` |
| `tailscale-proxy6-s21` | 1060 | Galaxy S21 `ks-s21` (100.114.2.60) | Android phone | `Scripts/proxy6-boot.sh` |

**Note:** Galaxy Note 9 (1058) and Galaxy S21 (1060) are different physical phones, both on the same home WiFi — they serve as backups of each other for IP rotation. The Windows laptop (1059) is also on the same home WiFi.

## Boot Scripts

Each proxy has a boot script at `/home/workspace/Scripts/proxyN-boot.sh` that:
1. Starts tailscaled with the correct SOCKS5 port
2. Waits 15 seconds for initialization
3. Configures the exit node
4. Stays alive as the main process

## Troubleshooting

**"node is not advertising an exit node":**
- The phone's exit node advertisement hasn't synced. Toggle exit node off/on in the phone's Tailscale app.
- Check admin console: phone must have "Exit Node" badge

**SOCKS5 connection timeout:**
- Check tailscaled is running: `ss -tlnp | grep PORT`
- Check auth: `tailscale --socket=/tmp/tailscale-proxy-N.sock status`
- Check logs: `cat /dev/shm/tailscale-proxyN.log | tail -20`

**Exit node works but DNS fails:**
- Wait 10-15 seconds after setting exit node for WireGuard handshake
- Test with IP first: `curl -s --socks5-hostname 127.0.0.1:PORT https://1.1.1.1/`

**Phone disconnected (Tailscale off):**
- That proxy pool will fail. 9Router round-robin should skip it.
- Other pools continue working.

## Phone Requirements

- Tailscale must be ON on the device for the proxy to work
- For cellular phones: exit IP = carrier's IP (unique per phone)
- For Wi-Fi phone: exit IP = home router's IP (unless VPN is used)
- For Wi-Fi phone with VPN: connect VPN FIRST, then Tailscale exit node
- For Windows laptop: same as Wi-Fi phone — exit IP = home router's IP unless a VPN is connected first
- A device showing "Not connected" in Tailscale means its proxy pool will fail until Tailscale is reconnected on the device; 9Router/OmniRoute round-robin should skip it

## 9Router Configuration

Add each proxy as a pool in 9Router's "Proxy Pools" page:

| Field | Value |
|-------|-------|
| Name | Descriptive name (e.g., "Galaxy S26 Ultra") |
| Proxy URL | `socks5://127.0.0.1:PORT` |
| No Proxy | `localhost,127.0.0.1,.internal` |
| Active | ON |
| Strict Proxy | OFF |

## Files

- `Scripts/proxy1-boot.sh` — Galaxy S26 Ultra boot script
- `Scripts/proxy2-boot.sh` — Work Phone boot script
- `Scripts/proxy3-direct.sh` — VPS direct proxy (microsocks)
- `Scripts/tailscale-proxy.sh` — Original combined startup script
- `Scripts/set-exit-nodes.sh` — Exit node configuration script

## VPS Direct Proxy

The VPS direct proxy uses `microsocks` (installed via apt) on port 1057. No Tailscale involved — traffic exits through the VPS's own public IP (`144.24.11.83`).
