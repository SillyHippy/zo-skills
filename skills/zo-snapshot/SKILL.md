---
name: zo-snapshot
description: Snapshot, diff word-for-word, and restore Zo files.
version: 1.0.0
metadata:
  hermes:
    tags: [zo, backup, snapshot, diff, rollback]
---

# zo-snapshot Skill

Use this skill whenever you or the user need to take a checkpoint, compare changes word-for-word, or roll back Zo Computer configuration and workspace files.

## CLI Usage

- `zo-snapshot list` — List all snapshots with timestamps and labels.
- `zo-snapshot create "label" --scope [config|workspace|all]` — Create atomic checkpoint.
- `zo-snapshot diff <id> [id2]` — Word-for-word unified diff matching GitHub/git diffs.
- `zo-snapshot restore <id> [--dry-run]` — Revert files with automatic safety backup.

## API & MCP Server

Runs locally at `http://127.0.0.1:3090` (`/api/snapshots`, `/api/snapshots/diff`, `/mcp`).
