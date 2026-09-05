#!/usr/bin/env python3
"""Audit Hermes /model picker — report duplicates, leaks, and misconfig."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/usr/local/lib/hermes-agent")
os.environ.setdefault("HOME", "/root")

from hermes_cli.config import load_config  # noqa: E402
from hermes_cli.model_switch import list_picker_providers  # noqa: E402

CONFIG = Path("/root/.hermes/config.yaml")
AUTH = Path("/root/.hermes/auth.json")

BAD_AUTH_POOLS = {
    "stepfun",
    "custom:gemini",
    "custom:gemini-1",
    "custom:gemini-2",
    "custom:opencode-zen-go-custom",
    "custom:clod",
    "custom:mistral",
    "custom:google",
}


def main() -> int:
    cfg = load_config()
    excluded = [
        str(p).strip().lower()
        for p in (cfg.get("model_catalog", {}) or {}).get("excluded_providers", [])
        if p
    ]
    providers = cfg.get("providers") or {}

    rows = list_picker_providers(
        current_provider=str((cfg.get("model") or {}).get("provider", "")),
        current_model=str((cfg.get("model") or {}).get("default", "")),
        user_providers=providers,
        include_moa=True,
        excluded_providers=excluded,
    )

    slugs = [str(r.get("slug", "")).lower() for r in rows]
    dup_slugs = sorted({s for s in slugs if slugs.count(s) > 1})

    leaks = []
    for name, pcfg in providers.items():
        if not isinstance(pcfg, dict):
            continue
        if name.lower() in excluded and pcfg.get("enabled", True) is not False:
            leaks.append(name)

    bad_pools = []
    if AUTH.exists():
        pools = (json.loads(AUTH.read_text()).get("credential_pool") or {}).keys()
        bad_pools = sorted(set(pools) & BAD_AUTH_POOLS)

    print("=== Hermes Model Picker Audit ===")
    print(f"Picker rows: {len(rows)}")
    print(f"Excluded list: {len(excluded)} entries")
    print(f"User providers: {len(providers)}")
    print()

    if dup_slugs:
        print(f"DUPLICATE SLUGS: {', '.join(dup_slugs)}")
    else:
        print("Duplicate slugs: none")

    if leaks:
        print(f"EXCLUDED BUT VISIBLE (need enabled: false): {', '.join(sorted(leaks))}")
    else:
        print("Excluded-leak user providers: none")

    if bad_pools:
        print(f"BAD AUTH POOLS: {', '.join(bad_pools)}")
    else:
        print("Bad auth pools: none")

    print()
    print("Visible providers:")
    for r in rows:
        mark = " [current]" if r.get("is_current") else ""
        print(
            f"  {r.get('slug')} ({r.get('name')}) — "
            f"{r.get('total_models', len(r.get('models') or []))} models{mark}"
        )

    issues = bool(dup_slugs or leaks or bad_pools)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
