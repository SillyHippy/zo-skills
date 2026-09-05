#!/bin/bash
# Vector search CLI
# Usage: ./search.sh "query text" [collection] [limit]

QUERY="${1:-}"
COLLECTION="${2:-documents}"
LIMIT="${3:-10}"

if [ -z "$QUERY" ]; then
  echo "Usage: $0 'search query' [collection] [limit]"
  echo "Collections: documents, cases, research"
  exit 1
fi

curl -s -X POST http://localhost:4400/search \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$QUERY\", \"collection\": \"$COLLECTION\", \"limit\": $LIMIT, \"threshold\": 0.3}" | jq .
