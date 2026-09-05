---
name: obsidian-memory
description: Read and write memory files in the Obsidian vault at /home/workspace/Obsidian/Hermes-Memory/. Companion to Mem0.
---

# obsidian-memory

This skill provides long-term human-readable memory via an Obsidian vault. It works alongside Mem0 (the external memory provider for agent retrieval).

## Vault Location
`/home/workspace/Obsidian/Hermes-Memory/`

## Folder Structure
```
Obsidian/Hermes-Memory/
├── People/           # Individual user profiles
├── Preferences/      # Style, rules, communication prefs
├── Projects/         # Active projects and context
├── Decisions/        # Important decisions and reasoning
├── Daily/            # Daily notes (YYYY-MM-DD.md)
└── Memory-Summaries/ # Periodic Mem0 exports
```

## When to Use
- Write important facts, preferences, and decisions to the correct folder
- Update existing files with new information
- Read from the vault when context is needed
- Keep notes short, structured, and linkable

## Rules
- Always use /home/workspace/Obsidian/Hermes-Memory/ not /root/Obsidian/
- Continue using Mem0 for fast retrieval
- User can read these files directly