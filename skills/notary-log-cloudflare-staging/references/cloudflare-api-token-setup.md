# Cloudflare API token — Notary-log staging (Joseph 2026-07)

**Default auth path.** Joseph explicitly rejected repeated OAuth loops: *"skip all OAuth forever — paste CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID once."*

## Why API token beats OAuth (for Hermes on Telegram)

| Path | Works from Telegram agent? | User steps |
|------|---------------------------|------------|
| **API token** | ✅ Yes — fully headless | Login dashboard → create token → paste 2 lines |
| Zo integrations UI (`/?t=integrations`) | ✅ For **Zo Computer only** | Click Log In once |
| Hermes `hermes mcp login` + phone paste | ⚠️ Fragile | Authorize + paste `127.0.0.1` callback; PKCE must persist |
| Direct profile URLs while logged out | ❌ **404** | Must log in at dash first |

## Step-by-step (no special URLs — avoids 404)

### 1. Log in

Open **https://dash.cloudflare.com** in browser → sign into **staging** Cloudflare account (empty account Joseph offered for Cal testing).

### 2. Account ID

1. Left sidebar → **Workers & Pages**
2. **Overview** page → copy **Account ID** (32-char hex, right column)

### 3. API token

**Joseph preference:** minimal clicks — not 352 permission toggles. Use **prefilled link** (logged in first):

https://dash.cloudflare.com/profile/api-tokens?permissionGroupKeys=%5B%7B%22key%22%3A%22workers_scripts%22%2C%22type%22%3A%22edit%22%7D%2C%7B%22key%22%3A%22d1%22%2C%22type%22%3A%22edit%22%7D%2C%7B%22key%22%3A%22workers_kv_storage%22%2C%22type%22%3A%22edit%22%7D%2C%7B%22key%22%3A%22account_settings%22%2C%22type%22%3A%22read%22%7D%5D&accountId=*&name=Notary-log%20Cal%20Deploy

Summary **must** show **D1 — Edit** (not just Workers Scripts / Access).

**Manual path** (if link 404 — log in at dash first):

1. Profile icon → **My Profile** → **API Tokens** → **Create Token**
2. Template **Edit Cloudflare Workers** → **then add D1 Edit** (template alone **failed** in session — token could deploy Workers but D1 API returned auth error)
3. Or **Custom token** → Account permissions: Workers Scripts Edit, **D1 Edit**, KV Edit, Account Settings Read
4. **Create Token** → copy secret immediately

**Token format:** `cfut_...` is **valid** Cloudflare user API token (2026). Do **not** tell Joseph it's a "preview ID" — wrong diagnosis caused a loop. Invalid token = **wrong permissions**, not wrong prefix.

**Mobile pitfall:** Zo/MCP token UI may only offer **Access** scopes (Apps:Edit, Audit Logs). That token **cannot** deploy Workers or D1. Joseph must use dashboard **Create Token** with Workers + **D1**, not the three-option Access flow.

### 4. Save on Zo (agent)

```bash
mkdir -p /home/workspace/credentials
cat > /home/workspace/credentials/notary-log-cloudflare.env << 'EOF'
CLOUDFLARE_API_TOKEN=paste_here
CLOUDFLARE_ACCOUNT_ID=paste_here
EOF
chmod 600 /home/workspace/credentials/notary-log-cloudflare.env
```

### 5. Verify

```bash
set -a && source /home/workspace/credentials/notary-log-cloudflare.env && set +a
wrangler whoami
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/d1/database"
```

Must show staging account **and** D1 list (empty `[]` is OK). If D1 returns authentication error → token missing **D1: Edit**.

## What Joseph pastes in chat

Two lines only:

```text
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=...
```

Agent saves to env file. **Do not** ask for OAuth after this.

## Security

- Staging throwaway account → broad Workers+D1 token is OK
- Prod Facebook Worker account → agent still only deploys `wrangler.cal.toml` unless Joseph says ship prod
- Never put token in MEMORY.md or git

## After token is saved

Joseph says **`go CF port staging`** → agent creates D1 (if needed), deploys `notary-log-cal-staging.*.workers.dev`, runs verify. **No `main` merge.**

**Completed 2026-07-19:** staging live at https://notary-log-cal-staging.rawr88098809.workers.dev — see `references/cf-staging-live-2026-07-19.md`.
