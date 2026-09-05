#!/usr/bin/env python3
"""Fix Hermes /model picker — hide excluded user providers, clean auth pools."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

CONFIG = Path("/root/.hermes/config.yaml")
AUTH = Path("/root/.hermes/auth.json")
BACKUP_DIR = Path("/home/workspace/Backups/hermes")

BAD_AUTH_POOLS = [
    "custom:gemini",
    "custom:gemini-1",
    "custom:gemini-2",
    "custom:opencode-zen-go-custom",
    "stepfun",
    "custom:clod",
    "custom:mistral",
    "custom:google",
]

# Legacy key — keep in sync with model_catalog.excluded_providers
DISABLE_AUTO_PAIRS = [
    ("groq", "Groq"),
    ("mistral", "Mistral"),
    ("gemini", "Gemini"),
    ("google", "Google"),
    ("deepseek", "DeepSeek"),
    ("stepfun", "StepFun"),
]


def backup(path: Path) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(path, BACKUP_DIR / f"{path.name}.{ts}")


def fix_config() -> list[str]:
    data = yaml.safe_load(CONFIG.read_text())
    changes: list[str] = []

    excluded = {
        str(p).strip().lower()
        for p in (data.get("model_catalog") or {}).get("excluded_providers", [])
        if p
    }
    providers = data.get("providers") or {}

    for name, pcfg in providers.items():
        if not isinstance(pcfg, dict):
            continue
        if name.lower() in excluded and pcfg.get("enabled", True) is not False:
            pcfg["enabled"] = False
            changes.append(f"providers.{name}.enabled=false")

    disable = list(data.get("disable_auto_providers") or [])
    disable_set = {str(x).strip() for x in disable if x}
    added_disable = []
    for low, title in DISABLE_AUTO_PAIRS:
        for entry in (low, title):
            if entry not in disable_set:
                disable.append(entry)
                disable_set.add(entry)
                added_disable.append(entry)
    if added_disable:
        data["disable_auto_providers"] = disable
        changes.append(f"disable_auto_providers += {added_disable}")

    if changes:
        backup(CONFIG)
        CONFIG.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))

    return changes


def fix_auth() -> list[str]:
    if not AUTH.exists():
        return []
    data = json.loads(AUTH.read_text())
    pools = data.get("credential_pool") or {}
    removed = [k for k in BAD_AUTH_POOLS if k in pools]
    for k in removed:
        del pools[k]
    if removed:
        backup(AUTH)
        AUTH.write_text(json.dumps(data, indent=2) + "\n")
    return removed


def restart_gateway() -> None:
    script = Path("/home/workspace/Skills/hermes-gateway/scripts/hermes-gateway.sh")
    if script.exists():
        subprocess.run(["bash", str(script), "restart"], check=False)
        return
    subprocess.run(["supervisorctl", "restart", "hermes-gateway"], check=False)


def main() -> int:
    print("=== Hermes Model Picker Fix ===")
    cfg_changes = fix_config()
    auth_removed = fix_auth()

    if cfg_changes:
        print("Config changes:")
        for c in cfg_changes:
            print(f"  ✓ {c}")
    else:
        print("Config: no changes needed")

    if auth_removed:
        print(f"Auth: removed pools {auth_removed}")
    else:
        print("Auth: no bad pools")

    print("Restarting gateway...")
    restart_gateway()
    print("Done. Run audit_picker.py to verify.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
