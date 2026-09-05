#!/usr/bin/env bash
#
# Apply all patches from this skill after a git pull or fresh clone.
# Run from inside the qwen-gate project directory.
#
set -euo pipefail

SKILL_DIR="/home/workspace/Skills/qwen-gate-maintain"
PATCH_DIR="$SKILL_DIR/patches"

if [ ! -d "$PATCH_DIR" ]; then
  echo "Patch directory not found: $PATCH_DIR"
  exit 1
fi

echo "Applying patches from $PATCH_DIR ..."

for patch in "$PATCH_DIR"/*.patch; do
  if [ -f "$patch" ]; then
    echo "→ $(basename "$patch")"
    git apply "$patch" || echo "   (patch may already be applied or conflict)"
  fi
done

echo "Done applying patches."
echo "Now run: bun install && bun run build"