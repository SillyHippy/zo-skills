"""
Mem0 setup with Cohere API key rotation via LangChain.
Uses all 17 Cohere API keys with rotation to avoid rate limits.
Uses DeepSeek for fact extraction.
"""
import os
import sys
from pathlib import Path

# Load Cohere API keys from credentials
env_path = Path("/home/workspace/credentials/master_keys.env")
cohere_keys = []
for line in env_path.read_text().splitlines():
    if line.startswith("COHERE_API_KEY_"):
        key = line.split("=", 1)[1].strip()
        cohere_keys.append(key)

print(f"Loaded {len(cohere_keys)} Cohere API keys")

from embedder import CohereRotatingEmbeddings
from mem0 import Memory

# Create Cohere embeddings with rotation
embeddings = CohereRotatingEmbeddings(cohere_keys)

# Mem0 config with Cohere embeddings and DeepSeek for fact extraction
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "mem0_cohere",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 1024,
        }
    },
    "embedder": {
        "provider": "langchain",
        "config": {
            "model": embeddings,
        }
    },
    "llm": {
        "provider": "deepseek",
        "config": {
            "model": "deepseek-chat",
            "api_key": "sk-23019c73149d454b81aafecc9d491a14",
            "temperature": 0.1,
            "max_tokens": 2000,
        }
    }
}

print("Initializing Mem0 with Cohere + DeepSeek...")
memory = Memory.from_config(config)
print("✓ Mem0 ready with 17-key Cohere rotation")

# Test
print("\nTesting memory storage...")
memory.add("The user's name is Joe and he lives in Tulsa, Oklahoma.", user_id="joe")
print("✓ Memory added")

print("\nSearching for memories...")
results = memory.search("Where does Joe live?", filters={"user_id": "joe"})
print(f"✓ Found {len(results.get('results', []))} results")
for r in results.get("results", []):
    print(f"  - {r.get('memory', 'N/A')}")

print("\n✓✓✓ All systems operational!")
