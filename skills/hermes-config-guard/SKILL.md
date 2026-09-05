---
name: hermes-config-guard
description: Fix Hermes /model picker clutter, duplicate providers, and excluded-provider leaks. Use when Telegram /model shows too many providers, duplicates, stepfun/google/gemini ghosts, or excluded providers still visible.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---

# Hermes Config Guard

Fixes recurring Hermes `/model` picker problems on Telegram and other gateways.

## One Command

```bash
# Audit first (read-only)
python3 /home/workspace/Skills/hermes-config-guard/scripts/audit_picker.py

# Fix + gateway restart
python3 /home/workspace/Skills/hermes-config-guard/scripts/fix_picker.py
```

Legacy shell wrappers still work:

```bash
bash /home/workspace/Skills/hermes-config-guard/scripts/backup.sh
bash /home/workspace/Skills/hermes-config-guard/scripts/validate.sh
bash /home/workspace/Skills/hermes-config-guard/scripts/fix.sh
```

## Root Cause (read this)

Hermes has **two** hide mechanisms — agents confuse them constantly:

| Mechanism | Config path | What it hides |
|-----------|-------------|---------------|
| **Picker exclusion** | `model_catalog.excluded_providers` | Built-in / auth-discovered providers only |
| **User provider off** | `providers.<name>.enabled: false` | Your manual `providers:` blocks |

**Critical:** If a provider exists under `providers:` in config.yaml, `excluded_providers` does **not** hide it. You must set `enabled: false` on that block.

Example — these are in `excluded_providers` but still show until disabled:

- `groq`, `mistral`, `deepseek`, `gemini`, `kilocode`, `opencode-go`
- `cerebras`, `modelscope`, `longcat`, `sakana`, `openai-api`

`fix_picker.py` auto-applies `enabled: false` to any user provider whose slug is in `excluded_providers`.

## Validation Checklist

### Config (`/root/.hermes/config.yaml`)
- [ ] No duplicate keys under `providers:`
- [ ] `model_catalog.excluded_providers` lists providers you never want in the picker
- [ ] Every excluded user provider has `enabled: false`
- [ ] `disable_auto_providers` has lowercase **and** Title Case pairs (legacy auto-discovery guard)
- [ ] Default model/provider matches intent (`free` / `oc/mimo-v2.5-free` for free tier)

### Auth (`/root/.hermes/auth.json`)
- [ ] No `stepfun` pool (causes ghost provider)
- [ ] No `custom:gemini`, `custom:gemini-1`, `custom:mistral`, `custom:clod`

### Picker code hygiene (`model_switch.py`)
Joe-local post-filter drops: `stepfun`, `google`, `custom:gemini*`, `opencode-zen*`
Aliases: `google` → `gemini`, `opencode-zen-go-custom` → `opencode-go`

### After any config change
Gateway must restart — running gateway reads stale config:

```bash
bash /home/workspace/Skills/hermes-gateway/scripts/hermes-gateway.sh restart
# or: supervisorctl restart hermes-gateway
```

## Expected Picker (~20 providers)

After fix, visible providers should be roughly:

- Mixture of Agents, free, 9router, kiro, gumloop, replit, command-code, cursor-sdk
- grok-9router, antigravity, nvidia-nim, mistral-9router, free-router, free-clod

Hidden (via exclusion + enabled:false): native groq/mistral/deepseek/gemini/kilocode/opencode-go, openrouter, copilot, nous, nvidia NIM auth row, etc.

## File Locations

| File | Path |
|------|------|
| Main config | `/root/.hermes/config.yaml` |
| Auth store | `/root/.hermes/auth.json` |
| Picker logic | `/usr/local/lib/hermes-agent/hermes_cli/model_switch.py` |
| Backups | `/home/workspace/Backups/hermes/` |

## When to Use

- `/model` shows 30+ providers / 4 pages on Telegram
- Provider in `excluded_providers` still visible
- stepfun, google, or duplicate gemini rows appear
- After editing providers or auth credentials
