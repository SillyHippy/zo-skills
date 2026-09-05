# Cloudflare MCP OAuth for Notary-log staging (2026-07-19, updated)

**Fallback only.** Joseph's rule: **API token first** (`references/cloudflare-api-token-setup.md`). Use OAuth only if Joseph refuses token and insists on MCP login.

## Goal

Authenticate Hermes Cloudflare MCP so agent can create D1, set secrets, deploy **staging only** (`wrangler.cal.toml`) without merging `main`.

## MCP servers (Hermes config)

| Server | Auth | Needed for staging |
|--------|------|-------------------|
| `cloudflare` | OAuth | ✅ API `execute` — often **enough alone** |
| `cloudflare-bindings` | OAuth | D1/KV/secrets via MCP (optional if token or execute works) |
| `cloudflare-docs` | None | Docs search |
| `cloudflare-builds` | OAuth | Optional — deploy status |
| `cloudflare-observability` | OAuth | Optional — logs |

After MCP config change: `hermes gateway restart` (separate terminal).

## Zo integrations ≠ Hermes (CRITICAL)

Joseph connected `mcp:cloudflare` on `https://sillyhippy.zo.computer/?t=integrations`. That **does not** populate `~/.hermes/mcp-tokens/`. See `references/zo-integrations-vs-hermes-mcp.md`.

## Preferred paths (in order)

### 1. API token (Joseph's choice — do this first)

`/home/workspace/credentials/notary-log-cloudflare.env` → `wrangler whoami` passes. No OAuth.

### 2. Zo terminal browser login

```bash
hermes mcp login cloudflare-bindings
hermes mcp test cloudflare-bindings
```

Browser opens **on Zo** — callback hits Zo localhost, not Joseph's phone.

### 3. Phone authorize + paste callback (fragile)

**User flow:** one authorize link → Allow → copy full `http://127.0.0.1:PORT/callback?code=...&state=...` → paste to agent.

**Agent rules (mandatory — prevents "how many times do I authorize?" loops):**

1. **Before** sending authorize URL: persist `{state, code_verifier, redirect_uri, client_id}` to disk (e.g. `/tmp/cf-oauth-${STATE}.json` or `/dev/shm/cf-oauth-sessions/`).
2. When Joseph pastes callback: **complete token exchange with saved verifier** for that `state`.
3. **Never** start a new OAuth session after Joseph pasted a valid callback for the current `state`.
4. **Never** ask re-authorize because the previous code "expired" if verifier file still exists — the failure is agent-side exchange, not user error.
5. Authorize URL must return **HTTP 200** when fetched server-side. Cloudflare **500 Server Error** with Error ID = stale/dead session → one fresh link only.
6. If exchange fails with "verifier not found" → agent bug (verifier not saved). Issue **one** new link with verifier saved; do **not** blame Joseph.

Helper script: `scripts/complete-mcp-oauth-callback.sh` (checks verifier file exists).

**Wrong:** Sending Zo terminal command blocks when Joseph expects one phone link (unless Option 3 already failed twice — then switch to API token).

## Verify auth before claiming deploy-ready

```bash
hermes mcp test cloudflare
hermes mcp test cloudflare-bindings   # or skip if API token + wrangler OK
wrangler whoami
test -f /home/workspace/credentials/notary-log-cloudflare.env && echo token_file_ok
```

**Honest status tiers:**

| Claim | Requires |
|-------|----------|
| "Cloudflare MCP logged in" | `hermes mcp test cloudflare` pass |
| "Can deploy D1/secrets" | API token + `wrangler whoami` **OR** bindings MCP **OR** `execute` API |
| "Cal staging deployed on CF" | D1 + `cal-handlers.ts` + staging deploy + verify 18/18 — **done 2026-07-19** see `references/cf-staging-live-2026-07-19.md` |

OAuth alone was never sufficient — code port required. **Completed** after API token + port.

## Staging account vs prod

- Joseph's **dedicated empty staging CF account** when possible.
- **Never** deploy `wrangler.toml` (prod `notary-log` / Facebook group) during staging.
- `main` merge auto-deploys prod — blocked until Joseph says ship.

## After auth: deploy sequence

Parent skill `notary-log-cloudflare-staging` — D1 create → `d1-schema.sql` → `cal-handlers.ts` → `pnpm run deploy:cloudflare:cal:staging` → `verify-cal-host.mjs` on staging URL.

**Completed 2026-07-19:** https://notary-log-cal-staging.rawr88098809.workers.dev
