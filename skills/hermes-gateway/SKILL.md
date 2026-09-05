---
name: hermes-gateway
description: Control the Hermes AI Agent gateway — start, stop, restart, and status. Use when the user says "Hermes", "open claw", "turn on Hermes", "start Hermes", "stop Hermes", or asks about the Hermes agent.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---
# Hermes Gateway Control

## What is this?

Hermes is your AI agent. The gateway is the messaging service that connects Hermes to Telegram and other platforms. OpenClaw was the predecessor — "open claw" and "Hermes" refer to the same system.

## Commands

```bash
# Start Hermes gateway
bash /home/workspace/Skills/hermes-gateway/scripts/hermes-gateway.sh start

# Stop Hermes gateway
bash /home/workspace/Skills/hermes-gateway/scripts/hermes-gateway.sh stop

# Restart Hermes gateway
bash /home/workspace/Skills/hermes-gateway/scripts/hermes-gateway.sh restart

# Check status
bash /home/workspace/Skills/hermes-gateway/scripts/hermes-gateway.sh status

# Install as boot-time service (persists across reboots)
bash /home/workspace/Skills/hermes-gateway/scripts/hermes-gateway.sh install
```

## Auto-restart

A cron job runs every 5 minutes to check if Hermes is running and restarts it if stopped. See the automation in Zo.

## state.db watchdog auto-repair

Hermes cron job **state.db write watchdog** (`b022f0868071`, every 30m) runs
`/root/.hermes/scripts/hermes_state_db_watchdog.py` (source:
`Skills/hermes-gateway/scripts/state_db_watchdog.py`).

When corruption or write failure is detected:

1. **Deterministic heal** — `state-db-auto-heal.py` (stop gateway → `disable-fts-permanent.py` → durable sync → boot)
2. **Re-probe** — integrity_check + write round-trip
3. **If still broken** — dispatches Zo agent via `/zo/ask` using **Cursor Auto** (`byok:0862d95f-…`), fallback Antigravity Opus thinking. Agent gets full repair instructions and Telegrams Joe when done.
4. **Cooldown** — agent dispatch max once per 2h; alert spam max once per 6h while down

Manual repair:

```bash
python3 /home/workspace/Skills/hermes-gateway/scripts/disable-fts-permanent.py
bash /home/workspace/Skills/hermes-gateway/scripts/sync-state-durable.sh
bash /home/workspace/Skills/hermes-gateway/scripts/hermes-gateway-boot.sh
```

## Keywords

When the user says any of these, use this skill:
- "Hermes"
- "open claw" / "openclaw"
- "turn on Hermes" / "start Hermes" / "stop Hermes"
- "Hermes agent" / "hermes gateway"
