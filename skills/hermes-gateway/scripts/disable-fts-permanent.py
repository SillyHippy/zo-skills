#!/usr/bin/env python3
"""Permanently disable Hermes FTS5 on state.db (multi-chat corruption fix)."""
from __future__ import annotations

import os
import shutil
import sqlite3
import time
from pathlib import Path

DB = Path(os.environ.get("HERMES_HOME", "/root/.hermes")) / "state.db"
LIVE = Path("/dev/shm/hermes/state.db")
DURABLE = Path("/root/.hermes/state.db.durable")


def backup_db(path: Path) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    dest = path.parent / "backups" / f"state.db.pre-fts-disable-{ts}.bak"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    return dest


def disable_fts(path: Path) -> dict:
    con = sqlite3.connect(str(path), isolation_level=None)
    cur = con.cursor()
    cur.execute("PRAGMA busy_timeout=60000")

    for trigger in (
        "messages_fts_insert",
        "messages_fts_delete",
        "messages_fts_update",
        "messages_fts_trigram_insert",
        "messages_fts_trigram_delete",
        "messages_fts_trigram_update",
        "messages_fts_cjk_insert",
        "messages_fts_cjk_delete",
        "messages_fts_cjk_update",
    ):
        cur.execute(f"DROP TRIGGER IF EXISTS {trigger}")

    for obj in (
        "messages_fts_trigram",
        "messages_fts_cjk",
        "messages_fts",
        "messages_fts_trigram_src",
        "messages_fts_cjk_src",
    ):
        try:
            cur.execute(f"DROP TABLE IF EXISTS {obj}")
        except sqlite3.Error:
            pass

    cur.execute("PRAGMA writable_schema=ON")
    cur.execute("DELETE FROM sqlite_master WHERE name LIKE 'messages_fts%'")
    cur.execute("PRAGMA writable_schema=OFF")

    cur.execute(
        "INSERT INTO state_meta (key, value) VALUES ('fts_permanently_disabled', '1') "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value"
    )
    cur.execute(
        "INSERT INTO state_meta (key, value) VALUES ('fts_stale', '1') "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value"
    )
    cur.execute("DELETE FROM state_meta WHERE key IN ('fts_rebuild_high_water', 'fts_rebuild_progress')")

    messages = cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    sessions = cur.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

    cur.execute("VACUUM")
    con.close()

    con2 = sqlite3.connect(str(path))
    integrity = con2.execute("PRAGMA integrity_check").fetchone()[0]
    triggers = [
        r[0]
        for r in con2.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE '%fts%'"
        ).fetchall()
    ]
    con2.close()

    return {
        "path": str(path),
        "size_mb": round(path.stat().st_size / (1024 * 1024), 1),
        "messages": messages,
        "sessions": sessions,
        "integrity": integrity,
        "fts_triggers": triggers,
    }


def main() -> None:
    target = LIVE if LIVE.exists() else DB
    if not target.exists():
        raise SystemExit(f"No state.db at {target}")

    bak = backup_db(target)
    print(f"backup: {bak}")
    report = disable_fts(target)
    print(report)

    if DURABLE.exists() and DURABLE.resolve() != target.resolve():
        bak2 = backup_db(DURABLE)
        print(f"durable backup: {bak2}")
        disable_fts(DURABLE)
        print(f"durable size_mb: {round(DURABLE.stat().st_size / (1024 * 1024), 1)}")

    if report["integrity"] != "ok":
        raise SystemExit(f"integrity_check failed: {report['integrity']}")
    if report["fts_triggers"]:
        raise SystemExit(f"FTS triggers remain: {report['fts_triggers']}")


if __name__ == "__main__":
    main()
