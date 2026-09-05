# Field Sheet Generation — Speed Analysis

## Current Pipeline Bottleneck Breakdown

| Step | Time (ms) | Notes |
|------|-----------|-------|
| Python process startup | ~40 | sys module loading, interpreter init |
| PyMuPDF (fitz) import | ~70 | Only needed for PDF text extraction |
| pdf2image import | ~1 | Only needed for OCR |
| pytesseract import | ~5 | Only needed for OCR |
| jinja2 import | ~21 | Template rendering |
| **weasyprint import** | **~983** | **72% of total cold time** |
| PDF text extraction (pdftotext) | ~18 | Per PDF, subprocess call |
| Regex extraction | ~0 | Negligible |
| Template fill + HTML write | ~5 | String operations |
| PDF render (weasyprint) | ~295 | CSS parsing + layout + output |
| **TOTAL cold process** | **~1360** | End-to-end, fresh Python |
| TOTAL warm (cached) | ~370 | Imports already in memory |

## The Problem

**weasyprint dominates at 983ms cold import.** Even the warm render (295ms) is slow because it must parse CSS, build a formatting tree, and rasterize layout for every call.

The current script (`scripts/generate_field_sheet.py`) imports weasyprint unconditionally, imports PyMuPDF unconditionally, and imports OCR libraries unconditionally. Every run pays the full cold cost.

## Fastest Possible Pipeline: Target < 3 seconds

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐     ┌─────────────┐
│  Email PDF  │────▶│  pdftotext   │────▶│   Regex    │────▶│  ReportLab  │
│  (text)     │     │  (subproc)   │     │  (one pass)│     │   PDF gen   │
└─────────────┘     └──────────────┘     └────────────┘     └─────────────┘
       ~0ms                ~18ms               ~0ms               ~7ms
                                                                   
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│ Petition    │────▶│  pdftotext   │────▶│   Merge    │
│ PDF (text)  │     │  page 1 only │     │  missing   │
└─────────────┘     └──────────────┘     │  fields    │
       ~0ms                ~18ms          └────────────┘
                                               
┌─────────────┐ (fallback only)
│ Scanned PDF │────▶ PyMuPDF + Tesseract OCR ──▶ Merge
└─────────────┘        ~2000-5000ms
```

### Timing Budget (text PDFs, no OCR)

| Component | Cold | Warm |
|-----------|------|------|
| Python startup | 40ms | 0ms |
| pdftotext × 2 | 36ms | 36ms |
| Regex (one pass, all patterns) | 1ms | 1ms |
| reportlab import | 238ms | 0ms |
| PDF layout + render | 7ms | 7ms |
| **TOTAL** | **~322ms** | **~44ms** |

With a persistent daemon (imports cached, only stdin/stdout): **< 100ms per request.**

### Timing Budget (scanned PDF, OCR needed)

| Component | Time |
|-----------|------|
| Everything above | ~322ms |
| PyMuPDF import | 70ms |
| pdf2image → PNG conversion (1 page, 200dpi) | ~800ms |
| Tesseract OCR (1 page) | ~1000ms |
| **TOTAL** | **~2200ms** |

Still well under 10 seconds.

## Key Changes from Current Code

### 1. Replace weasyprint → reportlab

| Metric | weasyprint | reportlab |
|--------|-----------|-----------|
| Cold import | 983ms | 238ms |
| Warm render | 295ms | 7ms |
| Full cold process | 1360ms | 282ms |
| PDF size | ~18KB | ~3KB |
| CSS dependency | Full CSS parser | Programmatic layout |

**Savings: ~1080ms cold, ~288ms warm per request.**

### 2. Replace PyMuPDF → pdftotext for text PDFs

- pdftotext is a C binary, 16ms process overhead, 18ms extraction
- PyMuPDF requires 70ms Python import
- Only fall back to PyMuPDF when pdftotext returns < 20 chars (scanned PDF)

**Savings: ~70ms cold per request (when text PDF).**

### 3. Lazy imports

- Don't import weasyprint, PyMuPDF, pdf2image, or jinja2 at module level
- Only import reportlab (needed for every run)
- Import OCR libs only when pdftotext fails

### 4. Single-pass regex

- Compile all regex patterns once at module load (not per field)
- Run against extracted text once, populate dict
- No multiple passes, no sequential field-by-field scanning

### 5. Skip HTML intermediate

- Current: regex → dict → HTML file → weasyprint → PDF (3 steps)
- Fast: regex → dict → reportlab PDF directly (2 steps)
- Eliminates HTML serialization, file I/O, CSS parsing

## Code Structure

See `scripts/ultra_fast_field_sheet.py` for the implementation.

## Daemon Mode (Optional, for < 100ms)

For maximum speed, keep a persistent Python process with reportlab imported:

```
stdin:  {"email_pdf": "/path/to/email.pdf", "petition_pdf": "/path/to/pet.pdf"}
stdout: {"pdf_path": "/output/CJ-2026-123.pdf", "extracted": {...}}
```

The daemon process:
1. Starts once, imports reportlab (238ms one-time cost)
2. Listens on stdin for JSON requests
3. Runs pdftotext subprocess + regex + reportlab render (~44ms per request)
4. Returns PDF path on stdout

Total: **< 100ms per field sheet** after initial daemon startup.
