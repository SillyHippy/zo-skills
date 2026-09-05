#!/usr/bin/env python3
"""Test GLM-5.1 endpoint connectivity on Modal."""
import os
import requests

BASE_URL = os.environ.get("MODAL_GLM_BASE_URL", "https://api.us-west-2.modal.direct/v1")
API_KEY = os.environ.get("MODAL_GLM_API_KEY", "")
MODEL = os.environ.get("MODAL_GLM_MODEL", "zai-org/GLM-5.1-FP8")

if not API_KEY:
    print("ERROR: Set MODAL_GLM_API_KEY env var with your GLM-5 endpoint token.")
    print("Get one at: https://modal.com/glm-5-endpoint")
    exit(1)

print(f"Testing endpoint: {BASE_URL}")
print(f"Model: {MODEL}")
print()

# Test chat completion
response = requests.post(
    f"{BASE_URL}/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": MODEL,
        "messages": [{"role": "user", "content": "Say hello in one sentence."}],
        "max_tokens": 50,
    },
    timeout=60,
)

if response.status_code == 200:
    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    print(f"SUCCESS: {reply}")
else:
    print(f"ERROR {response.status_code}: {response.text}")
