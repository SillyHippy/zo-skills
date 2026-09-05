"""OmniRoute reverse-proxy slash commands for Hermes gateway/CLI.

Usage (Telegram / CLI):
  /omni update          — git upgrade to latest upstream release (default) + backup + re-pin BASE_PATH + production rebuild + restart + verify login
  /omni update nopull   — same, but skip the git upgrade (no pull)
  /omni update install  — same + npm install
  /omni update nopull install — skip git upgrade, do npm install
  /omni verify          — read-only health check (no restarts)
  /omni status          — quick status (supervisor + API + browser URL)
  /omni help            — this help

Never invent alternate update steps. Always use the scripts in
/home/workspace/Skills/omniroute-maintain/scripts/.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

UPDATE_SCRIPT = Path(
    "/home/workspace/Skills/omniroute-maintain/scripts/update-via-proxy.sh"
)
VERIFY_SCRIPT = Path(
    "/home/workspace/Skills/omniroute-maintain/scripts/verify.sh"
)
BROWSER_URL = "https://zo-reverse-proxy-sillyhippy.zocomputer.io/omniroute/"
API_URL = "http://127.0.0.1:20128/omniroute/v1"
SUPER = ["supervisorctl", "-s", "http://127.0.0.1:29011"]

_HELP = """\
**/omni** — OmniRoute behind zo-reverse-proxy

Commands:
• `/omni update` — idiot-proof update: git upgrade to latest upstream release → backup → re-pin BASE_PATH → production rebuild → restart → verify login
• `/omni update nopull` — skip the git upgrade (no pull)
• `/omni update install` — also `npm install`
• `/omni verify` — read-only checks (no restarts)
• `/omni status` — quick supervisor + API ping
• `/omni help` — this text

Skill (for agents): `omniroute-maintain`
Browser: {browser}
Hermes API (localhost only): `{api}`
""".format(
    browser=BROWSER_URL, api=API_URL
)


def _run(cmd: list[str], *, env: dict | None = None, timeout: int = 600) -> tuple[int, str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=merged,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") + (exc.stderr or "")
        return 124, f"TIMEOUT after {timeout}s\n{out}".strip()
    except Exception as exc:  # noqa: BLE001 — surface to Telegram
        return 1, f"ERROR: {exc}"
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, out


def _status() -> str:
    lines: list[str] = ["**OmniRoute status**"]
    rc, out = _run([*SUPER, "status", "omniroute"], timeout=30)
    lines.append(f"supervisor: `{out.strip() or ('exit ' + str(rc))}`")
    rc2, out2 = _run([*SUPER, "status", "zo-reverse-proxy"], timeout=30)
    lines.append(f"proxy: `{out2.strip() or ('exit ' + str(rc2))}`")
    code_rc, code = _run(
        [
            "curl",
            "-s",
            "-o",
            "/dev/null",
            "-m",
            "15",
            "-w",
            "%{http_code}",
            f"{API_URL}/models",
        ],
        timeout=30,
    )
    lines.append(f"API `{API_URL}/models` → HTTP `{code if code_rc == 0 else 'err'}`")
    proxy_rc, proxy_code = _run(
        [
            "curl",
            "-s",
            "-o",
            "/dev/null",
            "-m",
            "20",
            "-L",
            "-w",
            "%{http_code}",
            BROWSER_URL,
        ],
        timeout=40,
    )
    lines.append(
        f"browser `{BROWSER_URL}` → HTTP `{proxy_code if proxy_rc == 0 else 'err'}`"
    )
    lines.append("")
    lines.append("Update: `/omni update` · Verify: `/omni verify`")
    return "\n".join(lines)


def _verify() -> str:
    if not VERIFY_SCRIPT.is_file():
        return f"FAIL: missing verify script at `{VERIFY_SCRIPT}`"
    rc, out = _run(["bash", str(VERIFY_SCRIPT)], timeout=180)
    header = "✅ VERIFY PASSED" if rc == 0 else f"❌ VERIFY FAILED (exit {rc})"
    return f"{header}\n\n```\n{out}\n```"


def _update(raw_args: str) -> str:
    if not UPDATE_SCRIPT.is_file():
        return f"FAIL: missing update script at `{UPDATE_SCRIPT}`"
    tokens = raw_args.lower().split()
    env: dict[str, str] = {}
    if "nopull" in tokens:
        env["OMNIROUTE_GIT_PULL"] = "0"
    elif "pull" in tokens:
        env["OMNIROUTE_GIT_PULL"] = "1"
    if "install" in tokens:
        env["OMNIROUTE_NPM_INSTALL"] = "1"
    # Drop the leading "update" token if present (handler may receive full args)
    rc, out = _run(["bash", str(UPDATE_SCRIPT)], env=env, timeout=900)
    header = "✅ UPDATE PASSED" if rc == 0 else f"❌ UPDATE FAILED (exit {rc})"
    # Telegram has practical message size limits — keep last ~3500 chars of log
    if len(out) > 3500:
        out = "…(truncated)…\n" + out[-3500:]
    return f"{header}\n\n```\n{out}\n```\n\nBrowser: {BROWSER_URL}"


def _handle_slash(raw_args: str) -> str:
    args = (raw_args or "").strip()
    if not args or args.lower() in {"help", "-h", "--help"}:
        return _HELP
    parts = args.split(None, 1)
    sub = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""

    if sub == "status":
        return _status()
    if sub == "verify":
        return _verify()
    if sub == "update":
        return _update(rest)
    # Allow bare "/omni pull" typos? No — keep strict.
    return f"Unknown subcommand: `{sub}`\n\n{_HELP}"


def register(ctx) -> None:
    ctx.register_command(
        "omni",
        handler=_handle_slash,
        description="OmniRoute proxy update/verify (/omni update)",
        args_hint="[update|verify|status|help]",
    )
