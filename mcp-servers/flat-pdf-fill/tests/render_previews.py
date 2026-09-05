#!/usr/bin/env python3
import fitz

for name in ("test_trap_filled.pdf", "test_filled.pdf"):
    doc = fitz.open(f"/home/workspace/flat-pdf-fill/tests/{name}")
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), alpha=False)
    out = f"/home/workspace/flat-pdf-fill/tests/{name.replace('.pdf', '')}_preview.png"
    pix.save(out)
    print("saved", out, pix.width, pix.height)
