#!/usr/bin/env python3
"""Deterministic repo/update check — reports stable updates vs installed."""

import json
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

SNAPSHOT = Path("/home/workspace/.github-release-versions.json")
UA = "ZoComputer-repo-update-check/1.0"

AUTO_APPLY_OK = {"9router", "QWEN-gate"}  # still require supervised apply — script never runs upgrades


def run(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


def gh_latest(repo: str) -> str:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    return (data.get("tag_name") or data.get("name") or "").strip()


def pypi_latest(package: str) -> str:
    url = f"https://pypi.org/pypi/{package}/json"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    return data["info"]["version"].strip()


def norm_ver(v: str) -> str:
    v = (v or "").strip()
    if v.startswith("v"):
        v = v[1:]
    return v


def is_stable_release(version: str) -> bool:
    low = (version or "").lower()
    bad = ("nightly", "alpha", "beta", "rc", "pre", "dev")
    return not any(b in low for b in bad)


def parse_parts(v: str):
    v = norm_ver(v)
    parts = []
    for chunk in re.split(r"[.\-+]", v):
        if chunk.isdigit():
            parts.append(int(chunk))
        elif chunk:
            parts.append(chunk)
    return parts


def version_behind(installed: str, latest: str) -> bool:
    if not installed or not latest:
        return False
    if norm_ver(installed) == norm_ver(latest):
        return False
    a, b = parse_parts(installed), parse_parts(latest)
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else 0
        y = b[i] if i < len(b) else 0
        if isinstance(x, int) and isinstance(y, int):
            if x < y:
                return True
            if x > y:
                return False
        else:
            if str(x) != str(y):
                return str(x) < str(y)
    return False


def base_tag_from_describe(describe: str) -> str:
    """git describe like v0.8.0-2-gabc -> v0.8.0 for compare to release tag."""
    if not describe:
        return ""
    m = re.match(r"^(v?[0-9]+(?:\.[0-9]+)*(?:\.[0-9]+)?)", describe)
    return m.group(1) if m else describe.split("-")[0]


def hermes_installed() -> tuple[str, bool]:
    p = Path("/usr/local/lib/hermes-agent")
    if not p.is_dir():
        return "", False
    out = run(f"cd {p} && git describe --tags --always 2>/dev/null")
    return out or "unknown", True


def qwen_installed() -> tuple[str, bool]:
    p = Path("/home/workspace/Projects/qwen-gate")
    if not p.is_dir():
        return "", False
    out = run(f"cd {p} && git describe --tags --always 2>/dev/null")
    return out or "unknown", True


def router_installed() -> tuple[str, bool]:
    p = Path("/home/workspace/Projects/9router-fresh")
    if not p.is_dir():
        return "", False
    out = run(f"cd {p} && git describe --tags --always 2>/dev/null")
    return out or "unknown", True


def mem0_installed() -> tuple[str, bool]:
    out = run("python3 -m pip show mem0ai 2>/dev/null | awk -F': ' '/^Version:/{print $2}'")
    return (out or "", bool(out))


def item_status(name: str, installed: str, latest: str, install_ok: bool, **extra) -> dict:
    today = date.today().isoformat()
    stable = is_stable_release(latest)
    compare_inst = base_tag_from_describe(installed) if "-" in installed and name in ("Hermes", "QWEN-gate", "9router") else installed
    behind = install_ok and stable and version_behind(compare_inst, latest)
    status = "update available (stable)" if behind else "current"
    if not install_ok:
        status = "install problem"
    elif not stable:
        status = "current (upstream not stable tag)"
    rec = {
        "installed_version": installed,
        "upstream_latest": latest,
        "install_ok": install_ok,
        "checked_at": today,
        "stable_latest": stable,
        "update_available": behind,
        "status": status,
        "auto_apply_ok": name in AUTO_APPLY_OK and behind,
        "auto_apply_note": "manual/supervised only — automation does not upgrade",
        **extra,
    }
    return rec


def main():
    items = {}

    h_inst, h_ok = hermes_installed()
    h_latest = gh_latest("NousResearch/hermes-agent")
    items["Hermes"] = item_status(
        "Hermes", h_inst, h_latest, h_ok,
        release_url="https://github.com/NousResearch/hermes-agent/releases/latest",
        install_path="/usr/local/lib/hermes-agent",
        note="Custom build common — update_available is informational only",
    )

    q_inst, q_ok = qwen_installed()
    q_latest = gh_latest("youssefvdel/qwen-gate")
    items["QWEN-gate"] = item_status(
        "QWEN-gate", q_inst, q_latest, q_ok,
        release_url="https://github.com/youssefvdel/qwen-gate/releases/latest",
        install_path="/home/workspace/Projects/qwen-gate",
        note="Never track QwenLM/qwen-code",
    )

    r_inst, r_ok = router_installed()
    r_latest = gh_latest("decolua/9router")
    items["9router"] = item_status(
        "9router", r_inst, r_latest, r_ok,
        release_url="https://github.com/decolua/9router/releases/latest",
        install_path="/home/workspace/Projects/9router-fresh",
    )

    m_inst, m_ok = mem0_installed()
    m_latest = pypi_latest("mem0ai")
    items["mem0"] = item_status(
        "mem0", m_inst, m_latest, m_ok,
        release_url="https://pypi.org/project/mem0ai/",
        install_path="pip package mem0ai",
        note="PyPI bump — apply only if you want (pip install -U mem0ai)",
    )

    SNAPSHOT.write_text(json.dumps(items, indent=2) + "\n")

    any_available = any(it.get("update_available") for it in items.values())
    lines = []
    for name in ("Hermes", "QWEN-gate", "9router", "mem0"):
        it = items[name]
        lines.append(
            f"{name}: {it['status']} — installed {it['installed_version']} | upstream {it['upstream_latest']}"
        )

    should_notify = any_available
    telegram_message = ""
    if should_notify:
        telegram_message = "Stable updates available (not auto-applied):\n" + "\n".join(
            ln for ln in lines if "update available" in ln
        )
        if not telegram_message.strip().endswith("available"):
            telegram_message += "\n\nAll items:\n" + "\n".join(lines)
    else:
        telegram_message = ""  # silent when nothing available

    out = {
        "should_notify": should_notify,
        "telegram_message": telegram_message,
        "items": items,
        "snapshot": str(SNAPSHOT),
        "policy": "Notify only when stable update_available. No unattended upgrades.",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        err = {
            "should_notify": True,
            "telegram_message": f"Repo check script failed: {e}",
            "items": {},
            "snapshot": str(SNAPSHOT),
        }
        print(json.dumps(err, indent=2))
        sys.exit(1)