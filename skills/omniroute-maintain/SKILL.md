---
name: omniroute-maintain
description: Use when updating/fixing OmniRoute. Production-only behind /omniroute; webpack build; never npm run dev.
---

# OmniRoute Maintenance (reverse-proxy deployment)

## Current Deployment (verified 2026-08-30 — production)

| Key | Value |
|-----|-------|
| Source | `/home/workspace/Projects/omniroute/` |
| Git | `release/v3.8.51` (upstream release-branch tip) |
| Supervisor | `omniroute` in `/etc/zo/supervisord-user.conf` |
| Start command | **`run-standalone.mjs`** from `.build/next/standalone` (applies `OMNIROUTE_MEMORY_MB=4096`) |
| Port | `20128` |
| **BASE_PATH** | **`/omniroute`** (pinned in `.env` + supervisor + Zo env) |
| **Public base (OAuth)** | **`NEXT_PUBLIC_BASE_URL=https://zo-reverse-proxy-sillyhippy.zocomputer.io/omniroute`** |
| **Session cookies** | **`AUTH_COOKIE_SECURE=true`** |
| **Public API** | `https://zo-reverse-proxy-sillyhippy.zocomputer.io/omniroute/v1` |
| **OAuth redirect** | `https://zo-reverse-proxy-sillyhippy.zocomputer.io/omniroute/callback` |
| Zo service | `svc_ZSZehS2z81g` — **`mode=process`**, `public=false` |
| Browser URL | `https://zo-reverse-proxy-sillyhippy.zocomputer.io/omniroute/` |
| Hermes / API | **`http://127.0.0.1:20128/omniroute/v1`** (NEVER the proxy host) |
| Proxy route | `{ prefix: "/omniroute", target: "http://localhost:20128", preservePrefix: true }` |
| Data DB | `/root/.omniroute/storage.sqlite` |

**Canonical files (keep all three in sync after every edit):**
1. `/home/workspace/Skills/omniroute-maintain/` (source of truth)
2. `/root/.hermes/skills/omniroute-maintain/`
3. `/root/.hermes/skills/devops/omniroute-maintain/`

## ⛔ `scripts/dev/run-standalone.mjs` is PRODUCTION

The path contains `dev`. That is the upstream filename. It is **not** `npm run dev`.

It is the production wrapper: cwd = `.build/next/standalone`, `NODE_ENV=production`, applies `OMNIROUTE_MEMORY_MB` → `--max-old-space-size`, then starts `server-ws.mjs` (fallback `server.js`).

**Forbidden start commands (all of these are wrong on this VPS):**
- `npm run dev` / `next dev` / Turbopack HMR
- bare `node .build/next/standalone/server.js` (ignores the 4096 heap pin → empty model list / 503)
- `npm start`

**Correct supervisor command (exact):**
```
command=bash -c 'cd /home/workspace/Projects/omniroute/.build/next/standalone && exec node ../../../scripts/dev/run-standalone.mjs'
```
plus `NODE_ENV="production"` and `OMNIROUTE_MEMORY_MB="4096"`.

Live check: `tr '\0' '\n' < /proc/$(pgrep -f run-standalone.mjs | head -1)/environ | grep NODE_ENV` must be `production`. Process title on :20128 is `omniroute (v16…)` — not `next-server` from another app.

Zo Computer’s own UI (`next-server` on :3088 under `/__modal/volumes/.../web-standalone`) is **not** OmniRoute. Do not kill it. Do not treat it as OmniRoute dev mode.

## ⛔ HARD RULE — never `npm run dev` behind the reverse proxy

`npm run dev` needs a WebSocket to `/_next/webpack-hmr`. `zo-reverse-proxy` does not proxy that → login stuck on **"Loading..."**. curl 200 is a lie.

## ⛔ UPDATE RULES (2026-08-30 — yesterday’s break)

`npm run build` defaults to **Turbopack**. Turbopack native RAM hit **14GB+** here, never finished, and a killed/timed-out build **wipes** `.build/next/standalone` so OmniRoute cannot start.

1. **Only** `bash /home/workspace/Skills/omniroute-maintain/scripts/update-via-proxy.sh`. Do not invent a second `npm run build`.
2. **Webpack only:** `OMNIROUTE_USE_TURBOPACK=0`. Never Turbopack on this VPS.
3. Build heap **10GB** (`OMNIROUTE_BUILD_MEMORY_MB=10240`). Runtime stays **4096**. Abort if available RAM drops under **1500MB**.
4. **Never start a second build.** If `build-next-isolated.mjs` / `next build` is already running, wait or stop — do not launch another.
5. **Do not stop OmniRoute** until the new standalone exists (`BUILD_ID` + `.build/next/standalone/server.js`). Stopping first + a dead build = site down.
6. **Do not `npm install`** unless the user asked (`OMNIROUTE_NPM_INSTALL=1`). Install is the RAM-heavy path.
7. Run the update **detached** (session disconnect must not SIGTERM the build). A killed build deletes standalone.
8. Update backups (`/home/workspace/Backups/omniroute-update-*`) are **config + sqlite only**. They do **not** contain a restorable standalone. The Aug 13 zip the watchdog named is **gone** and was config-only anyway. Failed build → re-run webpack, do not pretend a zip restore will bring `:20128` back.
9. `verify.sh` must require `run-standalone.mjs`. Bare `server.js` / `npm start` is a **FAIL**.

## IDIOT-PROOF UPDATE (run this — do not invent steps)

```
/omni update
/omni verify
/omni status
```

Or:

```bash
bash /home/workspace/Skills/omniroute-maintain/scripts/update-via-proxy.sh
```

- Git upgrade to latest `release/vX.Y.Z` is **ON** (`OMNIROUTE_GIT_PULL=0` to skip).
- `OMNIROUTE_NPM_INSTALL=1` — also `npm install` (off by default; do not turn on for RAM).

Then:

```bash
bash /home/workspace/Skills/omniroute-maintain/scripts/verify.sh
```

**If verify fails:** stop. Re-pin + webpack rebuild. Do not claim success.

### What every model must remember
1. `OMNIROUTE_BASE_PATH` stays `/omniroute`.
2. Supervisor stays `run-standalone.mjs` + `OMNIROUTE_MEMORY_MB=4096` + `NODE_ENV=production`.
3. Every update = webpack production build (`OMNIROUTE_USE_TURBOPACK=0`) with `OMNIROUTE_BASE_PATH=/omniroute` **before** restart.
4. Proxy prefix stays `/omniroute` + `preservePrefix: true`.
5. Hermes URL stays `http://127.0.0.1:20128/omniroute/v1`.
6. Root `http://127.0.0.1:20128/v1` is wrong (404).
7. Never point Hermes at `zo-reverse-proxy-.../omniroute/v1`.
8. Zo `mode=process` — do not pass `local_port`.
9. After Zo MCP `update_user_service`, re-pin supervisor env.
10. curl UI 200 is not enough — `verify-login.mjs` must see a password field.
11. Do not `git reset --hard` / `git checkout .` to “clean” before updating.

## Manual checklist (only if the script cannot run)

1. Backup `.env`, `proxy.ts`, supervisor conf, `storage.sqlite`.
2. Confirm pins (`.env`, `run-standalone.mjs` + production, Zo env, proxy.ts).
3. **Leave OmniRoute running.** If a build is already in flight, do not start another.
4. `cd /home/workspace/Projects/omniroute && OMNIROUTE_BASE_PATH=/omniroute OMNIROUTE_USE_TURBOPACK=0 OMNIROUTE_BUILD_MEMORY_MB=10240 NODE_OPTIONS=--max-old-space-size=10240 npm run build`
5. Confirm `.build/next/BUILD_ID` and `.build/next/standalone/server.js` exist.
6. `supervisorctl -s http://127.0.0.1:29011 restart omniroute`
7. Wait until `curl` to `http://127.0.0.1:20128/omniroute/v1/models` is `200` or `401`.
8. `supervisorctl -s http://127.0.0.1:29011 restart zo-reverse-proxy`
9. Run `scripts/verify.sh`.

Do **not** restart the Hermes gateway unless the user says so. Catalog rediscovery is `/restart` on Telegram.

## Hermes providers that hit OmniRoute

```yaml
providers:
  omniroute:
    base_url: http://127.0.0.1:20128/omniroute/v1
    key_env: OMNIROUTE_API_KEY
  venice:
    base_url: http://127.0.0.1:20128/omniroute/v1
    key_env: OMNIROUTE_API_KEY
```

## Rollback

See `references/reverse-proxy-rule.md` → Rollback.
Config backup example: `/home/workspace/Backups/omniroute-update-20260830_152521/`.
That restores `.env` / sqlite / proxy / supervisor — **not** the Next standalone.

## Related
- DB / providers: `omniroute-management`
- Zo HTTP→process: `zo-service-registration`
- `references/reverse-proxy-rule.md`
- `references/supervisor.conf` — `run-standalone.mjs` + production
- `scripts/verify.sh` / `scripts/verify-login.mjs` / `scripts/update-via-proxy.sh`
