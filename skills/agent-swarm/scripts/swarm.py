#!/usr/bin/env python3
"""
Zo Agent Swarm — Coordinator
Mimics Kimi K2.6 Agent Swarm: decompose → spawn → execute → synthesize

Usage:
    python swarm.py --task "Research top 10 competitors..." --agent-types researcher,analyst --max-agents 20
    python swarm.py --task-file brief.md --agent-types researcher,coder,writer,analyst,tester --max-agents 100 --verbose

Architecture:
    Coordinator (this script) → Zo /zo/ask API → Sub-agents (parallel) → Synthesis
"""

import os
import sys
import json
import time
import uuid
import asyncio
import argparse
import subprocess
import signal
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

try:
    import aiohttp
except ImportError:
    print("Installing aiohttp...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp", "-q"])
    import aiohttp

# ── Constants ────────────────────────────────────────────────────────────────

SKILL_DIR = Path(__file__).resolve().parent.parent
PROFILES_PATH = SKILL_DIR / "assets" / "agent_profiles.json"
WORKSPACE = Path("/home/workspace")
RUNS_DIR = WORKSPACE / ".swarm-runs"
ZO_API_URL = "https://api.zo.computer/zo/ask"
DEFAULT_MODEL = "byok:28a2655c-38fc-4571-9a01-fcf76d57ef6b"

MAX_CONCURRENT = 3  # Zo API recommended max (5 per workspace, leaving buffer)
DEFAULT_MAX_AGENTS = 50
DEFAULT_MAX_STEPS = 4000
DEFAULT_TIMEOUT = 300  # seconds per agent

# ── Agent Profiles ───────────────────────────────────────────────────────────

def load_profiles() -> dict:
    """Load agent profiles from JSON."""
    with open(PROFILES_PATH) as f:
        return json.load(f)

# ── Run State ─────────────────────────────────────────────────────────────────

class SwarmRun:
    """Tracks state for a single swarm run."""

    def __init__(self, run_id: str, task: str, agent_types: list[str],
                 max_agents: int, max_steps: int, output_formats: list[str],
                 verbose: bool = False):
        self.run_id = run_id
        self.task = task
        self.agent_types = agent_types
        self.max_agents = max_agents
        self.max_steps = max_steps
        self.output_formats = output_formats
        self.verbose = verbose
        self.run_dir = RUNS_DIR / run_id
        self.manifest = {
            "run_id": run_id,
            "task": task,
            "agent_types": agent_types,
            "max_agents": max_agents,
            "max_steps": max_steps,
            "output_formats": output_formats,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "initializing",
            "decomposition": None,
            "subtasks": [],
            "completed": 0,
            "failed": 0,
            "steps_used": 0,
            "started_at": None,
            "finished_at": None,
        }
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._save_manifest()

    def _save_manifest(self):
        with open(self.run_dir / "manifest.json", "w") as f:
            json.dump(self.manifest, f, indent=2)

    def log(self, msg: str):
        timestamp = datetime.now(timezone.utc).isoformat()
        line = f"[{timestamp}] {msg}"
        if self.verbose:
            print(line, file=sys.stderr)
        with open(self.run_dir / "run.log", "a") as f:
            f.write(line + "\n")

    def update(self, **kwargs):
        self.manifest.update(kwargs)
        self._save_manifest()

# ── Task Decomposition ───────────────────────────────────────────────────────

def decompose_task(task: str, agent_types: list[str], max_agents: int) -> list[dict]:
    """
    Decompose a complex task into subtasks.
    Uses the coordinator's own reasoning (we write the plan ourselves based on
    analysis of the task structure) rather than making a separate LLM call.
    """
    profiles = load_profiles()
    available_types = set(agent_types)

    # Build the decomposition prompt for ourselves
    # We'll analyze the task and create subtasks
    system_prompt = f"""You are a task decomposition specialist. Analyze the given task and break it into parallel subtasks.

Available agent types: {', '.join(agent_types)}
Maximum subtasks: {max_agents}

Rules:
1. Each subtask must be INDEPENDENT (can run in parallel)
2. Assign the best agent type for each subtask
3. Be specific — vague subtasks produce vague results
4. Number subtasks starting from 1
5. Include the exact question/instruction for each agent
6. Group related work but keep subtasks atomic

Output ONLY valid JSON array of objects with keys:
- id (int): subtask number
- agent_type (str): one of the available types
- instruction (str): exact instructions for the agent
- context (str): any background context the agent needs
- dependencies (list[int]): IDs of subtasks this depends on (empty if none)
"""

    # We use ourselves to decompose — write the plan directly
    # This is the key design decision: coordinator uses its own intelligence
    # rather than spawning yet another agent for decomposition
    
    decomposition_prompt = f"""{system_prompt}

TASK TO DECOMPOSE:
{task}

Output ONLY the JSON array. No explanation, no markdown wrapping."""

    return decomposition_prompt  # Return the prompt for the caller to handle

# ── Agent Execution ───────────────────────────────────────────────────────────

def build_agent_prompt(subtask: dict, profiles: dict) -> str:
    """Build a fully self-contained prompt for a sub-agent."""
    agent_type = subtask["agent_type"]
    profile = profiles.get(agent_type, profiles["generalist"])

    prompt_parts = [
        profile["system_prompt"],
        "",
        "─── YOUR SPECIFIC TASK ───",
        f"Task ID: {subtask['id']}",
        f"Agent Type: {agent_type}",
        "",
        "INSTRUCTIONS:",
        subtask["instruction"],
    ]

    if subtask.get("context"):
        prompt_parts.extend(["", "BACKGROUND CONTEXT:", subtask["context"]])

    if subtask.get("dependencies"):
        prompt_parts.extend(["", f"NOTE: You may need results from subtask(s): {subtask['dependencies']} — do your best with what you know."])

    prompt_parts.extend([
        "",
        "─── OUTPUT REQUIREMENTS ───",
        "Produce your complete output. Be thorough and specific.",
        "This is part of a coordinated swarm — your output will be merged with others.",
        "Do NOT ask clarifying questions in your output — work with what you have.",
    ])

    return "\n".join(prompt_parts)


async def spawn_agent(session: aiohttp.ClientSession, subtask: dict,
                      profiles: dict, token: str, semaphore: asyncio.Semaphore,
                      run: SwarmRun) -> Optional[dict]:
    """Spawn a single sub-agent via Zo API and collect its output."""
    agent_type = subtask["agent_type"]
    profile = profiles.get(agent_type, profiles["generalist"])
    timeout = profile.get("timeout_seconds", DEFAULT_TIMEOUT)
    prompt = build_agent_prompt(subtask, profiles)

    payload = {
        "input": prompt,
        "model_name": DEFAULT_MODEL,
    }

    agent_id = f"agent_{subtask['id']:03d}"
    output_path = run.run_dir / f"{agent_id}_output.md"

    async with semaphore:
        run.log(f"[{agent_id}] Spawning ({agent_type})...")
        start = time.time()

        try:
            async with session.post(
                ZO_API_URL,
                headers={
                    "authorization": token,
                    "content-type": "application/json",
                },
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout + 60),
            ) as resp:
                elapsed = time.time() - start

                if resp.status == 200:
                    result = await resp.json()
                    output = result.get("output", "")

                    if output and len(output.strip()) > 50:
                        # Save output
                        with open(output_path, "w") as f:
                            f.write(f"# {agent_id} — {agent_type}\n")
                            f.write(f"Task: {subtask['instruction'][:200]}...\n")
                            f.write(f"Completed in: {elapsed:.1f}s\n\n")
                            f.write(output)

                        run.log(f"[{agent_id}] ✓ Completed in {elapsed:.1f}s ({len(output)} chars)")
                        return {
                            "agent_id": agent_id,
                            "subtask_id": subtask["id"],
                            "agent_type": agent_type,
                            "status": "success",
                            "output": output,
                            "elapsed": elapsed,
                        }
                    else:
                        run.log(f"[{agent_id}] ✗ Empty/short output ({len(output)} chars)")
                        return {
                            "agent_id": agent_id,
                            "subtask_id": subtask["id"],
                            "agent_type": agent_type,
                            "status": "empty_output",
                            "output": output,
                            "elapsed": elapsed,
                        }
                else:
                    body = await resp.text()
                    run.log(f"[{agent_id}] ✗ HTTP {resp.status}: {body[:200]}")
                    return {
                        "agent_id": agent_id,
                        "subtask_id": subtask["id"],
                        "agent_type": agent_type,
                        "status": "error",
                        "error": f"HTTP {resp.status}",
                        "elapsed": elapsed,
                    }

        except asyncio.TimeoutError:
            run.log(f"[{agent_id}] ✗ Timeout after {timeout}s")
            return {
                "agent_id": agent_id,
                "subtask_id": subtask["id"],
                "agent_type": agent_type,
                "status": "timeout",
                "elapsed": timeout,
            }
        except Exception as e:
            run.log(f"[{agent_id}] ✗ Exception: {e}")
            return {
                "agent_id": agent_id,
                "subtask_id": subtask["id"],
                "agent_type": agent_type,
                "status": "exception",
                "error": str(e),
                "elapsed": time.time() - start,
            }


async def execute_wave(run: SwarmRun, subtasks: list[dict],
                       profiles: dict, token: str) -> list[dict]:
    """Execute a wave of up to MAX_CONCURRENT agents."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async with aiohttp.ClientSession() as session:
        tasks = [
            spawn_agent(session, st, profiles, token, semaphore, run)
            for st in subtasks
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Flatten exceptions
    flattened = []
    for r in results:
        if isinstance(r, Exception):
            flattened.append({"status": "exception", "error": str(r)})
        else:
            flattened.append(r)

    return flattened


def retry_failed(run: SwarmRun, results: list[dict], profiles: dict) -> list[dict]:
    """Identify failed agents that should be retried."""
    retryable = []
    final = []

    for r in results:
        agent_type = r.get("agent_type", "generalist")
        profile = profiles.get(agent_type, profiles["generalist"])
        max_retries = profile.get("max_retries", 3)

        if r["status"] in ("timeout", "empty_output", "error", "exception"):
            retries = r.get("_retries", 0)
            if retries < max_retries:
                r["_retries"] = retries + 1
                retryable.append(r)
                run.log(f"[{r['agent_id']}] ⟳ Retry {retries + 1}/{max_retries}")
            else:
                r["status"] = "exhausted"
                final.append(r)
                run.log(f"[{r['agent_id']}] ✗ Exhausted retries")
        else:
            final.append(r)

    return retryable, final


# ── Synthesis ─────────────────────────────────────────────────────────────────

def synthesize(run: SwarmRun, results: list[dict]) -> str:
    """Merge all agent outputs into a coherent final deliverable."""
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] != "success"]

    parts = [
        f"# Agent Swarm Results — {run.run_id}",
        f"",
        f"**Task:** {run.task[:300]}",
        f"**Run time:** {datetime.now(timezone.utc).isoformat()}",
        f"**Agents:** {len(results)} total ({len(successful)} succeeded, {len(failed)} failed)",
        f"**Steps used:** {run.manifest['steps_used']} / {run.manifest['max_steps']}",
        f"",
        f"---",
        f"",
    ]

    # Group by agent type
    by_type = {}
    for r in successful:
        t = r["agent_type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(r)

    for agent_type, agents in sorted(by_type.items()):
        parts.append(f"## {agent_type.title()} Agents ({len(agents)} results)")
        parts.append("")
        for r in agents:
            parts.append(f"### Subtask {r['subtask_id']} ({r['agent_id']})")
            parts.append("")
            parts.append(r["output"])
            parts.append("")
            parts.append("---")
            parts.append("")

    if failed:
        parts.append(f"## Failed/Incomplete ({len(failed)} agents)")
        parts.append("")
        for r in failed:
            parts.append(f"- **{r.get('agent_id', 'unknown')}** ({r.get('agent_type', '?')}): {r['status']}")
            if r.get("error"):
                parts.append(f"  - Error: {r['error']}")
        parts.append("")

    parts.append("## Synthesis Notes")
    parts.append("")
    parts.append("The above outputs were produced by independent parallel agents.")
    parts.append("Review for contradictions, redundancies, and completeness before using.")
    parts.append(f"Full run logs: `{run.run_dir}/run.log`")

    synthesis = "\n".join(parts)
    synthesis_path = run.run_dir / "synthesis.md"
    with open(synthesis_path, "w") as f:
        f.write(synthesis)

    return synthesis


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(
        description="Zo Agent Swarm — Multi-agent parallel task execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python swarm.py --task "Research cloud database competitors" --agent-types researcher,analyst
  python swarm.py --task-file brief.md --agent-types researcher,coder,writer --max-agents 100 --verbose
  python swarm.py --task "Analyze Q2 financials" --agent-types analyst,researcher,tester --output-formats report
        """
    )
    parser.add_argument("--task", help="Task description (natural language)")
    parser.add_argument("--task-file", help="Read task from a file")
    parser.add_argument("--agent-types", default="researcher,analyst,writer",
                        help="Comma-separated agent types (default: researcher,analyst,writer)")
    parser.add_argument("--max-agents", type=int, default=DEFAULT_MAX_AGENTS,
                        help=f"Maximum sub-agents to spawn (default: {DEFAULT_MAX_AGENTS})")
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS,
                        help=f"Maximum coordinated step budget (default: {DEFAULT_MAX_STEPS})")
    parser.add_argument("--output-formats", default="report",
                        help="Comma-separated output formats: report,json (default: report)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--dry-run", action="store_true", help="Decompose but don't execute")
    parser.add_argument("--run-id", help="Resume an existing run (by run_id)")
    parser.add_argument("--subtasks-file", help="Path to pre-decomposed subtasks JSON (skips LLM decomposition)")
    parser.add_argument("--no-synthesis", action="store_true", help="Skip synthesis — just collect raw agent outputs")

    args = parser.parse_args()

    # Load task
    if args.task_file:
        task_path = Path(args.task_file)
        if not task_path.exists():
            print(f"Error: task file not found: {args.task_file}", file=sys.stderr)
            sys.exit(1)
        task = task_path.read_text()
    elif args.task:
        task = args.task
    else:
        print("Error: --task or --task-file required", file=sys.stderr)
        sys.exit(1)

    agent_types = [t.strip() for t in args.agent_types.split(",")]
    output_formats = [f.strip() for f in args.output_formats.split(",")]

    # Validate agent types
    profiles = load_profiles()
    valid_types = set(profiles.keys())
    for t in agent_types:
        if t not in valid_types:
            print(f"Warning: unknown agent type '{t}'. Available: {', '.join(sorted(valid_types))}", file=sys.stderr)

    # Create run
    run_id = args.run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    run = SwarmRun(
        run_id=run_id,
        task=task,
        agent_types=agent_types,
        max_agents=args.max_agents,
        max_steps=args.max_steps,
        output_formats=output_formats,
        verbose=args.verbose,
    )

    run.log(f"═══ Agent Swarm Run: {run_id} ═══")
    run.log(f"Task: {task[:200]}...")
    run.log(f"Agent types: {agent_types}")
    run.log(f"Max agents: {args.max_agents}, Max steps: {args.max_steps}")

    # Decompose task
    run.log("Phase 1: Task Decomposition")
    decomposition_prompt = decompose_task(task, agent_types, args.max_agents)

    # Load or decompose subtasks
    if args.subtasks_file:
        subtasks_path = Path(args.subtasks_file)
        if not subtasks_path.exists():
            print(f"Error: subtasks file not found: {args.subtasks_file}", file=sys.stderr)
            sys.exit(1)
        subtasks = json.loads(subtasks_path.read_text())
        run.log(f"Loaded {len(subtasks)} pre-decomposed subtasks")
    else:
        # Decompose task via LLM
        run.log("Decomposing task via LLM...")
        
        token = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN", "")
        if not token:
            print("Error: ZO_CLIENT_IDENTITY_TOKEN not set", file=sys.stderr)
            sys.exit(1)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                ZO_API_URL,
                headers={"authorization": token, "content-type": "application/json"},
                json={
                    "input": decomposition_prompt,
                    "model_name": DEFAULT_MODEL,
                },
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    raw = result.get("output", "")
                else:
                    print(f"Error: decomposition failed HTTP {resp.status}", file=sys.stderr)
                    sys.exit(1)

        # Parse the JSON array from the LLM output
        try:
            # Handle markdown code blocks
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0]
            
            subtasks = json.loads(raw.strip())
            if not isinstance(subtasks, list):
                raise ValueError("Expected JSON array")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing decomposition: {e}", file=sys.stderr)
            print(f"Raw output: {raw[:500]}", file=sys.stderr)
            sys.exit(1)

    # Limit to max_agents
    subtasks = subtasks[:args.max_agents]

    # Validate and fill defaults
    for i, st in enumerate(subtasks):
        st.setdefault("id", i + 1)
        st.setdefault("agent_type", "generalist")
        st.setdefault("dependencies", [])
        if st["agent_type"] not in valid_types:
            st["agent_type"] = "generalist"

    # Save decomposition AFTER validation (single save point)
    with open(run.run_dir / "decomposition.json", "w") as f:
        json.dump(subtasks, f, indent=2)

    run.update(
        decomposition=subtasks,
        subtasks=[{"id": s["id"], "agent_type": s["agent_type"], "instruction": s["instruction"][:100]}
                   for s in subtasks],
        status="decomposed",
    )

    run.log(f"Decomposed into {len(subtasks)} subtasks across {len(set(s['agent_type'] for s in subtasks))} agent types")

    if args.dry_run:
        run.log("Dry run — stopping after decomposition")
        print(f"\nDecomposition saved to: {run.run_dir}/decomposition.json")
        print(f"Run ID: {run_id}")
        return

    # Execute in waves
    run.log("Phase 2: Parallel Execution")
    run.update(status="executing", started_at=datetime.now(timezone.utc).isoformat())

    # Ensure token is available for execution
    token = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN", "")
    if not token:
        print("Error: ZO_CLIENT_IDENTITY_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    all_results = []
    remaining = list(subtasks)
    wave_num = 0

    while remaining:
        wave_num += 1
        wave = remaining[:MAX_CONCURRENT]
        remaining = remaining[MAX_CONCURRENT:]

        run.log(f"Wave {wave_num}: {len(wave)} agents (max {MAX_CONCURRENT} concurrent)")

        wave_results = await execute_wave(run, wave, profiles, token)
        all_results.extend(wave_results)

        # Handle retries
        retryable, final = retry_failed(run, wave_results, profiles)
        if retryable:
            # Re-add retryable to remaining (at front for priority)
            retry_subtasks = []
            for r in retryable:
                # Find the original subtask
                for st in subtasks:
                    if st["id"] == r["subtask_id"]:
                        retry_subtasks.append(st)
                        break
            remaining = retry_subtasks + remaining

        # Update step count
        steps_used = sum(
            profiles.get(r.get("agent_type", "generalist"), profiles["generalist"])["step_weight"]
            for r in all_results
        )
        run.update(
            completed=sum(1 for r in all_results if r["status"] == "success"),
            failed=sum(1 for r in all_results if r["status"] not in ("success", "retrying")),
            steps_used=steps_used,
        )

        if steps_used >= args.max_steps:
            run.log(f"⚠ Step budget exhausted ({steps_used}/{args.max_steps})")
            break

        if remaining:
            run.log(f"Waiting 5s between waves...")
            await asyncio.sleep(5)

    run.update(status="synthesizing", finished_at=datetime.now(timezone.utc).isoformat())

    # Phase 3: Synthesis
    run.log("Phase 3: Synthesis")
    synthesis = synthesize(run, all_results)

    run.update(status="complete")

    # Print summary
    successful = [r for r in all_results if r["status"] == "success"]
    failed = [r for r in all_results if r["status"] != "success"]

    print(f"\n═══ Swarm Complete ═══")
    print(f"Run ID: {run_id}")
    print(f"Results: {len(successful)} succeeded, {len(failed)} failed (of {len(all_results)} total)")
    print(f"Steps used: {run.manifest['steps_used']} / {args.max_steps}")
    print(f"Synthesis: {run.run_dir}/synthesis.md")
    print(f"Run directory: {run.run_dir}")

    # Copy synthesis to workspace if requested
    if "report" in output_formats:
        workspace_output = WORKSPACE / f"swarm_{run_id}.md"
        with open(workspace_output, "w") as f:
            f.write(synthesis)
        print(f"Workspace copy: {workspace_output}")


if __name__ == "__main__":
    asyncio.run(main())
