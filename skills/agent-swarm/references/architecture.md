# Agent Swarm Architecture — Deep Technical Reference

## How Kimi K2.6 Agent Swarm Works (Original)

### Architectural Choice: Model-Native Orchestration

Kimi K2.6 absorbs multi-agent orchestration into the model itself. This means:

1. **No external framework** — no LangGraph, CrewAI, or custom orchestration code
2. **The model IS the coordinator** — task decomposition, agent spawning, routing, and synthesis are all first-party model capabilities learned during training
3. **Heterogeneous decomposition** — the model analyzes task structure and assigns subtasks based on agent "skill profiles" (searcher, coder, writer, analyst), not uniform cloning
4. **Shared state coordinator** — a controller manages dependencies, detects failures, and synthesizes results

### Four-Phase Execution Pipeline

```
Phase 1: TASK DECOMPOSITION
  Input: Natural language task description
  Process: Model analyzes task structure, identifies parallelizable components
  Output: Decomposition plan mapping subtasks → agent types

Phase 2: AGENT INSTANTIATION
  Process: Dynamically spawns specialized sub-agents
  Characteristic: Heterogeneous (different types), not uniform clones
  Scale: Up to 300 in K2.6 (was 100 in K2.5)

Phase 3: PARALLEL EXECUTION
  Process: Sub-agents execute simultaneously
  Coordination: Shared operational space with dependency management
  Budget: 4,000 total coordinated steps (avg ~13 per agent at full scale)
  Failure recovery: Automatic stall detection, task reassignment

Phase 4: SYNTHESIS
  Process: Coordinator gathers outputs, resolves conflicts
  Output: Multi-format — documents, websites, slides, spreadsheets, code
```

### K2.5 → K2.6 Evolution

| Capability | K2.5 (Jan 2026) | K2.6 (Apr 2026) |
|---|---|---|
| Max sub-agents | 100 | 300 |
| Coordinated steps | 1,500 | 4,000 |
| Tool call failure rate | ~12% | Improved (unspecified) |
| BrowseComp (swarm) | 78.4% | 86.3% |
| Claw Groups | No | Research preview |
| Document-to-Skill | No | Yes |
| Release status | Beta | GA |

### Key Insight: Architecture Didn't Change

K2.5 and K2.6 share the same architecture (1T params, 32B active, 384 experts, 61 layers, MLA attention). The improvements are purely post-training — more compute on long-horizon stability, instruction following, and swarm coordination routing. The model got better at *using* the capability it already had.

---

## Our Adaptation for Zo Computer

### The Constraint

We cannot modify the LLM's architecture or training. Kimi's model-native approach relies on the model having been trained on swarm coordination — our model wasn't. We must implement the coordination layer externally.

### Our Approach: Coordinator + Zo API

```
┌──────────────────────────────────────────────────┐
│              COORDINATOR (swarm.py)               │
│                                                   │
│  ┌─────────┐  ┌──────────┐  ┌────────────────┐  │
│  │Decompose│→ │Classify  │→ │Batch & Dispatch│  │
│  │(LLM)    │  │by type   │  │(Zo API calls)  │  │
│  └─────────┘  └──────────┘  └───────┬────────┘  │
│                                      │            │
│  ┌──────────────────────────────────▼──────────┐ │
│  │         PARALLEL EXECUTION LAYER             │ │
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ...    │ │
│  │  │ A1 │ │ A2 │ │ A3 │ │ A4 │ │ A5 │ (up to  │ │
│  │  │Res │ │Cod │ │Wri │ │Ana │ │Tes │  300)   │ │
│  │  └────┘ └────┘ └────┘ └────┘ └────┘         │ │
│  └──────────────────────────────────────────────┘ │
│                                      │            │
│  ┌──────────────────────────────────▼──────────┐ │
│  │              SYNTHESIZER                     │ │
│  │  Merge outputs → Validate → Format → Output  │ │
│  └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### Component Details

#### 1. Task Decomposition (LLM-driven)

We use an LLM call (ourselves, via the coordinator's own reasoning) to decompose tasks. The decomposition prompt instructs:
- Identify independent subtasks that can run in parallel
- Classify each subtask by required agent type
- Note dependencies between subtasks
- Estimate step complexity (for budget tracking)

#### 2. Agent Profiles

Six specialized agent types with distinct system prompts (see `assets/agent_profiles.json`):
- **researcher**: web search, fact verification, source gathering
- **coder**: code generation, debugging, optimization
- **writer**: prose, documentation, reports
- **analyst**: data analysis, pattern recognition, quantitative work
- **tester**: QA, edge cases, consistency checking
- **generalist**: fallback for any task type

Each profile defines:
- System prompt (the agent's "personality" and rules)
- Timeout (how long before we consider it stalled)
- Max retries (how many times we retry on failure)
- Max tokens (output token budget per agent)
- Step weight (how many steps each agent call counts against the budget)

#### 3. Parallel Execution via Zo API

We spawn sub-agents using the Zo `/zo/ask` API. Key implementation details:

- **Auth**: Uses `ZO_CLIENT_IDENTITY_TOKEN` env var automatically available in the shell
- **Model**: Passes `byok:7c9fded2-d777-42b0-8400-6a00ee71d77e` (our current BYOK model)
- **Concurrency**: Zo recommends ~20 concurrent requests. For larger swarms, we batch into waves of 20.
- **Prompt construction**: Each sub-agent prompt is fully self-contained — includes the agent profile system prompt, the specific subtask, context from any dependencies, and output format requirements.

#### 4. State Management

File-based state in `.swarm-runs/{run_id}/`:
```
.swarm-runs/
└── run_20260517_223000/
    ├── manifest.json       # Full run state
    ├── decomposition.json  # Decomposition plan
    ├── agent_001_output.md # Sub-agent outputs
    ├── agent_002_output.md
    ├── ...
    ├── synthesis.md        # Synthesized result
    └── run.log             # Execution log
```

#### 5. Failure Recovery

Three-layer recovery system:
1. **Timeout detection**: Each agent has a configurable timeout. If no response within timeout, mark as stalled.
2. **Output validation**: Check for empty, truncated, or clearly broken outputs.
3. **Retry with backoff**: Failed agents retry up to `max_retries` times with exponential backoff.
4. **Reassignment**: If all retries exhausted, reassign the subtask to a different agent type if appropriate, or mark as failed in the synthesis.

#### 6. Synthesis

After all agents complete, the coordinator:
1. Reads all agent outputs
2. Merges related findings (deduplication)
3. Resolves contradictions (flags disagreements)
4. Formats into requested output types
5. Runs a tester agent on the synthesis if requested
6. Saves final output to `.swarm-runs/{run_id}/synthesis.md`

### Step Budget System

We track steps consumed vs the total budget (default 4000, configurable):
- Each agent spawn costs 1 step
- Each agent type has a `step_weight` (research=10, coding=15, writing=8, etc.)
- Actual steps consumed = number of agents × their step weight
- Coordinator warns if approaching budget limit
- Can auto-stop spawning new agents when budget exhausted

---

## Comparison: Our Approach vs Others

| Dimension | Kimi K2.6 (model-native) | Zo Agent Swarm (coordinator) | LangGraph/CrewAI (framework) |
|---|---|---|---|
| Orchestration | Inside the model | Python script + Zo API | Graph/rules in code |
| Setup | Zero (prompt only) | Run a script | Build a graph/crew |
| Control | Black box | Full (Python) | Full (Python) |
| Audit trail | None | Full (files + logs) | Configurable |
| Max agents | 300 | 300 (batched) | Unlimited |
| Model choice | Kimi only | Any on Zo | Any LLM |
| Cost visibility | Opaque | Per-agent tracking | Per-node tracking |
| Failure recovery | Automatic (hidden) | Configurable (explicit) | Manual (code it) |
| Persistent memory | Per-agent (K2.6) | None (stateless) | Built-in (CrewAI) |

---

## Sources

- Kimi K2.6 Agent Swarm technical breakdown: https://kimik2ai.com/agent-swarm-k2.6/
- Verdent AI deep analysis: https://www.verdent.ai/guides/kimi-k2-6-agent-swarm
- Till Freitag architecture comparison: https://till-freitag.com/blog/agent-swarm-architectures-compared
- Moonshot AI official blog: https://www.kimi.com/blog/kimi-k2-6
- MarkTechPost coverage: https://www.marktechpost.com/2026/04/20/moonshot-ai-releases-kimi-k2-6-with-long-horizon-coding-agent-swarm-scaling-to-300-sub-agents-and-4000-coordinated-steps/
