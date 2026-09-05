#!/usr/bin/env bash
# Snapshot live tmpfs Hermes state.db to durable 9p path.
set -euo pipefail
LIVE=/dev/shm/hermes/state.db
DURABLE=/root/.hermes/state.db.durable
TMP=${DURABLE}.tmp.$$
if [[ ! -f "$LIVE" ]]; then
  echo "no live db" >&2
  exit 0
fi
# Online backup via sqlite API (safe with concurrent readers/writers)
# MUST use Hermes venv Python (SQLite 3.53.1) to prevent 9p WAL corruption
/usr/local/lib/hermes-agent/venv/bin/python3 - <<'PY'
import sqlite3, shutil, os
live="/dev/shm/hermes/state.db"
durable="/root/.hermes/state.db.durable"
tmp=durable+".tmp"
if os.path.exists(tmp):
    os.unlink(tmp)
src=sqlite3.connect(live, timeout=60)
src.execute("PRAGMA busy_timeout=60000")
dst=sqlite3.connect(tmp)
src.backup(dst)
dst.close()
src.close()
os.replace(tmp, durable)
print("durable ok", os.path.getsize(durable))
PY
