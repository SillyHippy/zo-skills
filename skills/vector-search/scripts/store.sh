#!/bin/bash
# Store document in vector DB
# Usage: ./store.sh "text content" "source" [collection]

TEXT="${1:-}"
SOURCE="${2:-manual}"
COLLECTION="${3:-documents}"

if [ -z "$TEXT" ]; then
  echo "Usage: $0 'text content' 'source' [collection]"
  exit 1
fi

curl -s -X POST http://localhost:4400/store \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$TEXT\", \"source\": \"$SOURCE\", \"collection\": \"$COLLECTION\"}" | jq .
