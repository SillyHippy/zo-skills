---
name: repo-update-check
description: Deterministic installed-vs-upstream check for Hermes, QWEN-gate, 9router, and mem0. Used by the daily automation — no LLM guessing.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---

# Repo update check

Run the script only:

```bash
python3 /home/workspace/Skills/repo-update-check/scripts/check_updates.py
```

Stdout is JSON with `should_notify`, `telegram_message`, and `items`. The automation must send Telegram **only** when `should_notify` is true, using `telegram_message` verbatim.