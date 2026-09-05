---
name: model-watcher
description: Monitor Command Code's upstream API for model additions/removals and report changes. Stores a baseline in /home/workspace/.model_baseline.json and compares daily.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---

# Model Watcher

Watches Command Code's provider model list for changes.

## Run

```bash
python3 /home/workspace/Skills/model-watcher/scripts/model_watcher.py
```

## Requirements

- `COMMANDCODE_API_KEY` environment variable set in Zo Settings > Advanced
- Python 3 + requests

## Behavior

1. Fetches current models from `https://api.commandcode.ai/provider/v1/models`
2. Loads baseline from `/home/workspace/.model_baseline.json` (creates one if missing)
3. Compares and prints any added/removed models
4. Updates baseline if changes were found

## Output codes

- `NO_CHANGES` — model list matches baseline
- `CHANGES_DETECTED` — models were added or removed
- Non-zero exit on fetch/API errors

## Automation

Intended to run daily via the "Model Watcher Script Execution" automation, which executes the script directly.
