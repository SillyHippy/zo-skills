#!/usr/bin/env python3
"""
Mem0 + Cohere setup with 17 API keys rotation
Uses all COHERE_API_KEY_1 through COHERE_API_KEY_17 from master_keys.env
"""
import os
import sys
from pathlib import Path
from mem0 import Memory
from langchain_core.embeddings import Embeddings
import cohere

# Load all 17 Cohere keys from master_keys.env
env_path = Path("/home/workspace/credentials/master_keys.env")
with open(env_path) as f:
    for line in f:
        if line.startswith('COHERE_API_KEY_'):
            key, val = line.strip().split('=', 1)
            os.environ[key] = val

# Collect all 17 keys
cohere_keys = []
for i in range(1, 18):
    key = os.environ.get(f'COHERE_API_KEY_{i}')
    if key:
        cohere_keys.append(key)

if len(cohere_keys) != 17:
    print(f"Warning: Found {len(cohere_keys)} keys, expected 17")

print(f"Loaded {len(cohere_keys)} Cohere API keys with rotation")

# Custom embeddings class with key rotation
class CohereRotatingEmbeddings(Embeddings):
    def __init__(self, keys, model="embed-english-v3.0"):
        self.keys = keys
        self.model = model
        self.current_key_idx = 0
    
    def _get_client(self):
        key = self.keys[self.current_key_idx]
        return cohere.ClientV2(api_key=key)
    
    def _rotate_key(self):
        self.current_key_idx = (self.current_key_idx + 1) % len(self.keys)
    
    def _embed_with_rotation(self, texts, input_type):
        """Embed with automatic key rotation on failure."""
        # Try each key up to 17 times
        for attempt in range(len(self.keys)):
            client = self._get_client()
            try:
                response = client.embed(
                    texts=texts,
                    model=self.model,
                    input_type=input_type
                )
                return response.embeddings.float  # Correct path for Cohere v2
            except cohere.errors.TooManyRequestsError:
                # Rate limit hit, rotate to next key
                print(f"Key {self.current_key_idx + 1} rate limited, rotating...")
                self._rotate_key()
                continue
            except Exception as e:
                # Other error, rotate and retry
                print(f"Key {self.current_key_idx + 1} failed: {e}, rotating...")
                self._rotate_key()
                continue
        
        raise RuntimeError("All 17 Cohere keys exhausted - all rate limited or failed")
    
    def embed_documents(self, texts):
        """Embed a list of documents."""
        return self._embed_with_rotation(texts, "search_document")
    
    def embed_query(self, text):
        """Embed a single query."""
        embeddings = self._embed_with_rotation([text], "search_query")
        return embeddings[0]

# Create the custom embeddings instance
embeddings = CohereRotatingEmbeddings(cohere_keys)

# Mem0 config with LangChain embedder
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
            "model": embeddings,  # Pass the custom embeddings instance
        }
    },
    "version": "v1.1"
}

print("Initializing Mem0 with 17 Cohere keys + rotation...")
m = Memory.from_config(config)
print("✓ Mem0 initialized successfully with Cohere rotation")

# Test
print("\nTesting memory storage...")
m.add("The user's name is Joe", user_id="test_user")
print("✓ Memory added")

print("\nTesting memory retrieval...")
results = m.search("What is the user's name?", filters={"user_id": "test_user"})
print(f"✓ Found {len(results.get('results', []))} results")

print("\n✓✓✓ All systems operational!")
