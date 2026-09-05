---
name: pdf-form-filler
description: Fill flattened/image-based PDF forms using PIL image compositing. Works in pixel space for precise field placement.
version: 1.0.0
---

# PDF Form Filler (Image Compositing)

For flattened/image-based PDFs where pymupdf text insertion misses field positions.

## Approach: Render → OCR → Composite → Save

1. **Render** PDF pages at 4x resolution (2448×3168 for letter)
2. **OCR** with pytesseract to get exact bounding boxes
3. **Find blanks** by locating gaps between text on same line
4. **Composite** text using PIL at exact pixel positions
5. **Save** composited image as PDF

## Key Advantage
Works in pixel space (not PDF points), so positioning is exact.

## Pitfalls
- pytesseract bounding boxes have ~2-5px noise at 4x render
- Small text (6-7pt) may need manual coordinate adjustment
- Always verify output with vision_analyze after filling
