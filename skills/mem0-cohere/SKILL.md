---
name: mem0-cohere
description: Mem0 persistent memory with Cohere embeddings (17-key rotation) + Qdrant server
triggers:
  - "save to mem0"
  - "mem0 memory"
  - "search memories"
  - "add memory"
  - "persistent memory"
  - "agent memory"
  - "cross-session memory"
---

# Mem0 + Cohere Memory System

Persistent agent memory using Mem0 with Cohere embeddings (17-key rotation) and Qdrant vector database.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Mem0 OSS (self-hosted)                                     │
├─────────────────────────────────────────────────────────────┤
│  Embeddings: Cohere embed-english-v3.0 (1024 dims)         │
│    - 17 API keys with rotation (COHERE_API_KEY_1..17)      │
│    - Free tier: 1,000 req/month per key = 17,000 total     │
│                                                             │
│  LLM: Groq llama-3.3-70b-versatile (3 keys rotating)       │
│    - Used for fact extraction from text                    │
│                                                             │
│  Vector Store: Qdrant server (localhost:6333)              │
│    - Managed by Zo Computer (dumb-init supervisor)         │
│    - Collections: mem0_cohere, mem0migrations              │
│    - Data path: /home/workspace/Projects/data/qdrant       │
│                                                             │
│  Config: /root/.hermes/mem0.json                           │
└─────────────────────────────────────────────────────────────┘
```

## Key Facts

- **Qdrant runs as a server** (not file-based) — enables concurrent access from multiple Hermes sessions
- **No systemd** — Zo Computer uses dumb-init (PID 1) for process supervision
- **17 Cohere keys** rotate automatically to avoid rate limits
- **Free tier only** — no paid API credits used for embeddings
- **Groq LLM** for fact extraction (3 keys rotating)
- **user_id**: `"workspace"` (not "joseph") — all existing data uses this ID

## Collections

| Collection | Purpose |
|------------|---------|
| `mem0_cohere` | Main memory storage (144 points) |
| `mem0migrations` | Migration tracking |
| `workspace_files` | Semantic search over workspace (9,765 points) |
| `cases` | Legal case data |
| `documents` | Document embeddings |
| `research` | Research data |
| `wiki` | Wiki/knowledge base |

## Usage

### Via Hermes Plugin (Recommended)

The mem0 plugin at `/root/.hermes/plugins/mem0/` provides:
- `mem0_add(content)` — Store a memory
- `mem0_search(query)` — Search memories
- `mem0_list()` — List all memories
- `mem0_update(memory_id, text)` — Update a memory
- `mem0_delete(memory_id)` — Delete a memory

### Via Python Scripts

```python
# Load credentials
from pathlib import Path
env_path = Path("/home/workspace/credentials/master_keys.env")

# Initialize with rotating embeddings
from embedder import CohereRotatingEmbeddings
cohere_keys = [load from master_keys.env]
embeddings = CohereRotatingEmbeddings(cohere_keys)

# Mem0 config
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333,
            "collection_name": "mem0_cohere",
            "embedding_model_dims": 1024,
        }
    },
    "embedder": {
        "provider": "langchain",
        "config": {"model": embeddings}
    },
    "llm": {
        "provider": "openai",
        "config": {
            "model": "groq-rotating",
            "groq_model": "llama-3.3-70b-versatile"
        }
    }
}

from mem0 import Memory
m = Memory.from_config(config)
m.add("fact to remember", user_id="joseph")
```

## Files

| File | Purpose |
|------|---------|
| `embedder.py` | CohereRotatingEmbeddings class |
| `setup_mem0.py` | Test setup with 17-key rotation |
| `workspace_indexer.py` | Index workspace files into mem0 |
| `test_mem0.py` | Test script (outdated — uses DeepSeek) |
| `config_free.py` | Free-tier config constants |

## Important Notes

### Data Structure Mismatch

The existing data in Qdrant was written by `workspace_indexer.py` directly to Qdrant, not through mem0's API. This means:

- **Payload structure**: Uses `data` field instead of `memory` field
- **mem0 API compatibility**: `get_all()` and `search()` may return empty results because mem0 expects a different payload format
- **Direct Qdrant access**: Data IS accessible via Qdrant's API directly (see Troubleshooting section)
- **Future writes**: Use `mem0_add` tool or mem0's `add()` method for proper mem0-compatible payloads

### Two Use Cases

1. **Workspace semantic search** (existing data): Use `workspace_indexer.py` to index workspace files, query via Qdrant API directly
2. **Agent memory** (new data): Use `mem0_add`/`mem0_search` tools for Hermes agent memory with proper mem0 format

### Qdrant File Lock Error
**Problem**: `File lock already acquired` when multiple sessions try to access mem0

**Solution**: Qdrant is now running as a server (not file-based). All sessions connect via HTTP to localhost:6333. No file locks.

### Rate Limit Errors
**Problem**: Cohere API rate limit (429)

**Solution**: The embedder automatically rotates through 17 keys. If all are exhausted, wait 1 minute and retry.

### Mem0 Plugin Not Loading
**Problem**: `Mem0Backend() takes no arguments` error

**Solution**: The plugin uses a factory pattern. Don't instantiate `Mem0Backend` directly — use the plugin's initialization flow via Hermes.

## Qdrant Server Management

Qdrant runs as a **supervisord-managed service** on Zo Computer.

**Configuration:**
- **Binary**: `/usr/local/bin/qdrant`
- **Config**: `/home/workspace/Projects/data/qdrant/qdrant_config.yaml`
- **Data**: `/home/workspace/Projects/data/qdrant/`
- **Ports**: 6333 (HTTP), 6334 (gRPC)
- **Supervisor config**: `/etc/zo/supervisord-user.conf`
- **Logs**: `/dev/shm/qdrant.log` and `/dev/shm/qdrant_err.log`

**Management commands:**
```bash
# Check status
supervisorctl -c /etc/zo/supervisord-user.conf status qdrant

# Restart
supervisorctl -c /etc/zo/supervisord-user.conf restart qdrant

# Stop/Start
supervisorctl -c /etc/zo/supervisord-user.conf stop qdrant
supervisorctl -c /etc/zo/supervisord-user.conf start qdrant

# View logs
tail -f /dev/shm/qdrant.log
tail -f /dev/shm/qdrant_err.log
```

**Verify Qdrant is running:**
```bash
curl http://localhost:6333/collections
```

**Auto-restart**: Qdrant is configured with `autorestart=true` — if it crashes, supervisord automatically restarts it.

## Migration History

- **Before**: File-based Qdrant at `/root/.hermes/mem0_qdrant` — caused concurrent access errors
- **After**: Server-based Qdrant at localhost:6333 — enables multiple Hermes sessions
- **Migration date**: June 25, 2026
- **Points migrated**: 144 (mem0_cohere collection)

## Cost

- **Embeddings**: $0 (Cohere free tier, 17 keys)
- **LLM**: $0 (Groq free tier, 3 keys)
- **Vector DB**: $0 (self-hosted Qdrant)
- **Total**: $0/month for persistent memory
