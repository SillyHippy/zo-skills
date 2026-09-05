#!/usr/bin/env python3
"""Modal-on-Zo preflight — run before modal volume/deploy actions."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = Path("/home/workspace")
EXPORTS = WORKSPACE / "Projects" / "modal-exports"
FORBIDDEN_PREFIXES = ("/__modal", "/mnt/web_build", "/mnt/zo-tools")

ZO_INJECTED_PREFIX = "ak-uIGIJ"


def run(cmd: list[str], timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()
    except FileNotFoundError:
        return 127, f"not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def main() -> int:
    ok = True
    print("=== Modal on Zo preflight ===\n")

    # Modal CLI
    code, out = run(["modal", "--version"])
    if code != 0:
        print("[FAIL] Modal CLI not available:", out)
        ok = False
    else:
        print("[OK] Modal CLI:", out.split("\n")[0] if out else "ok")

    # Profile
    code, out = run(["modal", "profile", "current"])
    if code == 0 and out:
        print("[OK] Active profile:\n", out[:500])
    else:
        print("[WARN] Could not read modal profile current:", out or code)

    # Zo-injected token warning
    tid = os.environ.get("MODAL_TOKEN_ID", "")
    if tid.startswith(ZO_INJECTED_PREFIX):
        print(
            "[INFO] MODAL_TOKEN_ID looks Zo-injected (platform). "
            "Use ~/.modal.toml profile for user volume ops."
        )

    # Volume list
    code, out = run(["modal", "volume", "list"])
    if code == 0:
        # Empty table has no volume name rows (only box chars and headers)
        has_named_volume = any(
            ln.strip()
            and not ln.strip().startswith(("┃", "┡", "└", "┏", "Name", "Created"))
            and "━━━━" not in ln
            for ln in out.splitlines()
        )
        if not has_named_volume:
            print("[OK] modal volume list: no user volumes")
        else:
            print("[WARN] modal volume list has entries — confirm names are user-owned:\n", out[:800])
    else:
        print("[WARN] modal volume list failed:", out[:300])

    # Stale host mounts
    modal_vol = Path("/__modal/volumes")
    if modal_vol.is_dir():
        code, out = run(["du", "-sh", str(modal_vol)], timeout=120)
        size = out.split()[0] if code == 0 and out else "?"
        print(f"[INFO] /__modal/volumes total ~{size} (platform/stale — not user-deletable here)")

    # Export dir
    EXPORTS.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Export dir ready: {EXPORTS}")

    print("\n--- Rules reminder ---")
    for p in FORBIDDEN_PREFIXES:
        print(f"  Do NOT persist or rm under {p}")
    print("  DO use /home/workspace for Zo-owned files")
    print(f"  Checklist: {SKILL_ROOT / 'references' / 'checklist.md'}")

    if not ok:
        print("\n[PREFLIGHT FAILED] Fix failures before Modal deploy/volume create.")
        return 1
    print("\n[PREFLIGHT OK] Proceed only if user requested Modal; follow SKILL.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())