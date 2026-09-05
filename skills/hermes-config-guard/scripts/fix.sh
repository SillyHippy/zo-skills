#!/bin/bash
# Hermes Config Guard - Fix Script
# Automatically repairs common Hermes configuration issues

echo "=== Hermes Config Auto-Fix ==="
echo ""

# Create backup first
bash "$(dirname "$0")/backup.sh"
echo ""

# Fix 1: Remove bad credential pools from auth.json
echo "[1/3] Cleaning auth.json credential pools..."
python3 << 'PY'
import json
from pathlib import Path

p = Path('/root/.hermes/auth.json')
if not p.exists():
    print("  ! auth.json not found, skipping")
    exit(0)

data = json.loads(p.read_text())
pools = data.get('credential_pool', {})

remove = [
    'custom:gemini', 'custom:gemini-1', 'custom:gemini-2',
    'custom:opencode-zen-go-custom', 'stepfun',
    'custom:clod', 'custom:mistral', 'custom:google'
]

removed = []
for key in remove:
    if key in pools:
        del pools[key]
        removed.append(key)

if removed:
    p.write_text(json.dumps(data, indent=2))
    print(f"  ✓ Removed: {', '.join(removed)}")
else:
    print("  ✓ No bad pools found")
PY

# Fix 2: Deduplicate .env
echo ""
echo "[2/3] Deduplicating .env file..."
python3 << 'PY'
from pathlib import Path

p = Path('/root/.hermes/.env')
if not p.exists():
    print("  ! .env not found, skipping")
    exit(0)

lines = p.read_text().splitlines()
seen = set()
kept = []

for line in lines:
    if line.startswith('#') or not line.strip():
        kept.append(line)
        continue
    key = line.split('=')[0] if '=' in line else line
    if key in seen:
        continue
    seen.add(key)
    kept.append(line)

p.write_text('\n'.join(kept) + '\n')
print(f"  ✓ Deduplicated .env ({len(lines)} -> {len(kept)} lines)")
PY

# Fix 3: Restart Hermes
echo ""
echo "[3/3] Restarting Hermes gateway..."
bash /home/workspace/Skills/hermes-gateway/scripts/hermes-gateway.sh restart

echo ""
echo "=== Fix Complete ==="
echo "Run validate.sh to verify fixes."
