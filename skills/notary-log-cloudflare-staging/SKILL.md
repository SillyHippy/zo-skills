---
name: notary-log-cloudflare-staging
description: Deploy and verify Notary-log Cal multi-tenant on Cloudflare Workers STAGING only (wrangler.cal.toml). Never deploy production wrangler.toml or merge to main without explicit user approval. Auth default is API token — not OAuth loops.
---

# Notary-log Cloudflare Staging

## Safety rules (mandatory)

1. **NEVER** run `pnpm run deploy:cloudflare` or `wrangler deploy` without `-c wrangler.cal.toml`
2. **NEVER** merge `feature/cal-multi-tenant` → `main` without explicit user "ship to prod"
3. **NEVER** touch `notary-log.iannazzi.workers.dev` during staging work
4. Production Facebook group URL auto-deploys from **GitHub main only**

## Repo

- Path: `/home/workspace/Projects/Notary-log`
- Branch: `feature/cal-multi-tenant` — pushed to GitHub; **does not** auto-deploy CF
- Staging config: `wrangler.cal.toml` → Worker name `notary-log-cal-staging`
- Full port plan: `docs/CAL-CLOUDFLARE-FULL-PORT-PLAN.md`
- Shorter checklist: `docs/CAL-CLOUDFLARE-WORKERS-PLAN.md`

**Merge `main` today ≠ Cal on CF prod** until Joseph says ship — but **staging is live** (2026-07-19). See `references/cf-staging-live-2026-07-19.md`.

**Port status:** `cloudflare/cal-handlers.ts`, `cal-crypto.ts`, D1 schema, Worker wiring — **done on staging**. Prod Facebook Worker still journal-only until `main` merge + prod D1 binding.

## Cloudflare auth — API token FIRST (Joseph 2026-07)

**Joseph's rule:** *"Skip all OAuth forever — paste CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID once."*

Do **not** send OAuth links or Zo terminal login blocks when Joseph asks for credentials. Give dashboard navigation (login at dash.cloudflare.com first — direct profile URLs 404 when logged out).

| Path | When |
|------|------|
| **API token** (default) | Always offer first — `references/cloudflare-api-token-setup.md` |
| Zo integrations UI | Zo Computer only — `/?t=integrations` → `mcp:cloudflare` — **does not feed Hermes** |
| Hermes MCP OAuth | Fallback only — `references/cloudflare-mcp-oauth.md` |
| `cloudflare` MCP `execute` | May be enough for D1/deploy even without bindings/wrangler |

### Credentials file

```bash
set -a && source /home/workspace/credentials/notary-log-cloudflare.env && set +a
wrangler whoami
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/d1/database" | head -c 200
```

Both must succeed — **Workers Scripts alone is not enough** (D1 API returns auth error without **D1: Edit**).

```env
CLOUDFLARE_API_TOKEN=...   # prefix cfut_ is valid Cloudflare 2026 user token format
CLOUDFLARE_ACCOUNT_ID=...
```

**Pitfall — "Edit Cloudflare Workers" template:** Joseph's first token had Workers+KV but **no D1** → deploy failed. Fix: add **Account → D1 → Edit** on same token, or create **Notary-log Cal Deploy** token with Workers + D1 + KV. See `references/cloudflare-api-token-setup.md` (prefilled link + mobile UI notes).

### Zo vs Hermes (do not conflate)

Connecting Cloudflare on **Zo Computer integrations** does **not** authenticate **Hermes** (`~/.hermes/mcp-tokens/`). See `references/zo-integrations-vs-hermes-mcp.md`.

### OAuth anti-loop rules

If Joseph must use phone authorize + paste callback:
1. Save PKCE verifier **before** sending authorize link
2. Complete exchange on paste — **never** ask re-authorize for same `state`
3. After 2 failures → **stop OAuth**, request API token only

Script: `scripts/complete-mcp-oauth-callback.sh`

## One-time infra (staging account)

```bash
cd /home/workspace/Projects/Notary-log
wrangler d1 create notary-log-cal -c wrangler.cal.toml
# Paste database_id into wrangler.cal.toml → [[d1_databases]] database_id

wrangler d1 execute notary-log-cal --file=cloudflare/d1-schema.sql --remote -c wrangler.cal.toml

wrangler secret put CAL_WEBHOOK_SECRET -c wrangler.cal.toml
```

## Deploy staging (manual only)

```bash
cd /home/workspace/Projects/Notary-log
pnpm run deploy:cloudflare:cal:staging
```

Build sets `VITE_CAL_HOST_MODE=1` so Bookings + Cal Settings show on `*.workers.dev`.

## Verify

```bash
bun scripts/verify-cal-host.mjs https://notary-log-cal-staging.<account-subdomain>.workers.dev
```

Expect 18/18 checks. **Staging verified 2026-07-19:** https://notary-log-cal-staging.rawr88098809.workers.dev

Joseph confirms one real Cal booking on phone (optional — closes last live Cal→phone gap).

## What Joseph does after staging deploy

1. Open staging URL on phone
2. Settings → account auto-creates → Save Cal username
3. Cal → Webhooks → **staging** webhook URL (not Zo cal host)
4. One test booking → Bookings tab

## Dual deploy from one branch

| Target | Command | Auto? |
|--------|---------|-------|
| Zo cal host | `supervisorctl restart notary-log-cal` | No |
| CF staging | `pnpm run deploy:cloudflare:cal:staging` | No |
| CF prod | merge main → Workers Builds | **Yes — blocked until Joseph approves** |

## References

- `references/cf-staging-live-2026-07-19.md` — **live staging URL**, D1 id, verify results, merge gates
- `references/cloudflare-api-token-setup.md` — **default auth**; cfut_ format, D1 permission pitfall, prefilled link
- `references/zo-integrations-vs-hermes-mcp.md` — Zo integrations ≠ Hermes tokens; `execute` may cover D1
- `references/cloudflare-mcp-oauth.md` — OAuth fallback + anti-loop rules
- Official bootstrap: https://developers.cloudflare.com/agent-setup/prompt.md

## Honest deploy status (check before claiming)

| Target | Ready? | Check |
|--------|--------|-------|
| **CF staging** | ✅ Live 2026-07-19 | curl staging `/api/health`; verify script 18/18 |
| **CF prod (`main`)** | ❌ Not shipped | No merge until Joseph says ship |
| API token + D1 | ✅ | `wrangler whoami` + D1 list API |
| Hermes `cloudflare` MCP | ✅ optional | `hermes mcp test cloudflare` — `execute` worked for D1 create |
| Cal Worker code | ✅ on branch | `cloudflare/cal-handlers.ts` exists |

**Joseph communication:** When he asks "can you deploy?" — staging **yes** (already done); prod **no** until merge. Do not re-send OAuth links if credentials file + wrangler work.
