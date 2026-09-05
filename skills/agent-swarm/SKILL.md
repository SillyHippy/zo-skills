---
name: agent-swarm
description: Mimics Moonshot AI's Kimi K2.6 Agent Swarm — decompose tasks into parallel sub-agents, coordinate execution via Zo API, and synthesize results. Use for research, batch processing, multi-format output, and any task that decomposes into parallel subtasks. Model-agnostic, framework-native on Zo.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
  version: "2.0.0"
  architecture: "Model-agnostic coordinator + Zo API parallel sub-agents. Mimics Kimi K2.6 Agent Swarm pattern (task decomposition → heterogeneous agent spawning → parallel execution → synthesis)."
  max_agents: 300 (batched in groups of 20 per wave)
  max_steps: 4000 (total coordinated step budget)
---

# Agent Swarm — Zo-Native Multi-Agent Orchestration

Mimics the Kimi K2.6 Agent Swarm architecture using Zo's native `/zo/ask` API as the sub-agent execution layer. You (the coordinator) decompose a complex task, spawn heterogeneous sub-agents in parallel, and synthesize their outputs — no external orchestration frameworks required.

## How It Works

The Kimi Agent Swarm is **model-native** — the model itself handles orchestration. Since we can't modify the model, we implement the same pattern using a **Python coordinator** that wraps the Zo API:

```
┌─────────────────────────────────────────────────────────┐
│                   COORDINATOR (you)                      │
│  1. Decompose task into subtasks                        │
│  2. Classify each subtask by agent type                 │
│  3. Spawn sub-agents via Zo API in parallel waves       │
│  4. Monitor progress, handle failures, retry            │
│  5. Synthesize all outputs into final deliverable       │
└──────────┬──────────────────────────────────┬───────────┘
           │                                  │
    ┌──────▼──────┐  ┌──────┐  ┌──────┐  ┌───▼──────────┐
    │  Researcher  │  │Coder │  │Writer│  │   Analyst     │
    │  (web search)│  │(code)│  │(prose│  │  (data)       │
    └──────────────┘  └──────┘  └──────┘  └──────────────┘
           │               │         │            │
           └───────────────┴─────────┴────────────┘
                           │
                  ┌────────▼────────┐
                  │  SYNTHESIZER    │
                  │  Merge outputs  │
                  │  into final doc │
                  └─────────────────┘
```

## When to Use

- **Parallel research** — investigate multiple topics/sources simultaneously
- **Batch processing** — process many items with the same logic (classification, enrichment, summarization)
- **Multi-format output** — produce reports, code, data, and docs from one prompt
- **Comparative analysis** — research competitors, evaluate options, cross-validate findings
- **Deep dives** — explore a topic from multiple angles (technical, business, legal, etc.)

## Quick Start

```bash
# Basic research swarm
python Skills/agent-swarm/scripts/swarm.py \
  --task "Research the top 10 competitors in cloud databases. For each: pricing, features, customers, funding. Output structured comparison." \
  --agent-types researcher,analyst,writer \
  --max-agents 20

# Full-scale swarm with custom output
python Skills/agent-swarm/scripts/swarm.py \
  --task-file /home/workspace/my-research-brief.md \
  --agent-types researcher,coder,analyst,writer,tester \
  --max-agents 100 \
  --output-format report,spreadsheet,slides \
  --verbose
```

## Agent Types

| Type | Role | Best For |
|------|------|----------|
| `researcher` | Web search, fact gathering, source verification | Competitive intel, literature reviews, due diligence |
| `coder` | Code generation, debugging, optimization, refactoring | Software engineering, automation scripts |
| `writer` | Prose, documentation, reports, creative content | Reports, articles, documentation |
| `analyst` | Data analysis, pattern recognition, statistics | Financial analysis, metrics, trend analysis |
| `tester` | Validation, edge cases, quality assurance | Code review, fact-checking, consistency validation |
| `generalist` | Any task type; fallback when specialization unclear | General-purpose subtasks |

## Architecture Details

See `references/architecture.md` for deep technical documentation on:
- How Kimi K2.6 Agent Swarm works under the hood
- How we adapted the pattern for Zo's API constraints
- State management, failure recovery, and step budgeting
- Comparison with LangGraph, CrewAI, and other frameworks

## Failure Recovery

The swarm handles failures automatically:
- **Agent timeout**: 5 min default, configurable per agent type
- **Empty/stale output**: detected and retried up to 3 times
- **Coordinator stall**: if an agent hangs, its subtask is reassigned
- **Step budget tracking**: total steps consumed vs budget, prevents infinite loops

## Limitations (Honest)

- **Not model-native**: we can't modify the LLM itself, so decomposition quality depends on prompt engineering
- **Concurrency cap**: Zo API recommends ~20 concurrent requests; larger swarms use batching
- **Cost**: each sub-agent is a full Zo session — budget carefully for large swarms
- **State drift**: file-based state can get stale under high concurrency; coordinator enforces serialized merge
- **Orchestration is a black box**: sub-agent routing is template-based, not learned
- **No persistent memory**: agents start fresh each run (unlike Kimi's persistent contexts)

## Scripts

- `scripts/swarm.py` — Main coordinator. Decompose, spawn, monitor, synthesize.
- `scripts/swarm_agent.py` — Sub-agent runner (called by Zo API). Execute single subtask.

Run `python scripts/swarm.py --help` for full options.
