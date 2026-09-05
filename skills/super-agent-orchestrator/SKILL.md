---
name: super-agent-orchestrator
description: Multi-agent task orchestration using the Zo /zo/ask API. Breaks complex goals into sub-tasks and dispatches them to parallel child agents, then synthesizes results. Use when you have multi-step research, skip tracing, document analysis, or any task that benefits from parallel agent execution.
compatibility: Created for Zo Computer. Requires `requests` and `aiohttp` Python packages.
metadata:
  author: sillyhippy.zo.computer
  version: 1.0.0
  pattern: planner-executor-synthesizer
---

# Super Agent Orchestrator

A lightweight multi-agent harness that uses the Zo `/zo/ask` API to spawn child agents for parallel task execution. No Docker, no heavy containers — just a Python script that orchestrates agents natively.

## How It Works

1. **Planner**: Analyzes the goal and breaks it into sub-tasks.
2. **Executors**: Dispatches sub-tasks to child Zo agent sessions via the `/zo/ask` API.
3. **Synthesizer**: Collects all results and compiles a final report.

## Usage

```bash
# Single goal (auto-planned):
cd /home/workspace/Skills/super-agent-orchestrator
python scripts/orchestrator.py --goal "Research the background of John Doe, find current address, and summarize any court records"

# With explicit sub-tasks:
python scripts/orchestrator.py --goal "Case research" --tasks "Search public records" "Check social media" "Summarize findings"

# Sequential mode (one agent at a time):
python scripts/orchestrator.py --goal "..." --sequential

# Save output to file:
python scripts/orchestrator.py --goal "..." --output /home/workspace/orchestrator-results.md

# Custom concurrency (parallel workers):
python scripts/orchentrator.py --goal "..." --workers 3
```

## When to Use

- **Skip tracing**: Multiple search strategies in parallel (public records, social media, reverse phone, etc.)
- **Case research**: Split into petition search, party lookup, document review simultaneously
- **Document analysis**: Analyze multiple documents at once and synthesize findings
- **Any multi-step workflow** where parallel agent execution saves time

## Architecture

```
┌─────────────────────┐
│     PLANNER         │  (breaks goal into sub-tasks)
└─────────┬───────────┘
          │
    ┌─────┼─────┐
    ▼     ▼     ▼
┌──────┐┌──────┐┌──────┐
│Agent1││Agent2││Agent3│  (child Zo sessions, parallel)
└──┬───┘└──┬───┘└──┬───┘
   │       │       │
   └───────┼───────┘
           ▼
┌─────────────────────┐
│   SYNTHESIZER       │  (compiles final report)
└─────────────────────┘
```

## Notes

- Each child invocation is an independent Zo session with full tool access.
- Child sessions use the same model as the parent (`byok:e68b8ecd-5a76-4f97-a1be-69ab2dddf351`).
- Default concurrency is 5 parallel workers. Adjust with `--workers`.
- Sequential mode (`--sequential`) runs one sub-task at a time (slower, but useful for dependent tasks).
- Costs scale with the number of sub-tasks and their complexity.
