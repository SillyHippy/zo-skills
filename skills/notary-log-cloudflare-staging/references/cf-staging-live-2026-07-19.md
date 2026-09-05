# CF Cal staging — live deploy (2026-07-19)

Joseph approved **`go CF port staging`**. Staging Worker is live and verified.

## URLs

| What | URL |
|------|-----|
| **Staging app** | https://notary-log-cal-staging.rawr88098809.workers.dev |
| **Health** | `GET /api/health` → `cal: true`, `calHostMode: true` |
| **Example book page** | `/book/joseph-joe-rf2msf` (after notary saves Cal username) |
| **Shared webhook** | `POST https://notary-log-cal-staging.rawr88098809.workers.dev/api/cal/webhook` |

Webhook secret: same as Zo cal host (`CAL_WEBHOOK_SECRET` on Worker). Copy from Settings after account + Cal username save, or from Zo cal host platform secret file.

## Verification (agent-run)

```bash
cd /home/workspace/Projects/Notary-log
bun scripts/verify-cal-host.mjs https://notary-log-cal-staging.rawr88098809.workers.dev
```

**Result:** 18/18 checks passed (two-account register, slug=username, 409 duplicate, webhook routing, no cross-contamination, pending bookings, book pages).

**Note:** On Worker URL, verifier must **not** wipe Zo SQLite — use remote-only mode / Worker target (see script flags if added).

## Infrastructure created

| Resource | Value |
|----------|--------|
| CF account | `966abe0fc380ff8b07e6c7f138a0e921` |
| D1 database | `notary-log-cal` id `c5b1d1da-96a1-42ee-a106-d3b8cb18af54` |
| Worker name | `notary-log-cal-staging` |
| Config | `wrangler.cal.toml` |
| Deploy cmd | `pnpm run deploy:cloudflare:cal:staging` |

## Code shipped (feature/cal-multi-tenant)

| File | Role |
|------|------|
| `cloudflare/cal-handlers.ts` | D1 port of `server/cal-routes.ts` |
| `cloudflare/cal-crypto.ts` | Web Crypto HMAC for Cal webhooks |
| `cloudflare/d1-schema.sql` | users + bookings (aligned to Zo columns) |
| `cloudflare/worker.ts` | Routes + `CAL_DB` binding |
| Build | `VITE_CAL_HOST_MODE=1` via staging deploy script |

## Not touched

- GitHub **`main`** — no merge
- Prod Worker **`notary-log.iannazzi.workers.dev`** — journal only
- Zo **`notary-log-cal-sillyhippy.zocomputer.io`** — still primary pilot URL

## Joseph manual test (~5 min)

1. Open staging URL on phone
2. Settings → account auto-creates → Save Cal username
3. Optional: Cal → Developer → Webhooks → staging URL + secret
4. One test booking → **Bookings** tab
5. Optional: Start journal entry (prefill only — journal same as CF prod client)

## Merge to prod gate

Do **not** merge `feature/cal-multi-tenant` → `main` until Joseph explicitly ships. Prod auto-deploys from `main` only.
