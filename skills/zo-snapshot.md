---
name: zo-snapshot
description: Capture, compare, diff, and restore Zo Computer configuration and workspace snapshots word-for-word.
version: 1.0.0
metadata:
  hermes:
    tags: [zo, backup, snapshot, diff, rollback]
---

# zo-snapshot Skill

Use this skill whenever the user wants to take a checkpoint, inspect past system changes, diff configurations word-for-word, or roll back Zo Computer files safely.

## Core Commands

- **List snapshots:** `zo-snapshot list` (or `zo-snapshot list --json`)
- **Create snapshot:** `zo-snapshot create "Reason / label" --scope [config|workspace|all]`
- **Diff against live state:** `zo-snapshot diff <snapshot_id>`
- **Diff between two snapshots:** `zo-snapshot diff <snap_id_1> <snap_id_2>`
- **Restore / Rollback:** `zo-snapshot restore <snapshot_id> [--dry-run]`

## REST / MCP API

Daemon runs locally at `http://127.0.0.1:3090`:
- `GET /api/snapshots`
- `GET /api/snapshots/diff?from=<id>&to=current`
- `POST /api/snapshots` (`{"label": "...", "scope": "config"}`)
- `POST /mcp` (MCP JSON-RPC tools: `snapshot_list`, `snapshot_create`, `snapshot_diff`, `snapshot_restore`)
