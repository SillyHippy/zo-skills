#!/usr/bin/env python3
"""Detect underscore line Y positions and label right-edges on a 300 DPI form PNG."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None


def find_underscore_rows(arr: np.ndarray, min_run: int = 150, min_dark: int = 200) -> list[dict]:
    """Return candidate horizontal underscore lines as {y, x_start, x_end, dark}."""
    h, w = arr.shape
    lines = []
    dark_count = (arr < 100).sum(axis=1)
    for y in range(h):
        if dark_count[y] < min_dark:
            continue
        row = arr[y] < 100
        max_run = cur = 0
        start = max_start = 0
        for x, v in enumerate(row):
            if v:
                if cur == 0:
                    start = x
                cur += 1
                if cur > max_run:
                    max_run = cur
                    max_start = start
            else:
                cur = 0
        if max_run < min_run:
            continue
        # prefer thin lines (not thick text bars): next few rows lighter
        if y + 3 < h and dark_count[y + 1] > dark_count[y] * 0.85:
            # might be middle of thick stroke; keep peak only
            if y > 0 and dark_count[y] < dark_count[y - 1]:
                continue
        dark_x = np.where(row)[0]
        lines.append(
            {
                "y": int(y),
                "x_start": int(dark_x[0]),
                "x_end": int(dark_x[-1]),
                "width": int(dark_x[-1] - dark_x[0]),
                "dark": int(dark_count[y]),
            }
        )
    # cluster nearby y into single line (take darkest in ±2)
    if not lines:
        return []
    clustered = []
    used = set()
    for i, ln in enumerate(lines):
        if i in used:
            continue
        group = [ln]
        used.add(i)
        for j in range(i + 1, len(lines)):
            if j in used:
                continue
            if abs(lines[j]["y"] - ln["y"]) <= 2:
                group.append(lines[j])
                used.add(j)
        best = max(group, key=lambda g: g["dark"])
        clustered.append(best)
    return clustered


def ocr_labels(img: Image.Image) -> list[dict]:
    if pytesseract is None:
        return []
    data = pytesseract.image_to_data(img, lang="eng", config="--psm 6", output_type=pytesseract.Output.DICT)
    words = []
    for i, t in enumerate(data["text"]):
        t = (t or "").strip()
        if not t:
            continue
        words.append(
            {
                "text": t,
                "x": int(data["left"][i]),
                "y": int(data["top"][i]),
                "x2": int(data["left"][i] + data["width"][i]),
                "y2": int(data["top"][i] + data["height"][i]),
                "h": int(data["height"][i]),
            }
        )
    return words


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("png")
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-run", type=int, default=150)
    args = ap.parse_args()

    img = Image.open(args.png).convert("RGB")
    arr = np.array(img.convert("L"))
    lines = find_underscore_rows(arr, min_run=args.min_run)
    words = ocr_labels(img)

    out = {
        "png": str(Path(args.png).resolve()),
        "size": list(img.size),
        "dpi_assumed": 300,
        "lines": lines,
        "labels": words,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"lines={len(lines)} labels={len(words)} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
