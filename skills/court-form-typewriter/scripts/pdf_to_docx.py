#!/usr/bin/env python3
"""Convert a PDF page set to DOCX via pdf2docx for Word-based fill workflows."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("docx")
    args = ap.parse_args()
    try:
        from pdf2docx import Converter
    except ImportError:
        print("pdf2docx not installed: pip install pdf2docx", file=sys.stderr)
        return 2
    pdf = Path(args.pdf)
    docx = Path(args.docx)
    docx.parent.mkdir(parents=True, exist_ok=True)
    cv = Converter(str(pdf))
    cv.convert(str(docx))
    cv.close()
    print(f"wrote {docx} ({docx.stat().st_size // 1024}KB)")
    print("NOTE: always human-check layout; scanned forms often need typewriter path instead.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
