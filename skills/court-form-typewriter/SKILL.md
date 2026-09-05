---
name: court-form-typewriter
description: "Use when filling flattened/scanned court PDFs or official blank forms so typed values sit on printed lines without gray boxes, cross-outs, or rotation errors. Typewriter overlay + 300 DPI pixel verification; optional Word recreate path."
---

# Court Form Typewriter

## When to use

- Official court PDFs that are **scanned / flattened / image-based** (no reliable AcroForm appearance)
- User requires text **on the blank lines**, not floating and **not crossed through** by the underscore
- Prior fillable-widget fills produced **gray bars**, wrong rotation, or values lost on flatten
- Multi-page divorce / family packets (Pro Se, Pauper’s, UCCJEA, Waiver, Summons, Jurisdictional, etc.)

## Hard rules (never violate)

1. **One form at a time.** Perfect page 1 before multi-page forms.
2. **Fill blanks only.** Never erase, whiteout, or cover printed legal text (`Petitioner/Respondent (circle one)`, statutes, clerk language).
3. **Leave execution blank:** signatures, notary, dates-to-sign, judge/clerk-only fields (unless user explicitly provides them).
4. **No gray widget backgrounds.** Do not deliver unflattened fillable PDFs with `MK BG/BC` gray bars to mobile viewers.
5. **Never claim complete** until 300 DPI render + field crops + pixel checks pass. Vision alone is not enough.
6. **Unique deliverable names** when re-sending (avoid phone PDF cache): append `_vN` or timestamp.
7. **Rotation:** if source `page.rotation != 0`, always render with `pdftoppm` (respects rotation) before measuring/drawing. Output final PDF must be upright portrait for letter forms unless the official form is truly landscape content.

## Preferred pipeline (flattened / scanned official forms)

### A. Typewriter overlay (default — best for Tulsa/OK scanned blanks)

```bash
# 1) Render blank official page at 300 DPI (rotation-safe)
pdftoppm -r 300 -png SOURCE.pdf /tmp/form_src

# 2) Detect underscore Y positions + label X ends
python3 scripts/detect_lines.py /tmp/form_src-1.png --out /tmp/lines.json

# 3) Place text with baseline ABOVE the line (not through letters)
python3 scripts/typewriter_fill.py \
  --source-png /tmp/form_src-1.png \
  --fields /path/to/fields.json \
  --lines /tmp/lines.json \
  --out /path/to/OUT.pdf \
  --dpi 300 --font-size 48 --raise-px 6

# 4) Mandatory verification (must exit 0)
python3 scripts/verify_on_line.py --filled-png /tmp/OUT_300.png --source-png /tmp/form_src-1.png --fields /path/to/fields.json
```

**Placement law (learned the hard way):**

- Use PIL `draw.text(..., anchor='ls')` so `y` is the **baseline**.
- Set baseline to `line_y - raise_px` with `raise_px` default **6** at 300 DPI so letter bodies clear the stroke.
- Pixel gate: `added_on_line < 80` vs blank source, and substantial dark mass **above** the line.
- Font: DejaVu Serif or Liberation Serif ~13pt → **~48px at 300 DPI** (match printed label height via OCR).

### B. True AcroForm fillable (only if source has real widgets AND no baked gray)

1. Fill with pymupdf / fillpdf using **form-specific** field dicts (never one shared dict across form types).
2. Strip widget gray: remove `/MK` (BG/BC), `/BS`, regenerate `/AP` via `widget.update()`.
3. Flatten only after visual proof values appear: `pdftoppm` render of filled file.
4. If caption values vanish on render → **abandon widgets**, use pipeline A on the non-fillable scan twin.

### C. Word recreate (when user wants editable DOCX match)

```bash
# PDF → DOCX (layout approx; always human-check)
python3 scripts/pdf_to_docx.py SOURCE.pdf /tmp/form.docx

# Edit/fill with python-docx OR LibreOffice, then:
soffice --headless --convert-to pdf --outdir /tmp /tmp/form_filled.docx
# Then run verify_on_line on the exported PDF render
```

Use Word path for **born-digital** text forms. For **scanned** court images, typewriter (A) wins.

## Verification checklist (every page)

Run `scripts/verify_on_line.py` and confirm:

| Check | Pass criteria |
|--------|----------------|
| Orientation | Final page upright; `rotation=0` after flatten; width < height for letter portrait |
| No added margin vertical text | Left/right 0.2" margins match source dark-pixel count (±tolerance) |
| No gray boxes | Empty corners gray≈0; no solid mid-gray rectangles over fields |
| On-line, not crossed out | Text mass above line; `added_on_line` near 0 |
| Values correct | OCR or known string present in field crop |
| Signature/notary blank | No added dark mass in execution zones |
| Printed text intact | Diff vs source only in intended field bands |

**Also** crop each field and open crops with `vision_analyze`, but **pixel script is the gate**. If vision and pixels disagree, trust pixels + send unique file to user.

## Failure modes already burned

| Symptom | Cause | Fix |
|---------|--------|-----|
| Gray bars on phone | Fillable `MK BG[.96.96.96]` | Don’t ship widgets; typewriter on scan |
| Values blank after flatten | `get_pixmap`/pdftoppm dropped appearances | Typewriter, or strip+regen AP then verify render |
| Text “crossed out” | Baseline on/below underscore | `anchor='ls'`, `raise_px=6+` |
| Landscape / vertical margin names | Source `/Rotate 270` mishandled | Always `pdftoppm` first; draw on upright raster |
| Wrong utility $ got phone # | Shared field name dict across forms | Per-form field maps only |
| User sees old PDF | Telegram/cache | New filename every deliverable |

## Oklahoma divorce packet notes

- Sources often live under `/root/.hermes/cache/documents/` (`*_FILLABLE.pdf` and scanned twins like `tulsa_FormsProSeEntryofAppeance.pdf`).
- Pro Se scan is portrait media box with **rotation 270** — treat as upright after pdftoppm.
- Preserve `Petitioner/Respondent (circle one)`; leave physical circle to parties.
- Case number may stay `FD-____________` until clerk assigns.
- Do not promise court acceptance; maximize legibility and blank integrity.

## Scripts in this skill

| Script | Purpose |
|--------|---------|
| `scripts/detect_lines.py` | Find underscore Y and label ends via dark runs + OCR |
| `scripts/typewriter_fill.py` | Overlay fields onto blank 300 DPI page → PDF |
| `scripts/verify_on_line.py` | Pixel gates; exit 1 on any fail |
| `scripts/pdf_to_docx.py` | pdf2docx wrapper |
| `scripts/fill_acroform_clean.py` | Optional AcroForm fill + strip gray + render check |

## One-page success gate (user standard)

> Put the words **on the lines** and **not crossed out**.

Only after that passes for one page, proceed to 3–4 page forms using the same scripts and gates.
