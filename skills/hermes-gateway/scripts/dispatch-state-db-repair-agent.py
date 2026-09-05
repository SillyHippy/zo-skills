#!/usr/bin/env python3
"""Dispatch Zo agent to repair Hermes state.db (capable model).

Called by the watchdog when deterministic auto-heal fails.
Fires /zo/ask in background so the cron script returns immediately.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

STATE_FILE = Path("/root/.hermes/cache/state_db_repair_agent_state.json")
ZO_API = "https://api.zo.computer/zo/ask"
SECRETS = Path("/root/.zo_secrets")

# Capable models — try Cursor Auto first, then Antigravity Opus thinking
MODELS = [
    "byok:0862d95f-2ee5-515d-a31d-8c0b46401519",  # Cursor Auto
    "byok:5097f60c-d863-508b-a831-b2635d43b088",  # Antigravity claude-opus-4-6-thinking
]
COOLDOWN_S = 2 * 3600  # max one agent dispatch per 2h


def load_token() -> str:
    tok = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN", "")
    if tok:
        return tok
    if SECRETS.is_file():
        for line in SECRETS.read_text().splitlines():
            line = line.strip()
            if line.startswith("export ZO_CLIENT_IDENTITY_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"last_dispatch": 0}


def save_state(s: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s))


def build_prompt(error_detail: str) -> str:
    return f"""HERMES STATE.DB AUTO-REPAIR (cron watchdog triggered this).

The state.db write watchdog detected corruption or write failure:
{error_detail}

You MUST fix Hermes state.db completely. Follow this exact order:

1. Read /home/workspace/Skills/hermes-gateway/SKILL.md and AGENTS.md.
2. Full backup first: copy /dev/shm/hermes/state.db to /root/.hermes/backups/state.db.watchdog-$(date +%Y%m%d_%H%M%S).bak
3. Stop gateway: pkill -f "hermes gateway run"; sleep 3
4. Run: python3 /home/workspace/Skills/hermes-gateway/scripts/disable-fts-permanent.py
5. Verify: sqlite3 /dev/shm/hermes/state.db "PRAGMA integrity_check;" must return ok
6. Run: bash /home/workspace/Skills/hermes-gateway/scripts/sync-state-durable.sh
7. Restart: bash /home/workspace/Skills/hermes-gateway/scripts/hermes-gateway-boot.sh (background)
8. Wait 10s, verify gateway running and integrity ok
9. Run the watchdog probe: python3 /root/.hermes/scripts/hermes_state_db_watchdog.py (must be silent = healthy)

ENSURE HERMES_DISABLE_FTS=1 in /root/.hermes/.env and supervisord env.

Send Joe a Telegram message (send_telegram_message) with:
- What was wrong
- What you did
- Final integrity_check result and message count
- Whether watchdog is now silent

Do NOT use Resend. Do NOT guess — verify every step.
Give realistic time estimates only if you mention timing.
This is production — Joe's Hermes gateway must work when you're done."""


def dispatch_async(prompt: str, model: str, token: str) -> bool:
    """Spawn background curl so parent returns immediately."""
    body = json.dumps({"input": prompt, "model_name": model})
    payload_path = Path(f"/tmp/state_db_repair_zo_{int(time.time())}.json")
    payload_path.write_text(body)

    cmd = [
        "curl", "-sS", "-m", "1800",
        "-X", "POST", ZO_API,
        "-H", f"Authorization: {token}",
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/json",
        "-d", f"@{payload_path}",
        "-o", f"/root/.hermes/cache/state_db_repair_agent_last.json",
    ]
    log = open("/root/.hermes/cache/state_db_repair_agent_dispatch.log", "a")
    subprocess.Popen(cmd, stdout=log, stderr=log, start_new_session=True)
    return True


def main() -> int:
    error_detail = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "state.db write/integrity failure"
    state = load_state()
    now = time.time()

    if now - state.get("last_dispatch", 0) < COOLDOWN_S:
        print(f"ℹ️ Repair agent cooldown active ({int(COOLDOWN_S - (now - state['last_dispatch']))}s left)")
        return 0

    token = load_token()
    if not token:
        print("⚠️ Cannot dispatch repair agent: ZO_CLIENT_IDENTITY_TOKEN missing")
        return 1

    prompt = build_prompt(error_detail)
    model = MODELS[0]
    dispatch_async(prompt, model, token)
    save_state({"last_dispatch": now, "model": model, "error": error_detail[:500]})
    print(f"🔧 Auto-repair agent dispatched (model: Cursor Auto). Results via Telegram when done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
