#!/bin/bash
# Hermes Config Guard - Validation Script
# Checks for duplicate providers and configuration issues

echo "=== Hermes Config Validation ==="
echo ""

ERRORS=0

# Check 1: Config YAML duplicates
echo "[1/4] Checking config.yaml for duplicate providers..."
DUPS=$(grep -E "^  [a-z0-9-]+:" /root/.hermes/config.yaml | sort | uniq -d)
if [ -n "$DUPS" ]; then
    echo "  ✗ FAIL: Duplicate providers found:"
    echo "$DUPS" | sed 's/^/    /'
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ PASS: No duplicate providers in config.yaml"
fi

# Check 2: Specific provider rules
echo ""
echo "[2/4] Checking provider-specific rules..."

if grep -q "^  google:" /root/.hermes/config.yaml; then
    echo "  ✗ FAIL: 'google' provider found (should be 'gemini' only)"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ PASS: No 'google' provider (gemini only)"
fi

if grep -q "^  stepfun:" /root/.hermes/config.yaml; then
    echo "  ✗ FAIL: 'stepfun' provider found in config.yaml"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ PASS: No 'stepfun' provider in config.yaml"
fi

# Check 3: Auth JSON duplicates
echo ""
echo "[3/4] Checking auth.json for duplicate credential pools..."
BAD_POOLS=$(grep -E '"(custom:gemini|custom:gemini-1|custom:opencode-zen-go-custom|stepfun|custom:clod|custom:mistral)":' /root/.hermes/auth.json 2>/dev/null || true)
if [ -n "$BAD_POOLS" ]; then
    echo "  ✗ FAIL: Bad credential pools found:"
    echo "$BAD_POOLS" | sed 's/^/    /'
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ PASS: No bad credential pools in auth.json"
fi

# Check 4: Environment duplicates
echo ""
echo "[4/4] Checking .env for duplicate keys..."
DUP_KEYS=$(grep -E "^[A-Z_]+=" /root/.hermes/.env | cut -d= -f1 | sort | uniq -d)
if [ -n "$DUP_KEYS" ]; then
    echo "  ✗ FAIL: Duplicate env keys:"
    echo "$DUP_KEYS" | sed 's/^/    /'
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ PASS: No duplicate env keys"
fi

# Summary
echo ""
echo "=== Validation Summary ==="
if [ $ERRORS -eq 0 ]; then
    echo "✓ All checks passed!"
    exit 0
else
    echo "✗ $ERRORS issue(s) found. Run fix.sh to repair."
    exit 1
fi
