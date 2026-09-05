# OmniRoute Reverse-Proxy Rule (current — 2026-08-30)

## The rule (one line)
OmniRoute runs as a **process-mode** supervisor service on `localhost:20128` with
`OMNIROUTE_BASE_PATH=/omniroute`, and is reached in the browser via:

`https://zo-reverse-proxy-sillyhippy.zocomputer.io/omniroute/`

Hermes / APIs **never** use the reverse-proxy URL. They use:

`http://127.0.0.1:20128/omniroute/v1`

## Why this works
- OmniRoute’s `next.config.mjs` sets `basePath: process.env.OMNIROUTE_BASE_PATH || ""`.
- Proxy route uses `preservePrefix: true` so `/omniroute/...` is forwarded unchanged.
- Prefix in `proxy.ts` **must equal** `OMNIROUTE_BASE_PATH` exactly (`/omniroute`).
- Process runs **`run-standalone.mjs` (production wrapper)**. Path contains `dev`;
  that is the upstream filename, not `npm run dev`. Dev/HMR WebSockets are not
  proxied by `zo-reverse-proxy`; `npm run dev` leaves `/login` stuck on "Loading...".

## Pins (must exist after every update)
1. `/home/workspace/Projects/omniroute/.env` → `OMNIROUTE_BASE_PATH=/omniroute`
2. Supervisor `[program:omniroute]`:
   - `command=bash -c 'cd /home/workspace/Projects/omniroute/.build/next/standalone && exec node ../../../scripts/dev/run-standalone.mjs'`
   - `environment=` includes `OMNIROUTE_BASE_PATH="/omniroute"`, `NODE_ENV="production"`, `OMNIROUTE_MEMORY_MB="4096"`
3. Fresh production build with `OMNIROUTE_BASE_PATH=/omniroute` (`routes-manifest` basePath)
4. Zo MCP service `omniroute` env_vars includes `OMNIROUTE_BASE_PATH=/omniroute`
5. `proxy.ts` has:
   `{ prefix: "/omniroute", target: "http://localhost:20128", preservePrefix: true }`
   and excludes `/omniroute` from HTML path rewriting
6. Hermes `providers.omniroute.base_url` (and any Omni-backed provider like `venice`) =
   `http://127.0.0.1:20128/omniroute/v1`
7. Browser verify: password field visible at `/omniroute/login` (not infinite Loading...)

## Zo service mode
- `mode=process`, `public=false` (frees the HTTP slot)
- Do **not** pass `local_port` when mode=process (Zo rejects it)
- Port comes from env: `PORT=20128`

## Foolproof Hermes rule
If the proxy UI breaks after an update, **chat still works** as long as
`127.0.0.1:20128/omniroute/v1` answers. Fix UI/basePath separately; do not
point Hermes at the public proxy host.

## Rollback (emergency)
1. Set `OMNIROUTE_BASE_PATH=` empty in `.env` + supervisor + Zo env
2. Remove `/omniroute` route from `proxy.ts`
3. Restart omniroute + zo-reverse-proxy
4. Restore Hermes URLs to `http://127.0.0.1:20128/v1`
5. Optionally re-enable Zo `mode=http` `public=true` `local_port=20128`
