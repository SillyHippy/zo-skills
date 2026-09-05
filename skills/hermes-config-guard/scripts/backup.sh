#!/bin/bash
# Hermes Config Guard - Backup Script
# Creates timestamped backups of all Hermes config files

set -e

BACKUP_DIR="/home/workspace/Backups/hermes"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup config.yaml
if [ -f /root/.hermes/config.yaml ]; then
    cp /root/.hermes/config.yaml "$BACKUP_DIR/config.yaml.$TIMESTAMP"
    echo "✓ config.yaml backed up"
fi

# Backup auth.json
if [ -f /root/.hermes/auth.json ]; then
    cp /root/.hermes/auth.json "$BACKUP_DIR/auth.json.$TIMESTAMP"
    echo "✓ auth.json backed up"
fi

# Backup .env
if [ -f /root/.hermes/.env ]; then
    cp /root/.hermes/.env "$BACKUP_DIR/env.$TIMESTAMP"
    echo "✓ .env backed up"
fi

echo ""
echo "Backups stored in: $BACKUP_DIR"
