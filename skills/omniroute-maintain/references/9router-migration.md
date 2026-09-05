# 9router → OmniRoute Migration

OmniRoute has a **native 9router JSON import** endpoint. This reference captures the gotchas discovered on 2026-07-25 after a real migration of 102 connections / 7 nodes / 125 custom models / 5 aliases / 1 API key.

## The native import endpoint (do NOT miss this)

`POST /api/settings/import-json` — exposed in the dashboard as **Settings → Import JSON**.

Accepts 9router's **camelCase** JSON backup schema directly: `providerConnections`, `providerNodes`, `apiKeys`, `modelAliases`, `settings`, `mitmAlias`, `pricing`. The migration code (`src/.../migrate9routerJson` or equivalent) reads these camelCase keys and inserts into OmniRoute's snake_case tables.

**Do NOT waste time writing a conversion script before trying the built-in import.** A previous session did exactly this because the assistant incorrectly claimed "there is no direct/native import from 9Router to OmniRoute." That was wrong. Try the dashboard import first.

## What imports cleanly (no intervention)

- `providerConnections` → `provider_connections` ✓ (camelCase → snake_case, 1:1)
- `providerNodes` → `provider_nodes` ✓
- `apiKeys` → `api_keys` ✓
- `modelAliases` → `model_aliases` ✓
- `settings`, `mitmAlias`, `pricing` ✓

## What does NOT import cleanly (known schema mismatches)

### 1. `customModels` — list vs dict mismatch
9router backup stores `customModels` as a **JSON array** of 125 items. The migration calls `Object.entries(data.customModels)`, which on an array produces `[[0, item], [1, item], ...]` — 125 rows keyed by numeric index, not by provider id. Broken.

**Fix:** before importing, transform `customModels` from a list into a dict keyed by provider id (group items by their `provider` field, or use the model name as key). Or skip the built-in import for customModels and insert them separately with a small script after the main import.

### 2. `proxyPools` — silently dropped
Migration looks for `proxyConfig` (object). 9router backup has `proxyPools` (list). Silently dropped — no error, no import.

**Fix:** map `proxyPools` → `proxyConfig` shape before import, or insert into `proxy_assignments` / `proxy_registry` separately after import. If you don't actually use proxies, just drop them.

### 3. Reserved built-in provider prefixes (CRITICAL)
OmniRoute has built-in providers named `longcat` and `modelscope` (with alias `ms`). If your 9router custom OpenAI-compatible nodes use `longcat/` or `ms/` as their prefix, **OmniRoute routes those requests to its built-in provider (which has no credentials) instead of your custom node**. Requests fail with "No active credentials for provider: longcat".

**Fix:** rename the colliding node prefixes before/after import. We used `lc2` (was `longcat`) and `ms2` (was `ms`). `clod` was unchanged (not reserved). After renaming, the prefixed node models work: `lc2/LongCat-2.0`, `ms2/Qwen/Qwen3-8B`, `clod/Gemma 4 31B IT`.

### 4. Bare aliases for custom-node models do NOT work
OmniRoute's alias resolution path (`getModelInfoCore` → `resolveProviderAlias`) only resolves **built-in provider ids**. An alias target like `lc2/LongCat-2.0` gets `lc2` looked up as a built-in provider (not found), and the request fails. Bare aliases work ONLY when the target prefix is a built-in provider (e.g. `oc/...` works because `oc` is the built-in opencode-go provider).

**Fix:** accept that custom-node models must be called by their full prefixed name (`lc2/LongCat-2.0`). Do not create bare aliases for them — they will fail and confuse users.

### 5. SearXNG port hardcoded to 8888
OmniRoute hardcodes `http://localhost:8888/search` for the `searxng-search` provider. The actual SearXNG instance on this VPS runs on **8080** (port 8888 is dead). Requests ECONNREFUSED.

**Fix options:**
- (A) Edit the Base URL in the dashboard to `http://localhost:8080/search` (per-connection override, no rebuild).
- (B) Disable the `searxng-search` connection and rely on `exa-search` (which works) — recommended if you don't need SearXNG.

### 6. Search routing auto-picks cheapest first
OmniRoute's search fallback chain tries providers in cost order: `searxng-search` (free) → `linkup-search` (cheap) → `exa-search` (paid). If searxng is dead (port mismatch) and linkup has no funds (429), searches die before Exa is tried — even though all 5 Exa keys are valid.

**Fix:** disable or fix the dead/broke connections (searxng port, linkup funds) so the fallback reaches Exa. Or call search with `provider: "exa-search"` explicitly.

### 7. Encrypted keys need `STORAGE_ENCRYPTION_KEY`
OmniRoute stores provider keys encrypted with `enc:v1:...` prefix. If `STORAGE_ENCRYPTION_KEY` is empty in `.env`, decryption returns null and all keys fail at runtime with 401 from the upstream (the empty/null key gets sent). Symptom: keys "test valid" via the test endpoint but fail at chat time.

**Fix:** ensure `STORAGE_ENCRYPTION_KEY` is set in `.env` (any non-empty value, but keep it stable — changing it invalidates all stored keys). Restart omniroute after setting.

## Ephemeral field sanitization (do this on import)

Reset runtime/backoff state so nothing restores into a locked/failed state:
- `errorCode`, `lastError`, `lastErrorAt` → NULL
- `backoffLevel`, `consecutiveUseCount` → 0
- `testStatus` → `"unknown"` (OmniRoute re-validates on first use)
- `modelLock_*` dynamic keys → drop (OmniRoute has no dynamic modelLock columns; it rebuilds lockout state in-memory)
- `lastUsedAt`, `lastRefreshAt` → NULL

The built-in `import-json` endpoint may already do some of this — verify after import by checking a few rows.

## Provider keys available on this VPS

For re-adding providers manually after a fresh DB wipe:

- **Exa Search** — 5 keys, one per email account (see `/home/workspace/credentials/master_keys.env` lines 321-325). All verified working. Bulk-add format: `email|apiKey` (one per line).
- **Jina Reader** — 1 unique key (was listed twice under two email labels but same value). Jina Reader is **free without an API key** for basic usage; the key only raises rate limits. Can leave the API key field blank.
- **Firecrawl** — 5 keys (1 dead, 4 working).
- **Tavily** — 1 key.
- **Steel.dev** — 4 keys (use direct API only, not through OmniRoute — JS-heavy pages).
- **Qwen Web (Free)** — 6 accounts (email + password `Crazy8809!`) stored in `/home/workspace/Projects/qwen-gate/.qwen/accounts.json`. **OmniRoute needs session cookies, not email/password.** The cookies ARE persisted on disk in qwen-gate's Chromium browser profiles at `/home/workspace/Projects/qwen-gate/.qwen/browser-profiles/<account>/Default/Cookies` (SQLite file, `encrypted_value` column, Chromium-encrypted). They are decryptable on Linux gVisor — see `qwen-gate-maintain/references/cookie-extraction.md` for the full recipe. To fill OmniRoute's "Session Cookie" field: decrypt the cookies and format as `email|cna=...; token=...; tfstk=...` (one per line, Bulk Add tab). Required cookies: `cna`, `token` (JWT), `tfstk` (the OmniRoute hint mentions `ssxmod_itna` but Qwen actually uses `tfstk` — same session role). Cookies expire in ~2 days; qwen-gate auto-refreshes them on disk, so re-dump after a refresh if needed. Alternatively, skip "Qwen Web (Free)" entirely and add qwen-gate as a custom OpenAI-compatible node (`http://localhost:26405/v1`, prefix `qg`) for auto-rotation across all 6 accounts.

## Vision / embedding flags — do NOT manually click per model

OmniRoute auto-applies `supportsVision` / `supportsEmbeddings` from three sources:
1. Built-in model specs (`src/shared/constants/modelSpecs.ts`) — hardcoded for ~60 well-known models.
2. Auto-discovery from upstream `/v1/models` (`detectVisionInput` reads `supportsVision`, `architecture.input_modalities`, `architecture.modality`).
3. Auto-sync scheduler — runs every 24h for connections with `autoSync` enabled.

The per-model checkboxes in the dashboard are **override** fields, not the primary source. Leave them null.

**When you DO need to click:** custom OpenAI-compatible nodes whose upstream `/v1/models` doesn't report vision capability (common with self-hosted backends). For those, click "Sync Models" once per provider (not per model) to trigger `/api/providers/[id]/sync-models`.

## Conversion script (fallback if built-in import is insufficient)

A working Python conversion script lives at `/tmp/convert_9router_to_omniroute.py` (created 2026-07-25). It:
- Reads the 9router JSON backup
- Sanitizes ephemeral fields
- Transforms camelCase → snake_case
- Inserts in FK-safe order: settings → proxy → provider_nodes → provider_connections → custom_models → api_keys → combos
- Is idempotent (wipe-then-insert)

Re-run only if the built-in `import-json` endpoint doesn't cover your use case (e.g. you need customModels as a proper dict, or proxyPools mapped to proxy_assignments). Backups of `storage.sqlite` before each step are saved to `/root/.omniroute/storage.sqlite.bak-*`.

## Post-import verification

```bash
# Counts
sqlite3 /root/.omniroute/storage.sqlite "SELECT COUNT(*) FROM provider_connections;"  # expect 102
sqlite3 /root/.omniroute/storage.sqlite "SELECT COUNT(*) FROM provider_nodes;"         # expect 7
sqlite3 /root/.omniroute/storage.sqlite "SELECT COUNT(*) FROM api_keys;"               # expect 1-2

# API
curl -s http://localhost:20128/v1/models | jq '.data | length'   # expect 400-600+

# Login
curl -s -X POST http://localhost:20128/api/auth/login -H 'Content-Type: application/json' \
  -d '{"password":"Crazy8809!"}' | jq .   # expect {"success":true}

# Public
curl -s -o /dev/null -w '%{http_code}' https://omniroute-sillyhippy.zocomputer.io/dashboard  # expect 200
```

## Bulk-add formats (verified working in OmniRoute dashboard)

These formats were used successfully on 2026-07-25 to import credentials into a fresh OmniRoute DB.

### Exa Search (5 keys, named by email account)
Bulk Add tab, one per line: `email|apiKey`
```
iannazzi.joseph@gmail.com|b102e0da-c193-4d9b-8c4b-7c9c77079fdb
iannazzi@alumni.nsuok.edu|1ca764df-f90b-4039-a958-8fecf680ed37
joseph.iannazzi@gmail.com|b0da6727-8892-4ca5-81f6-f4e34560a0ef
nicmys129@gmail.com|d57a19d4-c902-412f-a1aa-87b68d16b654
rawr88098809@gmail.com|34e33d3d-71d1-433a-bf2c-4e97d1ece224
```
Priority 1. All 5 verified valid against `https://api.exa.ai`.

### Qwen Web (Free) session cookies (6 accounts)
Bulk Add tab under "Qwen Web (Free)" provider, one per line: `email|cookie-string`
Cookie string must include `cna`, `token` (JWT), `tfstk`. See `qwen-gate-maintain/references/cookie-extraction.md` to decrypt from disk.

### Proxy bulk import (4 proxies)
Bulk Import Proxies dialog, pipe-delimited: `NAME|HOST|PORT|USERNAME|PASSWORD|TYPE`
```
Galaxy S26 Ultra|127.0.0.1|1055|||socks5
Work phone|127.0.0.1|1056|||socks5
Vps|127.0.0.1|1057|||socks5
Galaxy Note 9|127.0.0.1|1058|||socks5
```
Required: NAME, HOST, PORT. Optional: USERNAME, PASSWORD, TYPE. All 4 are socks5 on localhost (Tailscale/phone proxies).

## Backups retained (2026-07-25)

All `storage.sqlite.bak-*` snapshots in `/root/.omniroute/`:
- `.bak-pw-*` — before password change
- `.bak-import-*` — before 9router import
- `.bak-cm-*` — before customModels insert
- `.bak-prefix-*` — before prefix collision fix
- `.bak-exa-fix-*` — before exa investigation
- `.bak-wipe-*` — before fresh DB wipe (has the 102-connection state — restore this if a re-import goes sideways)
