---
name: modal-on-zo
description: Run Modal.com from Zo Computer safely — remote compute only, workspace-owned artifacts, never attach or delete platform volumes under /__modal or /mnt/web_build. Use when the user says Modal, modal.com, modal run, modal deploy, Modal credits, or wants GPU/serverless jobs without bloating the 512 GB VPS.
compatibility: Created for Zo Computer; requires Modal CLI (modal) and user Modal account profiles in ~/.modal.toml
metadata:
  author: sillyhippy.zo.computer
---

# Modal on Zo (safe usage)

**Read this entire skill before any Modal CLI command, volume create/delete, or deploy.**

## When to use

- User wants to use Modal.com again (e.g. monthly credits, GPU, serverless Python).
- User asks how to run jobs without filling the Zo disk.
- User mentions stale `/__modal`, `web_build`, or `zo-tools` mounts.

## Non-negotiable rules

### 0. Zo platform volumes (NOT yours — do not delete or unmount)

Zo Computer mounts **read-only 9p** platform volumes on every host:

| Mount inside VM | Role |
|-----------------|------|
| `/__modal/volumes/vo-hUAIGF3JyIfa2OZaTGr6op` → `/mnt/web_build` | Zo **web app build** (e.g. `web-standalone/node_modules`) |
| `/__modal/volumes/vo-YZGBuOFIMj36ysFJx7jnlI` → `/mnt/zo-tools` | Zo **shared tool binaries** (d2, frpc, etc.) |

**Authoritative (Zo support, 2026):** These are **not** from your Modal.com workspaces. Deleting volumes in modal.com does not affect them. They are **not stored on your 512 GB quota** — disk usage is measured on real filesystems (`/`, `/home/workspace`). `du` on `/__modal/volumes` **over-counts** by walking shared platform content.

**Do not** ask support to unmount them to “free space” — that would **break the Zo web app**, and would not reclaim your quota anyway.

Your **real** usage is what `df` shows on `/` (~150 GB range), mostly `/usr`, `/root`, `/home/workspace`, swap — not the ~39 GB phantom from `du` on platform mounts.

### 1. Two filesystem worlds

| Location | Who owns it | You may delete? |
|----------|-------------|-----------------|
| `/home/workspace/**` | User | Yes (`rm`, normal disk) |
| `~/.modal.toml`, Modal cloud volumes **you named** | User Modal account | Yes via `modal volume delete -y YOUR-NAME` |
| `/__modal/volumes/*`, `/mnt/web_build`, `/mnt/zo-tools` | Zo platform + stale host mounts | **No** — read-only 9p; Zo support only |

**Never** run `modal volume delete` on volume IDs you did not create for a personal project (e.g. `vo-hUAIGF3JyIfa2OZaTGr6op`). **Never** `rm -rf` under `/__modal` or `/mnt/web_build` — it fails and wastes time.

### 2. Architecture (avoid Zo support next time)

- **Zo VPS** = code in `/home/workspace`, secrets in Zo Settings, trigger runs with `modal run` / `modal deploy` from workspace.
- **Modal cloud** = compute + optional **named** Modal volumes (billable on Modal, not Zo 512 GB).
- **Artifacts on Zo** = copy results into `/home/workspace/Projects/modal-exports/` (or user path) via `modal volume get` / download / script output — not by mounting big volumes onto the Zo VM.

Do **not** design flows that persist large caches on the Zo host via platform paths.

### 3. Before first Modal action in a session

Run preflight:

```bash
python3 /home/workspace/Skills/modal-on-zo/scripts/preflight.py
```

Follow printed checklist. If preflight fails (unknown active profile, mystery volumes), stop and ask user before `volume create` or `deploy`.

### 4. Volume naming and lifecycle

- Prefix user volumes: e.g. `joe-legal-cache`, `joe-modal-scratch` — never generic names that could collide with platform.
- Create: `modal volume create YOUR-NAME` (only when persistence on Modal is required).
- Mount **only inside Modal remote** functions/sandboxes at paths like `/data`, not on Zo paths.
- Tear down: `modal volume list` → confirm only your names → `modal volume delete -y YOUR-NAME` when no deployed app still references it.

### 5. Profiles and tokens

- User profiles on this host: `iannazzi-joseph`, `rawr88098809` (see `~/.modal.toml`).
- `MODAL_TOKEN_ID` prefix `ak-uIGIJ...` is Zo-injected for platform — **do not** use it to reason about which volumes are "yours."
- Set active profile explicitly: `modal profile activate rawr88098809` (or user choice) before user-owned volume ops.

### 6. Cost clarity

- Modal bills: GPU/time, Modal volume storage (cloud), egress per Modal pricing.
- Zo 512 GB: workspace + system; stale platform mounts are **not** freed by Modal dashboard delete alone.
- Prefer ephemeral Modal disk for one-off runs; persistent Modal volumes only when user accepts Modal-side storage cost.

### 7. Stale ~39 GB already on host

Documented in `Documents/modal-safe-usage.md` and `Documents/Zo-support-ticket-modal-volumes.md`. Using Modal again **correctly** does not require new host mounts under `/__modal` for user projects. Existing stale mounts still need Zo support to reclaim disk.

## Standard workflow

1. Read `references/checklist.md` if user is returning after a break.
2. Run `scripts/preflight.py`.
3. Put project under `/home/workspace/Projects/<name>/` with `modal` App code; no volumes unless user requests persistence.
4. `modal run` or `modal deploy` from project dir with correct `--env` / profile.
5. Pull outputs to workspace; delete user Modal volumes when done.
6. Do not modify ServTracker DB or Zo platform services unless user explicitly asks.

## References

- `references/checklist.md` — copy-paste session checklist
- `references/paths-and-mounts.md` — mount table and support escalation
- `/home/workspace/Documents/modal-safe-usage.md` — user-facing summary

## Tool mapping

- Shell: `bash` with `modal` CLI
- Secrets: user adds `MODAL_TOKEN_*` in Settings only if not using `modal token set` / profiles file