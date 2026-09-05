#!/usr/bin/env python3
"""Deterministic Hermes state.db repair (FTS corruption class).

Run standalone or imported by the watchdog. Stops gateway, disables FTS,
vacuums, syncs durable copy, restarts gateway.
"""
from __future__ import annotations

import os
import shutil
import signal
import sqlite3
import subprocess
import time
from pathlib import Path

SKILL_DIR = Path("/home/workspace/Skills/hermes-gateway/scripts")
DISABLE_FTS = SKILL_DIR / "disable-fts-permanent.py"
BOOT_SCRIPT = SKILL_DIR / "hermes-gateway-boot.sh"
SYNC_SCRIPT = SKILL_DIR / "sync-state-durable.sh"
LIVE = Path("/dev/shm/hermes/state.db")
DURABLE = Path("/root/.hermes/state.db.durable")


def _run(cmd: list[str], timeout: int = 600) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "HERMES_DISABLE_FTS": "1", "HERMES_DISABLE_FTS_TRIGRAM": "1"},
        )
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode == 0, out.strip()[-2000:]
    except Exception as e:
        return False, str(e)


def stop_gateway() -> bool:
    ok, _ = _run(["pkill", "-f", "hermes gateway run"], timeout=15)
    time.sleep(3)
    # pkill returns 1 if no process — still ok
    return True


def integrity_ok(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, "missing"
    try:
        con = sqlite3.connect(str(path), timeout=30)
        row = con.execute("PRAGMA integrity_check").fetchone()
        con.close()
        val = row[0] if row else "?"
        return val == "ok", val
    except Exception as e:
        return False, str(e)


def heal() -> dict:
    steps: list[str] = []
    errors: list[str] = []

    stop_gateway()
    steps.append("gateway stopped")

    if DISABLE_FTS.is_file():
        ok, out = _run(["python3", str(DISABLE_FTS)], timeout=900)
        steps.append("disable-fts-permanent.py")
        if not ok:
            errors.append(f"disable-fts failed: {out[:400]}")
    else:
        errors.append(f"missing {DISABLE_FTS}")

    live_ok, live_msg = integrity_ok(LIVE)
    dur_ok, dur_msg = integrity_ok(DURABLE)
    steps.append(f"integrity live={live_ok} durable={dur_ok}")

    if SYNC_SCRIPT.is_file():
        ok, out = _run(["bash", str(SYNC_SCRIPT)], timeout=120)
        steps.append("durable sync")
        if not ok:
            errors.append(f"sync failed: {out[:300]}")

    if BOOT_SCRIPT.is_file():
        # Boot script exec's gateway — run in background
        try:
            subprocess.Popen(
                ["bash", str(BOOT_SCRIPT)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                env={**os.environ, "HERMES_DISABLE_FTS": "1", "HERMES_DISABLE_FTS_TRIGRAM": "1"},
            )
            steps.append("gateway boot dispatched")
            time.sleep(8)
        except Exception as e:
            errors.append(f"boot failed: {e}")
    else:
        ok, out = _run(["hermes", "gateway", "run", "--replace"], timeout=30)
        steps.append("hermes gateway run --replace")

    live_ok2, live_msg2 = integrity_ok(LIVE)
    return {
        "ok": live_ok2 and not errors,
        "steps": steps,
        "errors": errors,
        "integrity_live": live_msg2,
        "integrity_durable": dur_msg,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(heal(), indent=2))
