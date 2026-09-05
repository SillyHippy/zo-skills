#!/usr/bin/env python3
"""
Super Agent Orchestrator
Multi-agent task orchestration using the Zo /zo/ask API.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional

import aiohttp

ZO_API_URL = "https://api.zo.computer/zo/ask"
MODEL_NAME = "byok:e68b8ecd-5a76-4f97-a1be-69ab2dddf351"


def get_token():
    """Get the Zo API token from environment."""
    token = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")
    if not token:
        print("ERROR: ZO_CLIENT_IDENTITY_TOKEN not set in environment.")
        sys.exit(1)
    return token


async def call_zo_api(session: aiohttp.ClientSession, prompt: str, timeout: int = 300) -> str:
    """Call the Zo /zo/ask API and return the output text."""
    token = get_token()
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = {
        "input": prompt,
        "model_name": MODEL_NAME,
    }

    try:
        async with session.post(ZO_API_URL, headers=headers, json=body, timeout=timeout) as resp:
            if resp.status != 200:
                text = await resp.text()
                return f"[ERROR: HTTP {resp.status}] {text[:200]}"
            data = await resp.json()
            return data.get("output", "[No output returned]")
    except asyncio.TimeoutError:
        return "[ERROR: Request timed out]"
    except Exception as e:
        return f"[ERROR: {str(e)}]"


async def planner(session: aiohttp.ClientSession, goal: str) -> list[str]:
    """Ask a planning agent to break the goal into sub-tasks."""
    prompt = (
        f"You are a task planner. Break down this goal into 3-7 specific, independent sub-tasks "
        f"that can be executed in parallel by different agents.\n\n"
        f"GOAL: {goal}\n\n"
        f"Respond ONLY with a JSON array of strings, one sub-task per string. "
        f"Each sub-task should be self-contained and include all context needed for an agent "
        f"to execute it independently.\n\n"
        f"Example: [\"Search public records for current addresses of John Doe in Tulsa OK\", "
        f"\"Search social media for recent activity of John Doe\", "
        f"\"Search court databases for cases involving John Doe in Oklahoma\"]"
    )
    result = await call_zo_api(session, prompt)

    # Try to parse JSON from the result
    for line in result.strip().split("\n"):
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            try:
                tasks = json.loads(line)
                if isinstance(tasks, list) and len(tasks) > 0:
                    return tasks
            except json.JSONDecodeError:
                continue

    # Fallback: return the goal as a single task
    return [goal]


async def execute_task(
    session: aiohttp.ClientSession, task: str, index: int, total: int
) -> dict:
    """Execute a single sub-task via a child Zo agent."""
    agent_prompt = (
        f"You are a specialized research agent. Execute the following task thoroughly.\n\n"
        f"TASK: {task}\n\n"
        f"Instructions:\n"
        f"- Use all available tools (web search, file reading, etc.) to complete this task.\n"
        f"- Provide specific, factual findings with sources where possible.\n"
        f"- If you cannot find information, state clearly what you could not find.\n"
        f"- Keep your response focused and structured.\n\n"
        f"Respond with your findings below."
    )

    print(f"  [Agent {index + 1}/{total}] Starting: {task[:80]}{'...' if len(task) > 80 else ''}")
    result = await call_zo_api(session, agent_prompt, timeout=600)
    print(f"  [Agent {index + 1}/{total}] Complete ({len(result)} chars)")
    return {"task": task, "index": index, "result": result}


async def synthesizer(
    session: aiohttp.ClientSession, goal: str, findings: list[dict]
) -> str:
    """Synthesize all findings into a final report."""
    findings_text = ""
    for f in findings:
        findings_text += f"\n--- Agent {f['index'] + 1}: {f['task']} ---\n{f['result']}\n"

    prompt = (
        f"You are a report synthesizer. Combine the following agent findings into a cohesive, "
        f"well-structured report.\n\n"
        f"ORIGINAL GOAL: {goal}\n\n"
        f"FINDINGS:\n{findings_text}\n\n"
        f"Instructions:\n"
        f"- Organize findings by topic/agent.\n"
        f"- Highlight confirmed facts vs. uncertainties.\n"
        f"- Note any contradictions between agents.\n"
        f"- Provide a clear executive summary at the top.\n"
        f"- Use markdown formatting.\n\n"
        f"Return the final report in markdown."
    )

    print("\n[Synthesizer] Compiling final report...")
    return await call_zo_api(session, prompt, timeout=300)


async def run_orchestrator(
    goal: str,
    tasks: Optional[list[str]] = None,
    sequential: bool = False,
    workers: int = 5,
) -> str:
    """Run the full orchestrator pipeline."""
    async with aiohttp.ClientSession() as session:
        # Step 1: Plan
        if not tasks:
            print("[Planner] Breaking down goal into sub-tasks...")
            tasks = await planner(session, goal)
            print(f"[Planner] Identified {len(tasks)} sub-task(s):\n")
            for i, t in enumerate(tasks, 1):
                print(f"  {i}. {t}")
            print()

        # Step 2: Execute
        print(f"[Executor] Dispatching {len(tasks)} agent(s)...")
        if sequential:
            print("[Executor] Running in sequential mode.\n")
            findings = []
            for i, task in enumerate(tasks):
                result = await execute_task(session, task, i, len(tasks))
                findings.append(result)
        else:
            print(f"[Executor] Running in parallel mode ({workers} workers).\n")
            semaphore = asyncio.Semaphore(workers)

            async def bounded_execute(task, i):
                async with semaphore:
                    return await execute_task(session, task, i, len(tasks))

            findings = await asyncio.gather(
                *[bounded_execute(t, i) for i, t in enumerate(tasks)]
            )

        # Step 3: Synthesize
        print()
        report = await synthesizer(session, goal, findings)
        return report


def main():
    parser = argparse.ArgumentParser(description="Super Agent Orchestrator")
    parser.add_argument("--goal", required=True, help="The main goal to accomplish")
    parser.add_argument("--tasks", nargs="*", default=None, help="Explicit sub-tasks (skip auto-planning)")
    parser.add_argument("--sequential", action="store_true", help="Run agents one at a time")
    parser.add_argument("--workers", type=int, default=5, help="Number of parallel workers (default: 5)")
    parser.add_argument("--output", type=str, default=None, help="Save final report to file")

    args = parser.parse_args()

    print("=" * 60)
    print("  SUPER AGENT ORCHESTRATOR")
    print(f"  Goal: {args.goal}")
    print(f"  Mode: {'Sequential' if args.sequential else f'Parallel ({args.workers} workers)'}")
    print("=" * 60)
    print()

    report = asyncio.run(run_orchestrator(args.goal, args.tasks, args.sequential, args.workers))

    print("\n" + "=" * 60)
    print("  FINAL REPORT")
    print("=" * 60)
    print(report)

    if args.output:
        with open(args.output, "w") as f:
            f.write(f"# Orchestrator Report\n")
            f.write(f"# Goal: {args.goal}\n")
            f.write(f"# Date: {datetime.now().isoformat()}\n\n")
            f.write(report)
        print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    main()
