#!/usr/bin/env python3
"""Pixel verification: text on lines, not crossed out, no added margin junk.

Exit 0 only if all gates pass.
fields.json same as typewriter_fill.py; optional signature zones:
  "blank_zones": [{"name":"signature","x1":..,"y1":..,"x2":..,"y2":..,"max_added":100}]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--filled-png", required=True)
    ap.add_argument("--source-png", required=True)
    ap.add_argument("--fields", required=True)
    ap.add_argument("--raise-px", type=int, default=6)
    ap.add_argument("--margin", type=int, default=60)
    args = ap.parse_args()

    cfg = json.loads(Path(args.fields).read_text())
    fields = cfg["fields"]
    filled = np.array(Image.open(args.filled_png).convert("L"))
    source = np.array(Image.open(args.source_png).convert("L"))
    if filled.shape != source.shape:
        print(f"FAIL size mismatch filled={filled.shape} source={source.shape}")
        return 1

    h, w = filled.shape
    fails = []

    # margins: added dark must be near-zero
    for side, sl in (
        ("left", (slice(None), slice(0, args.margin))),
        ("right", (slice(None), slice(w - args.margin, w))),
    ):
        f_d = (filled[sl] < 100).sum()
        s_d = (source[sl] < 100).sum()
        added = int(f_d - s_d)
        print(f"margin_{side}: source_dark={s_d} filled_dark={f_d} added={added}")
        if added > 200:
            fails.append(f"margin_{side}_added={added}")

    # orientation proxy
    print(f"size: {w}x{h} portrait={w < h}")
    if w >= h:
        fails.append("not_portrait")

    # per-field on-line check
    for f in fields:
        name = f.get("name", "?")
        text = f.get("text") or ""
        if not text:
            continue
        line_y = int(f["line_y"])
        x = int(f["x"])
        # estimate text width ~ 0.55 * font_size * len
        font_size = cfg.get("font_size", 48)
        tw = int(max(200, min(w - x - 10, 0.55 * font_size * len(text) + 40)))
        x1, x2 = x, min(w - 1, x + tw)
        baseline = line_y - args.raise_px
        above = filled[max(0, baseline - 45) : max(0, baseline - 2), x1:x2]
        above_dark = int((above < 80).sum())
        # ink on line that wasn't on source line
        fl = filled[line_y - 1 : line_y + 2, x1:x2] < 80
        sl = source[line_y - 1 : line_y + 2, x1:x2] < 80
        added_on_line = int((fl & ~sl).sum())
        ok = above_dark > 200 and added_on_line < 80
        status = "PASS" if ok else "FAIL"
        print(f"{name}: above={above_dark} added_on_line={added_on_line} -> {status}")
        if not ok:
            fails.append(name)

    for z in cfg.get("blank_zones") or []:
        x1, y1, x2, y2 = int(z["x1"]), int(z["y1"]), int(z["x2"]), int(z["y2"])
        fl = filled[y1:y2, x1:x2] < 100
        sl = source[y1:y2, x1:x2] < 100
        added = int((fl & ~sl).sum())
        max_added = int(z.get("max_added", 100))
        ok = added <= max_added
        print(f"blank_zone {z.get('name','?')}: added={added} max={max_added} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            fails.append(f"blank:{z.get('name')}")

    if fails:
        print(f"FAILED: {fails}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
