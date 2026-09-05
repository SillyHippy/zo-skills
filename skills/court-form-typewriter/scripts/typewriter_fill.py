#!/usr/bin/env python3
"""Typewriter-fill a blank court form PNG and save print-ready PDF.

fields.json format:
{
  "fields": [
    {"name": "plaintiff", "text": "DAKOTA FRAZIER", "x": 750, "line_y": 524},
    ...
  ],
  "font_path": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",  // optional
  "font_size": 48,
  "raise_px": 6
}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-png", required=True)
    ap.add_argument("--fields", required=True, help="JSON with fields list")
    ap.add_argument("--lines", default=None, help="optional detect_lines.json (unused if x/line_y set)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--font-size", type=int, default=None)
    ap.add_argument("--raise-px", type=int, default=None)
    ap.add_argument("--preview-png", default=None)
    args = ap.parse_args()

    cfg = json.loads(Path(args.fields).read_text())
    fields = cfg["fields"]
    font_size = args.font_size or cfg.get("font_size", 48)
    raise_px = args.raise_px if args.raise_px is not None else cfg.get("raise_px", 6)
    font_path = cfg.get(
        "font_path",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    )
    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError:
        font = ImageFont.load_default()

    img = Image.open(args.source_png).convert("RGB")
    draw = ImageDraw.Draw(img)

    for f in fields:
        text = f.get("text") or ""
        if not text:
            continue  # blank execution field
        x = int(f["x"])
        line_y = int(f["line_y"])
        # baseline above the printed underscore so letters are not crossed out
        draw.text((x, line_y - raise_px), text, fill=(0, 0, 0), font=font, anchor="ls")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PDF", resolution=args.dpi)

    preview = args.preview_png or str(out.with_suffix("")) + f"_{args.dpi}.png"
    img.save(preview)
    print(f"saved {out} ({out.stat().st_size // 1024}KB) raise_px={raise_px} font={font_size}")
    print(f"preview {preview}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
