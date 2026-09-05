#!/usr/bin/env bash
set -e

echo "=== Installing Zo Skills & MCP Tools ==="

# 1. Install zo-snapshot
echo "[1/3] Installing zo-snapshot..."
curl -sL https://raw.githubusercontent.com/SillyHippy/zo-skills/main/mcp-servers/zo-snapshot/zo-snapshot -o /usr/local/bin/zo-snapshot
chmod +x /usr/local/bin/zo-snapshot

# 2. Setup renewal hook
echo "[2/3] Setting up Zo VM renewal hook..."
mkdir -p /home/workspace/.zo/renewal-hooks.d
curl -sL https://raw.githubusercontent.com/SillyHippy/zo-skills/main/mcp-servers/zo-snapshot/zo-renewal-hook.py -o /home/workspace/.zo/renewal-hooks.d/01-zo-snapshot.py
chmod +x /home/workspace/.zo/renewal-hooks.d/01-zo-snapshot.py

# 3. Setup Hermes Skill
echo "[3/3] Setting up Hermes Skill..."
mkdir -p /root/.hermes/skills/zo-snapshot
curl -sL https://raw.githubusercontent.com/SillyHippy/zo-skills/main/skills/zo-snapshot.md -o /root/.hermes/skills/zo-snapshot/SKILL.md

echo "=== Installation Complete! ==="
echo "Run 'zo-snapshot list' or 'zo-snapshot create' to get started."
