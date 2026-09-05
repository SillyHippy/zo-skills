#!/usr/bin/env bash
# Boot Hermes with state.db on tmpfs (avoids 9p SQLite corruption).
set -euo pipefail

SHM_DIR=/dev/shm/hermes
LIVE=$SHM_DIR/state.db
DURABLE=/root/.hermes/state.db.durable
LINK=/root/.hermes/state.db

mkdir -p "$SHM_DIR"

# If tmpfs was wiped (reboot), restore durable snapshot into shm.
if [[ ! -f "$LIVE" ]]; then
  if [[ -f "$DURABLE" ]]; then
    echo "[hermes-boot] restoring durable state.db into tmpfs"
    cp -f "$DURABLE" "$LIVE"
  else
    echo "[hermes-boot] WARNING: no live or durable state.db" >&2
  fi
fi

# Ensure ~/.hermes/state.db is a symlink to tmpfs live DB.
if [[ -L "$LINK" ]]; then
  target=$(readlink -f "$LINK" || true)
  if [[ "$target" != "$LIVE" ]]; then
    rm -f "$LINK"
    ln -s "$LIVE" "$LINK"
  fi
elif [[ -e "$LINK" ]]; then
  # Accidental real file on 9p — move aside and relink.
  ts=$(date -u +%Y%m%d_%H%M%S)
  mv "$LINK" "/root/.hermes/state.db.9p-aside-$ts"
  rm -f "$LINK-wal" "$LINK-shm" 2>/dev/null || true
  ln -s "$LIVE" "$LINK"
else
  ln -s "$LIVE" "$LINK"
fi

# Drop stale 9p WAL sidecars that are NOT on the symlink target.
# (sqlite will create wal/shm next to the real file on tmpfs)
rm -f /root/.hermes/state.db-wal /root/.hermes/state.db-shm 2>/dev/null || true

export HERMES_DISABLE_FTS_TRIGRAM=1
export HERMES_DISABLE_FTS=1
export HERMES_CJK_FTS=0

# CRITICAL: Hermes venv Python ships SQLite 3.53.1 (WAL-reset fixed).
# System /usr/local/bin/python is SQLite 3.44.2 and corrupts state.db under concurrent chats.
HERMES_BIN=/usr/local/lib/hermes-agent/venv/bin/hermes
if [[ ! -x "$HERMES_BIN" ]]; then
  HERMES_BIN=/usr/local/bin/hermes
fi
exec "$HERMES_BIN" gateway run --replace
