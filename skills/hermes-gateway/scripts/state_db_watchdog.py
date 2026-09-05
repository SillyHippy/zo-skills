#!/usr/local/lib/hermes-agent/venv/bin/python3
"""Silent-when-healthy state.db write watchdog with auto-heal + Zo agent dispatch.

Catches btreeInitPage / SQLITE_CORRUPT / session storage failures.

Flow:
  1. integrity_check + write probe
  2. If unhealthy → deterministic auto-heal (disable FTS, vacuum, restart)
  3. Re-probe; if still broken → dispatch Zo agent (Cursor Auto / Antigravity)
  4. Alert on transition or 6h cooldown while still down

- Empty stdout + exit 0 = healthy (cron silent)
- Non-empty stdout = delivered to origin Telegram
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

DB = Path(os.environ.get("HERMES_HOME", "/root/.hermes")) / "state.db"
STATE_FILE = Path("/root/.hermes/cache/state_db_watchdog_state.json")
HEAL_SCRIPT = Path("/home/workspace/Skills/hermes-gateway/scripts/state-db-auto-heal.py")
DISPATCH_SCRIPT = Path(
    "/home/workspace/Skills/hermes-gateway/scripts/dispatch-state-db-repair-agent.py"
)
COOLDOWN_S = 6 * 3600


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"last_state": "up", "last_alert": 0}


def save_state(s: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s))


def integrity_check(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, "missing"
    try:
        con = sqlite3.connect(str(path), timeout=30)
        row = con.execute("PRAGMA integrity_check").fetchone()
        con.close()
        val = row[0] if row else "?"
        return val == "ok", val
    except sqlite3.Error as e:
        return False, str(e)


def write_probe() -> tuple[bool, str]:
    if not DB.is_file():
        return False, f"state.db MISSING: {DB}"

    sid = f"_watchdog_{time.time_ns()}"
    now = time.time()
    token = f"xyzzy{int(now)}"
    con = None
    try:
        con = sqlite3.connect(str(DB), timeout=15)
        cur = con.cursor()
        cur.execute("PRAGMA busy_timeout=10000")
        cur.execute(
            "INSERT INTO sessions (id, source, started_at) VALUES (?,?,?)",
            (sid, "_health_probe", now),
        )
        cur.execute(
            "INSERT INTO messages (session_id, role, content, timestamp) "
            "VALUES (?,?,?,?)",
            (sid, "user", token, now),
        )
        con.commit()
        got = cur.execute(
            "SELECT content FROM messages WHERE session_id=?", (sid,)
        ).fetchone()
        if not got or got[0] != token:
            return False, "write probe: insert did not round-trip"
        cur.execute("DELETE FROM messages WHERE session_id=?", (sid,))
        cur.execute("DELETE FROM sessions WHERE id=?", (sid,))
        con.commit()
        return True, ""
    except sqlite3.DatabaseError as e:
        return False, f"{type(e).__name__}: {e}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    finally:
        if con is not None:
            try:
                con.execute("DELETE FROM messages WHERE session_id=?", (sid,))
                con.execute("DELETE FROM sessions WHERE id=?", (sid,))
                con.commit()
            except Exception:
                pass
            try:
                con.close()
            except Exception:
                pass


def check_health() -> tuple[bool, list[str]]:
    problems: list[str] = []
    live = Path("/dev/shm/hermes/state.db")
    target = live if live.is_file() else DB

    ok, msg = integrity_check(target)
    if not ok:
        problems.append(f"integrity_check failed: {msg}")

    ok2, msg2 = write_probe()
    if not ok2:
        problems.append(f"write probe failed: {msg2}")

    return not problems, problems


def run_auto_heal() -> tuple[bool, str]:
    if not HEAL_SCRIPT.is_file():
        return False, "heal script missing"
    try:
        r = subprocess.run(
            ["python3", str(HEAL_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=900,
        )
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode != 0:
            return False, out[-800:]
        try:
            data = json.loads(r.stdout)
            return bool(data.get("ok")), json.dumps(data, indent=0)[:600]
        except json.JSONDecodeError:
            return r.returncode == 0, out[-400:]
    except Exception as e:
        return False, str(e)


def dispatch_repair_agent(detail: str) -> str:
    if not DISPATCH_SCRIPT.is_file():
        return "repair agent script missing"
    try:
        r = subprocess.run(
            ["python3", str(DISPATCH_SCRIPT), detail],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return (r.stdout or r.stderr or "").strip()
    except Exception as e:
        return f"dispatch failed: {e}"


def main() -> int:
    now = time.time()
    state = load_state()

    healthy, problems = check_health()

    if healthy:
        if state.get("last_state") == "down":
            save_state({"last_state": "up", "last_alert": 0})
            print("✅ state.db recovered — integrity + write probe healthy.")
        else:
            save_state({"last_state": "up", "last_alert": 0})
        return 0

    detail = "; ".join(problems)
    healed_lines: list[str] = []

    # Attempt deterministic heal
    heal_ok, heal_report = run_auto_heal()
    if heal_ok:
        healed_lines.append("deterministic auto-heal succeeded")
    else:
        healed_lines.append(f"auto-heal attempted: {heal_report[:300]}")

    time.sleep(5)
    healthy2, problems2 = check_health()

    if healthy2:
        save_state({"last_state": "down", "last_alert": now})
        msg = ["🟡 state.db AUTO-HEALED"]
        msg.append("· " + "\n· ".join(healed_lines))
        print("\n".join(msg))
        return 0

    # Still broken — dispatch capable Zo agent (background)
    agent_msg = dispatch_repair_agent(detail)
    if agent_msg:
        healed_lines.append(agent_msg)

    last_state = state.get("last_state")
    last_alert = state.get("last_alert", 0)
    should_alert = (last_state == "up") or (now - last_alert > COOLDOWN_S)

    if should_alert:
        save_state({"last_state": "down", "last_alert": now})
        msg = ["🚨 state.db DOWN — auto-fix in progress"]
        msg.append("· " + "\n· ".join(problems2 or problems))
        if healed_lines:
            msg.append("actions: " + " | ".join(healed_lines))
        print("\n".join(msg))
    else:
        save_state({"last_state": "down", "last_alert": last_alert})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
