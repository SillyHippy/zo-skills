#!/bin/bash
echo "=== Modal Configuration ==="
modal config show 2>&1
echo ""
echo "=== Token Verification ==="
# Check current profile token
modal dashboard 2>&1 | head -5
echo ""
echo "=== Hermes Gateway ==="
hermes gateway status 2>&1
