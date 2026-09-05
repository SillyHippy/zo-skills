# Zo Computer integrations vs Hermes MCP tokens (2026-07)

Joseph connected Cloudflare the **easy way** on Zo Computer. Hermes on Telegram did **not** automatically get that access.

## Two separate auth systems

| System | Where OAuth lands | Token storage | Used by |
|--------|-------------------|---------------|---------|
| **Zo Computer integrations** | `https://{handle}.zo.computer/?t=integrations` → connect `mcp:cloudflare` | Zo platform | Zo Computer browser agent |
| **Hermes MCP** | `hermes mcp login cloudflare` or phone paste-back | `~/.hermes/mcp-tokens/*.json` | Hermes Telegram / gateway |

**Connecting on Zo does NOT feed Hermes.** Zo Computer confirmed this explicitly.

## Easy path (Zo Computer — what Joseph did)

1. Open integrations: `https://sillyhippy.zo.computer/?t=integrations`
2. Connect: **`mcp:cloudflare`** (Code Mode — `https://mcp.cloudflare.com/mcp`)
3. Click **Log In** → approve in browser on Zo
4. Done for Zo Computer agent

Optional additional MCPs on same page if listed: `cloudflare-bindings`, `cloudflare-builds`, `cloudflare-observability`.

## Hermes path (Telegram agent — separate)

Check status:

```bash
hermes mcp test cloudflare
hermes mcp test cloudflare-bindings
ls ~/.hermes/mcp-tokens/
```

Typical state after Joseph's Zo login:
- `cloudflare.json` ✅ (execute, search, docs)
- `cloudflare-bindings.json` ❌ often missing
- `wrangler whoami` ❌ often "not authenticated"

### Option A — API token (Joseph's preference)

See `references/cloudflare-api-token-setup.md`. One paste, no more links.

### Option B — Hermes OAuth in Zo terminal (browser on Zo)

```bash
hermes mcp login cloudflare-bindings
hermes mcp test cloudflare-bindings
hermes gateway restart
```

Run on **Zo terminal with browser** — not phone-only Telegram.

### Option C — Phone authorize + paste callback (last resort)

See `references/cloudflare-mcp-oauth.md`. Agent **must** persist PKCE verifier before giving link; complete exchange on paste — **never** start new session and ask re-authorize.

## What `cloudflare` MCP alone can do

Main server (`mcp_cloudflare_*` / `execute`) **did** cover D1 create + Worker deploy in 2026-07 session when OAuth token had write scopes — even before wrangler CLI auth. Still prefer API token file for headless redeploys.

**Hermes `cloudflare` MCP OAuth** (after phone paste-back with persisted PKCE) ≠ wrangler CLI. API token in env file satisfies both wrangler and REST.

## Official bootstrap doc

https://developers.cloudflare.com/agent-setup/prompt.md — installs Cloudflare skills + documents five MCP URLs. Map to Hermes via `/root/.hermes/config.yaml` `mcp_servers:`.

## Agent communication rule

When Joseph asks "can you deploy?":
- **Zo integrations connected** ≠ Hermes can deploy
- Answer honestly: check `hermes mcp test` + `wrangler whoami` + credentials file
- Do **not** send Zo terminal command blocks when Joseph wants **one phone link** — unless OAuth is already failing; then switch to API token immediately
