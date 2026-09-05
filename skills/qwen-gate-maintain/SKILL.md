---
name: qwen-gate-maintain
description: Maintain, rebuild, and restart the qwen-gate Qwen API proxy on the Zo workspace. Use whenever the user asks to fix, update, rebuild, restart, or patch qwen-gate (including BASE_PATH/reverse-proxy issues).
---

# Qwen Gate Maintenance

Maintain the qwen-gate OpenAI-compatible proxy for Qwen AI models.

## Scope
- Rebuild qwen-gate after source changes
- Restart the service cleanly
- Fix BASE_PATH / reverse-proxy dashboard URL rewriting
- Verify health and Hermes provider connectivity
- Update the supervisor config when the startup command changes
- Re-apply critical patches after `git pull` or fresh clone
- Understand tool calling behavior with `TOOL_CALLING=false`
- Safely add custom instructions without breaking core functionality

## Project layout
- Source: `/home/workspace/Projects/qwen-gate/`
- Supervisor config: `/etc/zo/supervisord-user.conf`
- Program name: `qwen-gate`
- Port: `26405`
- Health: `http://localhost:26405/health`

## Directory Contents (this skill)
- `references/` — Configs, supervisor blocks, and documentation
- `scripts/` — Executable helpers (rebuild, verify, apply-patches)
- `patches/` — .patch files for the two critical customizations

## Quick Rebuild + Restart (Normal Case)
1. `supervisorctl -c /etc/zo/supervisord-user.conf stop qwen-gate`
2. Kill stragglers if needed: `pkill -9 -f "bun src/index.tsx" || true`
3. `cd /home/workspace/Projects/qwen-gate && bun run build`
4. `supervisorctl -c /etc/zo/supervisord-user.conf start qwen-gate`
5. Wait ~8s then run `scripts/verify.sh`

## Full Recovery: "Pull repo and make it work again"

This is the procedure when you tell another model "pull the latest qwen-gate and implement the fixes":

```bash
cd /home/workspace/Projects/qwen-gate

# 1. Get latest code
git pull origin main

# 2. Reset config to known-good values (TOOL_CALLING=false is critical)
cp /home/workspace/Skills/qwen-gate-maintain/references/recommended-config.json config.json

# 3. Apply the two essential patches
/home/workspace/Skills/qwen-gate-maintain/scripts/apply-patches.sh

# 4. Install + build
bun install
bun run build

# 5. Update supervisor (copy the exact block)
#    See: references/supervisor-block.conf
#    Then:
supervisorctl -c /etc/zo/supervisord-user.conf reread
supervisorctl -c /etc/zo/supervisord-user.conf update

# 6. Restart cleanly
supervisorctl -c /etc/zo/supervisord-user.conf restart qwen-gate

# 7. Verify
/home/workspace/Skills/qwen-gate-maintain/scripts/verify.sh
```

## Tool Calling Behavior

**`TOOL_CALLING=false` does NOT disable tool calling.**

- It only prevents sending the massive structured `local_mcp` tool schemas to Qwen (which causes empty responses on the free tier).
- Tool lists are still sent as **plain text** in the system instructions.
- The model is instructed to call tools "in the appropriate format".
- Qwen outputs tool calls using its XML format (`<function=NAME><parameter>...</parameter></function>`).
- The gateway parses these XML calls and returns standard OpenAI `tool_calls` to Hermes.

Tool calling works normally from the caller's perspective.

See `references/critical-customizations.md` for the full explanation.

## Custom Instructions for Tools (Safe Way)

**Important**: Setting `USE_CUSTOM_INSTRUCTION=true` makes qwen-gate **replace** the entire default system prompt. The default prompt contains critical rules for reading tool results from `context.txt`.

You should **not** just paste tool instructions alone.

**Safe approach**:
Use the pre-merged file:

→ `references/safe-custom-instruction.txt`

This file contains the full original default prompt + additional tool calling format reinforcement.

**How to apply**:
1. Copy the instruction content from the file.
2. In the qwen-gate dashboard Settings, paste into **CUSTOM_INSTRUCTION**.
3. Enable **USE_CUSTOM_INSTRUCTION**.
4. Save and restart qwen-gate.
5. Test.

See `references/critical-customizations.md` for full details and warnings.

## References

- `references/supervisor-block.conf` — Exact supervisor program block
- `references/recommended-config.json` — Full config with TOOL_CALLING=false and safe defaults
- `references/critical-customizations.md` — Detailed explanation of patches + tool calling behavior + custom instructions guidance
- `references/safe-custom-instruction.txt` — Ready-to-use merged custom instruction that preserves core functionality
- `references/cookie-extraction.md` — Extracting Qwen session cookies from qwen-gate's Chromium browser profiles (for importing into OmniRoute "Qwen Web (Free)" or other tools that need raw cookie strings)

## Patches

- `patches/00-basepath-reverse-proxy.patch` — Makes dashboard work behind `/qwen` or any prefix
- `patches/01-tool-stripping-context-cap.patch` — Prevents Qwen free API from returning empty content on large tool lists or big context

## Scripts

- `scripts/rebuild.sh` — Full safe stop + build + start
- `scripts/verify.sh` — Health, models, Hermes test, and BASE_PATH check
- `scripts/apply-patches.sh` — Apply all patches from this skill

## Supervisor Command (current correct one)

```bash
command=bash -c 'cd /home/workspace/Projects/qwen-gate && bun src/index.tsx --host 0.0.0.0'
```

## Important Notes
- Dashboard static files live in `src/routes/dashboard/public/` (not dist).
- `bun run build` is required after patching.
- Always stop via supervisorctl — the service auto-restarts aggressively.
- The repo version string is often stale (still 0.7.0 on newer commits).
- These two patches + `TOOL_CALLING=false` are mandatory for stable Hermes + qwen3.7-plus usage with tools.
- For custom instructions, always use the merged version in `references/safe-custom-instruction.txt` instead of starting from scratch.