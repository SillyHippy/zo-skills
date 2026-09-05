#!/usr/bin/env python3
"""Accurate disk report for Zo 9p hosts where df is inflated vs walkable trees."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Iterable

# Paths that are real host content (not shared platform volume over-count).
REAL_PATHS: list[tuple[str, str]] = [
    ("workspace", "/home/workspace"),
    ("zo_internal", "/home/.z"),
    ("root_home", "/root"),
    ("usr", "/usr"),
    ("var", "/var"),
    ("tmp", "/tmp"),
    ("opt", "/opt"),
    ("swapfile", "/swapfile"),
    ("substrate", "/__substrate"),
]

# Never walk these for quota — du over-counts shared platform mounts.
SKIP_DU_PATHS = (
    "/__modal/volumes",
    "/mnt/web_build",
    "/mnt/zo-tools",
    "/mnt/pub",
    "/mnt/cloud",
)


def run(cmd: str) -> str:
    return subprocess.check_output(
        cmd, shell=True, text=True, stderr=subprocess.DEVNULL
    ).strip()


def human_to_bytes(s: str) -> int:
    s = (s or "").strip()
    if not s or s in ("n/a", "-", "0"):
        return 0
    m = re.match(r"^([0-9]*\.?[0-9]+)\s*([KMGTPE]?)i?B?$", s, re.I)
    if not m:
        return 0
    n = float(m.group(1))
    u = (m.group(2) or "").upper()
    mult = {
        "": 1,
        "K": 1024,
        "M": 1024**2,
        "G": 1024**3,
        "T": 1024**4,
        "P": 1024**5,
        "E": 1024**6,
    }.get(u, 1)
    return int(n * mult)


def bytes_to_human(n: int) -> str:
    if n < 0:
        n = 0
    units = ["B", "K", "M", "G", "T", "P"]
    f = float(n)
    for u in units:
        if f < 1024 or u == units[-1]:
            if u == "B":
                return f"{int(f)}B"
            if f >= 100:
                return f"{f:.0f}{u}"
            if f >= 10:
                return f"{f:.1f}{u}".rstrip("0").rstrip(".") + u if False else f"{f:.1f}{u}"
            return f"{f:.1f}{u}"
        f /= 1024.0
    return f"{n}B"


def du_bytes(path: str) -> int:
    if not os.path.exists(path):
        return 0
    try:
        # -s summary, -x stay on one filesystem, -B1 bytes
        out = run(f"du -sx -B1 {path} 2>/dev/null")
        # format: "12345\t/path"
        first = out.split()[0]
        return int(first)
    except Exception:
        return 0


def parse_df(path: str = "/") -> dict:
    # Prefer portable df -k
    try:
        out = run(f"df -kP {path} | tail -1")
        parts = out.split()
        # Filesystem 1024-blocks Used Available Capacity Mounted
        size_k = int(parts[1])
        used_k = int(parts[2])
        avail_k = int(parts[3])
        pct = parts[4].rstrip("%")
        return {
            "size_b": size_k * 1024,
            "used_b": used_k * 1024,
            "avail_b": avail_k * 1024,
            "use_pct": float(pct),
            "mount": parts[5] if len(parts) > 5 else path,
            "raw": out,
        }
    except Exception as e:
        return {
            "size_b": 0,
            "used_b": 0,
            "avail_b": 0,
            "use_pct": 0.0,
            "mount": path,
            "raw": str(e),
        }


def collect() -> dict:
    parts: dict[str, int] = {}
    for name, path in REAL_PATHS:
        parts[name] = du_bytes(path)
    real_total = sum(parts.values())
    df = parse_df("/")
    # Modal platform storage lives behind separate 9p mounts; `du -x /__modal` won't
    # descend into them, so measure each mount point explicitly.
    modal_b = (
        du_bytes("/__modal/volumes")
        + du_bytes("/__modal/mounts")
        + du_bytes("/__modal/.bin")
        + du_bytes("/root/.modal")
    )
    gap = max(0, df["used_b"] - real_total)
    return {
        "parts_b": parts,
        "real_total_b": real_total,
        "df": df,
        "modal_b": modal_b,
        "gap_b": gap,
        "note": (
            "DF is the Zo 9p container view and includes opaque Modal/platform "
            "overhead (Modal volumes, daemons, runtime) that is NOT visible as "
            "walkable user files and does NOT count toward your quota. REAL is "
            "du of caller-owned trees and already excludes /__modal. Most of the "
            "opaque gap (DF used - REAL) is Modal platform storage. Do not treat "
            "DF alone as billable user files. Never du "
            + ", ".join(SKIP_DU_PATHS)
            + " for quota (over-count)."
        ),
    }


def one_liner(data: dict) -> str:
    real = bytes_to_human(data["real_total_b"])
    ws = bytes_to_human(data["parts_b"].get("workspace", 0))
    df_u = bytes_to_human(data["df"]["used_b"])
    df_s = bytes_to_human(data["df"]["size_b"])
    pct = data["df"]["use_pct"]
    gap = bytes_to_human(data["gap_b"])
    # Drop trailing .0 style already handled; keep compact
    pct_s = f"{pct:.0f}" if abs(pct - round(pct)) < 0.05 else f"{pct:.1f}"
    return (
        f"REAL {real} (workspace {ws}) | "
        f"DF {df_u}/{df_s} ({pct_s}%, gap {gap} opaque)"
    )


def full_text(data: dict) -> str:
    lines = [
        one_liner(data),
        "",
        "REAL breakdown:",
    ]
    for name, _path in REAL_PATHS:
        b = data["parts_b"].get(name, 0)
        if b <= 0:
            continue
        lines.append(f"  {name:12} {bytes_to_human(b):>8}  {_path}")
    lines.append(f"  {'TOTAL':12} {bytes_to_human(data['real_total_b']):>8}")
    lines.append("")
    lines.append(
        f"DF / : used {bytes_to_human(data['df']['used_b'])} / "
        f"{bytes_to_human(data['df']['size_b'])} "
        f"({data['df']['use_pct']:.1f}%), "
        f"avail {bytes_to_human(data['df']['avail_b'])}"
    )
    lines.append(
        f"Opaque gap (DF used − REAL): {bytes_to_human(data['gap_b'])}"
    )
    lines.append(
        f"Modal platform (NOT counted toward quota): "
        f"{bytes_to_human(data.get('modal_b', 0))}"
    )
    lines.append(data["note"])
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Accurate Zo disk usage report")
    p.add_argument("--full", action="store_true", help="Print breakdown")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument(
        "--alert-gb",
        type=float,
        default=None,
        help="Exit 2 if DF available GiB is at or below this threshold",
    )
    p.add_argument(
        "--one-line",
        action="store_true",
        help="Force one-liner (default without --full/--json)",
    )
    args = p.parse_args(list(argv) if argv is not None else None)

    data = collect()

    if args.json:
        out = {
            "one_liner": one_liner(data),
            "real_total": bytes_to_human(data["real_total_b"]),
            "real_total_b": data["real_total_b"],
            "parts": {k: bytes_to_human(v) for k, v in data["parts_b"].items()},
            "parts_b": data["parts_b"],
            "df_used": bytes_to_human(data["df"]["used_b"]),
            "df_size": bytes_to_human(data["df"]["size_b"]),
            "df_avail": bytes_to_human(data["df"]["avail_b"]),
            "df_use_pct": data["df"]["use_pct"],
            "gap": bytes_to_human(data["gap_b"]),
            "gap_b": data["gap_b"],            "modal": bytes_to_human(data["modal_b"]),
            "modal_b": data["modal_b"],
            "note": data["note"],
        }
        print(json.dumps(out, indent=2))
    elif args.full:
        print(full_text(data))
    else:
        print(one_liner(data))

    if args.alert_gb is not None:
        avail_g = data["df"]["avail_b"] / (1024**3)
        if avail_g <= args.alert_gb:
            print(
                f"ALERT: DF available {avail_g:.1f}G <= {args.alert_gb:g}G",
                file=sys.stderr,
            )
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
