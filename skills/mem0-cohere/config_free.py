"""Mem0 config using FREE tiers only - OpenCode Go + Cohere free tier"""

# OpenCode Go free model (no cost)
FREE_MODEL = "qwen/qwen3.6-plus-free"

# Use Cohere free tier for embeddings (1,000 req/month per key, 17 keys = 17,000 free)
USE_FREE_COHERE = True

# NO DeepSeek, NO paid models
