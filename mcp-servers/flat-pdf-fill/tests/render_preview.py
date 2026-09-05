#!/usr/bin/env python3
import fitz

doc = fitz.open("/home/workspace/flat-pdf-fill/tests/test_filled.pdf")
pix = doc[0].get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), alpha=False)
pix.save("/home/workspace/flat-pdf-fill/tests/test_filled_preview.png")
print("preview saved", pix.width, pix.height, "pages:", doc.page_count)
