#!/usr/bin/env python3
"""Fill AcroForm, strip gray MK/BS, regenerate appearances, render-check.

Only use when source is true fillable AND pdftoppm shows values without gray bars.
Otherwise use typewriter_fill.py on the scanned twin.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz
import pikepdf
from PIL import Image


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--values", required=True, help="JSON {field: value, ...}")
    ap.add_argument("--checkboxes", default=None, help="JSON {field: 'Yes'|True, ...}")
    ap.add_argument("--out-filled", required=True, help="filled unflattened PDF")
    ap.add_argument("--out-flat-pdf", default=None, help="optional image-flattened PDF")
    ap.add_argument("--render-png", default=None)
    ap.add_argument("--dpi", type=int, default=200)
    args = ap.parse_args()

    vals = json.loads(Path(args.values).read_text())
    cbs = json.loads(Path(args.checkboxes).read_text()) if args.checkboxes else {}

    tmpdir = tempfile.mkdtemp(prefix="acro_")
    try:
        filled = Path(tmpdir) / "filled.pdf"
        stripped = Path(tmpdir) / "stripped.pdf"
        regen = Path(tmpdir) / "regen.pdf"

        shutil.copy2(args.source, filled)
        doc = fitz.open(filled)
        for pg in doc:
            for w in list(pg.widgets() or []):
                fn = w.field_name
                if fn in vals:
                    w.field_value = str(vals[fn])
                    w.update()
                elif fn in cbs:
                    v = cbs[fn]
                    w.field_value = "Yes" if v in (True, "Yes", "yes", 1, "1") else v
                    w.update()
        doc.save(str(Path(tmpdir) / "filled2.pdf"), garbage=3, deflate=True)
        doc.close()

        pdf = pikepdf.open(Path(tmpdir) / "filled2.pdf")
        n = 0
        for obj in pdf.objects:
            if isinstance(obj, pikepdf.Dictionary) and obj.get("/Subtype") == pikepdf.Name("/Widget"):
                for k in ("/MK", "/BS", "/AP"):
                    if k in obj:
                        del obj[k]
                        n += 1
        pdf.save(stripped)
        pdf.close()
        print(f"stripped {n} MK/BS/AP entries")

        doc = fitz.open(stripped)
        for pg in doc:
            for w in list(pg.widgets() or []):
                w.update()
        Path(args.out_filled).parent.mkdir(parents=True, exist_ok=True)
        doc.save(args.out_filled, garbage=3, deflate=True)
        doc.close()

        # render check
        rdir = Path(tmpdir) / "r"
        rdir.mkdir()
        subprocess.run(
            ["pdftoppm", "-r", str(args.dpi), "-png", args.out_filled, str(rdir / "p")],
            check=True,
            capture_output=True,
        )
        pngs = sorted(rdir.glob("p-*.png"))
        if not pngs:
            print("FAIL: pdftoppm produced no pages", file=sys.stderr)
            return 1
        if args.render_png:
            shutil.copy2(pngs[0], args.render_png)
            print(f"render {args.render_png}")
        if args.out_flat_pdf:
            images = [Image.open(p) for p in pngs]
            if len(images) == 1:
                images[0].save(args.out_flat_pdf, "PDF", resolution=args.dpi)
            else:
                images[0].save(
                    args.out_flat_pdf,
                    "PDF",
                    resolution=args.dpi,
                    save_all=True,
                    append_images=images[1:],
                )
            print(f"flat {args.out_flat_pdf}")
        print(f"filled {args.out_filled}")
        print("WARNING: always open render PNG — if values missing or gray remains, use typewriter path.")
        return 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
