"""
Mem0 embedder using Cohere API keys with rotation.
Uses all 17 COHERE_API_KEY_* keys from credentials.
"""
from langchain_core.embeddings import Embeddings
import os
import time

try:
    from cohere import Client
except ImportError:
    raise ImportError("cohere package is not installed. Run: pip install cohere")


class CohereRotatingEmbeddings(Embeddings):
    """Cohere embeddings with API key rotation to avoid rate limits."""
    
    def __init__(self, keys, model="embed-english-v3.0"):
        self.keys = keys
        self.model = model
        self.current_key_idx = 0
        self.embedding_dims = 1024
    
    def _get_client(self):
        key = self.keys[self.current_key_idx]
        return Client(api_key=key)
    
    def _rotate_key(self):
        self.current_key_idx = (self.current_key_idx + 1) % len(self.keys)
    
    def embed_documents(self, texts):
        """Embed a list of documents with rotation."""
        embeddings = []
        for text in texts:
            embeddings.append(self.embed_query(text))
        return embeddings
    
    def embed_query(self, text):
        """Embed a single query with automatic key rotation on rate limit."""
        for attempt in range(len(self.keys)):
            client = self._get_client()
            try:
                response = client.embed(
                    texts=[text],
                    model=self.model,
                    input_type="search_query"
                )
                return response.embeddings[0]
            except Exception as e:
                if "rate limit" in str(e).lower() or "429" in str(e):
                    print(f"Rate limited on key {self.current_key_idx + 1}, rotating...")
                    self._rotate_key()
                    time.sleep(1)
                    continue
                raise
        
        raise RuntimeError("All Cohere API keys exhausted due to rate limiting")
