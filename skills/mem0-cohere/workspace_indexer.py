"""
Workspace indexer for Mem0.
LLM: OpenCode Go free model (qwen/qwen3.6-plus-free) — $0 cost
Embeddings: Cohere free tier with 17-key rotation
"""
import os
import sys
from pathlib import Path

# Load credentials
env_path = Path("/home/workspace/credentials/master_keys.env")
cohere_keys = []
for line in env_path.read_text().splitlines():
    if line.startswith("COHERE_API_KEY_"):
        key = line.split("=", 1)[1].strip()
        cohere_keys.append(key)
    if line.startswith("OPENCODE_GO_API_KEY="):
        os.environ["OPENCODE_GO_API_KEY"] = line.split("=", 1)[1].strip()

print(f"Loaded {len(cohere_keys)} Cohere keys")

from embedder import CohereRotatingEmbeddings
from mem0 import Memory

embeddings = CohereRotatingEmbeddings(cohere_keys)

# Mem0 configuration — FREE MODELS ONLY
MEM0_CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333,
            "collection_name": "mem0_cohere",
            "embedding_model_dims": 1024,
        },
    },
    "llm": {
        "provider": "openai",
        "config": {
            "model": "qwen/qwen3.6-plus-free",
            "api_key": os.environ["OPENCODE_GO_API_KEY"],
            "base_url": "https://opencode.ai/zen/go/v1",
            "max_tokens": 500,
            "temperature": 0.1,
        },
    },
    "embedder": {
        "provider": "langchain",
        "config": {
            "model": embeddings,
            "model_kwargs": {"input_type": "search_document"},
        },
    },
}


def init_memory():
    """Initialize Mem0 with free model config"""
    return Memory.from_config(MEM0_CONFIG)


def index_workspace():
    """Index workspace documentation files"""
    memory = init_memory()
    
    workspace_files = [
        "/home/workspace/AGENTS.md",
        "/home/workspace/SOUL.md",
        "/home/workspace/memory.md",
        "/home/workspace/WORKSPACE_INDEX.md",
    ]
    
    print("Indexing workspace files...")
    for file_path in workspace_files:
        path = Path(file_path)
        if not path.exists():
            print(f"  Skipping {file_path} (not found)")
            continue
        
        print(f"  Processing {file_path}...")
        content = path.read_text()
        
        # Split into chunks (approx 1000 chars each)
        chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
        
        for i, chunk in enumerate(chunks):
            try:
                memory.add(chunk, user_id="workspace", metadata={"source": file_path, "chunk": i})
                print(f"    Added chunk {i+1}/{len(chunks)}")
            except Exception as e:
                print(f"    Error adding chunk {i+1}: {e}")
    
    print("Workspace indexing complete!")


def search_memory(query, user_id="workspace"):
    """Search indexed memories"""
    memory = init_memory()
    results = memory.search(query, filters={"user_id": user_id})
    return results


if __name__ == "__main__":
    index_workspace()
