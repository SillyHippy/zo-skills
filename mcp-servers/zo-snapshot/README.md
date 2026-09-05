# zo-snapshot

> **Instant, differential, word-for-word snapshot & comparison engine for Zo Computer & autonomous AI agents.**

`zo-snapshot` provides atomic file tree checkpoints, unified word-for-word diffs (identical to GitHub PR diffs), safe rollbacks, and automatic hooks for Zo Computer VM renewals.

Zero external dependencies — pure Python 3.12 stdlib.

---

## Features

- **Hardlink Copy-on-Write (COW):** Creates point-in-time snapshots in `< 100ms` with near-zero disk usage.
- **Word-for-Word Diffs:** Exact unified diffs (`+` added, `-` deleted, `~` modified) matching standard `git diff`.
- **Automatic Zo Renewal Integration:** Hooks into Zo Computer's native `renewal_handoff.py` lifecycle (`/home/workspace/.zo/renewal-hooks.d/`) to automatically take a snapshot every time Zo renews or prepares a VM snapshot.
- **Dual Access Interface:**
  - **CLI:** Fast, human-readable terminal commands with `--json` support.
  - **Local REST API (`127.0.0.1:3090`):** Queryable by local apps, scripts, or proxies.
  - **Native MCP Server (`127.0.0.1:3090/mcp`):** Standard Model Context Protocol for Zo AI, Hermes Agent, Cursor, Replit, or OpenHands.
- **Safe Rollback:** Automatically generates a safety checkpoint before applying any restore.

---

## Quick Install on Zo Computer

```bash
# 1. Download and install binary
curl -sL https://raw.githubusercontent.com/SillyHippy/zo-snapshot/main/zo-snapshot -o /usr/local/bin/zo-snapshot
chmod +x /usr/local/bin/zo-snapshot

# 2. Enable automatic VM snapshot & renewal hook
mkdir -p /home/workspace/.zo/renewal-hooks.d
curl -sL https://raw.githubusercontent.com/SillyHippy/zo-snapshot/main/zo-renewal-hook.py -o /home/workspace/.zo/renewal-hooks.d/01-zo-snapshot.py
chmod +x /home/workspace/.zo/renewal-hooks.d/01-zo-snapshot.py

# 3. (Optional) Run background REST / MCP daemon under supervisor
cat << 'EOF' >> /etc/zo/supervisord-user.conf

[program:zo-snapshot]
command=/usr/local/bin/zo-snapshot serve --port 3090
autostart=true
autorestart=true
stderr_logfile=/var/log/zo-snapshot.err.log
stdout_logfile=/var/log/zo-snapshot.out.log
EOF
supervisorctl -c /etc/zo/supervisord-user.conf reread
supervisorctl -c /etc/zo/supervisord-user.conf update
```

---

## CLI Usage

### 1. Create a Snapshot
```bash
# Default config scope (/root/.hermes, /etc/zo, .env, .zo_secrets)
zo-snapshot create "Before testing model switch"

# Full workspace scope
zo-snapshot create "Before big refactor" --scope workspace
```

### 2. List All Snapshots
```bash
zo-snapshot list
```
```
ID                               CREATED              SCOPE      FILES    LABEL
------------------------------------------------------------------------------------------
snap_20260905_015912_01f6ea      2026-09-05 01:59:12  config     3452     Auto-Snapshot before Zo VM Renewal
snap_20260905_014440_d2b5d9      2026-09-05 01:44:40  config     3451     Baseline Test Snapshot
```

### 3. Compare / Diff Word-for-Word
```bash
# Compare a snapshot against live current state
zo-snapshot diff snap_20260905_014440_d2b5d9

# Compare two past snapshots
zo-snapshot diff snap_20260905_014440_d2b5d9 snap_20260905_015912_01f6ea

# Output machine-readable JSON for AI models
zo-snapshot diff snap_20260905_014440_d2b5d9 --json
```

Sample Diff Output:
```diff
Comparing: snap_20260905_014440_d2b5d9 ➔ current_live
Summary: +0 added, ~1 modified, -0 deleted, 3450 unchanged

Modified files:
  ~ /etc/zo/supervisord-user.conf

============================================================ UNIFIED DIFFS ============================================================

--- /etc/zo/supervisord-user.conf ---
--- a//etc/zo/supervisord-user.conf (snap_20260905_014440_d2b5d9)
+++ b//etc/zo/supervisord-user.conf (live)
@@ -45,3 +45,10 @@
 [program:custom-service]
-port=3000
+port=8080
```

### 4. Restore / Rollback
```bash
# Preview what would change without modifying files
zo-snapshot restore snap_20260905_014440_d2b5d9 --dry-run

# Apply restore (auto-creates a safety checkpoint first)
zo-snapshot restore snap_20260905_014440_d2b5d9
```

---

## MCP Server Integration

When running as a daemon on `:3090`, `zo-snapshot` provides native JSON-RPC 2.0 MCP tools at `http://127.0.0.1:3090/mcp`:

- `snapshot_list`: List all snapshots with metadata.
- `snapshot_create`: Create a snapshot with custom label and scope.
- `snapshot_diff`: Generate structured and unified diffs.
- `snapshot_restore`: Revert files to a previous snapshot state.

---

## License
MIT
