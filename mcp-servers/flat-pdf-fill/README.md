# flat-pdf-fill MCP server

Fill **flat / scanned PDFs** (court forms, affidavits, service packets) by OCR-detecting
field labels and typewriter-overlaying values on the printed lines.

- **Free tier**: CPU-only (tesseract OCR). No GPU, no API keys, no credits.
- Runs as a stdio MCP server inside Hermes — tools appear as `mcp_flat_pdf_fill_*`.
- Future upgrade path: swap `core.ocr_lines` for a PaddleOCR/vision pass on a free Colab
  GPU for messy scans or batch jobs (see notes at bottom).

## Tools

| Tool | Purpose |
|---|---|
| `detect_fields(input_pdf, page=1)` | OCR the page, return detected labels + pixel boxes (verify before filling, or use as manual anchors) |
| `fill_flat_pdf(input_pdf, output_pdf, fields, page=1, dpi=300, font_size_px=0)` | Fill it. `fields` = `{"Label as printed": "value"}`. Returns placed/missing report |
| `make_test_form(output_pdf)` | Generate a synthetic flat (image-only) form for testing |

## Install / register

```bash
pip install -r /home/workspace/flat-pdf-fill/requirements.txt   # already present on Zo
```

Add to `/root/.hermes/config.yaml`:

```yaml
mcp_servers:
  flat_pdf_fill:
    command: python3
    args: [/home/workspace/flat-pdf-fill/server.py]
    timeout: 300
```

Then `/restart` the gateway. Verify: `hermes mcp test flat_pdf_fill`.

## Usage (once tools are live)

```
fill_flat_pdf(
  input_pdf="/home/workspace/cases/CaseA_scan.pdf",
  output_pdf="/home/workspace/cases/CaseA_filled.pdf",
  fields={"Name": "John Doe", "Address": "123 Main St", "Case No.": "FD-2026-123"}
)
```

Label matching is normalized (case/punctuation-insensitive). If a label isn't found,
it's reported in `missing` — run `detect_fields` first to see the exact OCR text and
use that as the key.

## Placement rules (from court-form-typewriter skill)

- Values go **ON the printed line** — baseline sits **above** the underscore (`raise_px=6` @300dpi) so letter bodies clear the stroke, nothing crossed out, nothing floating.
- Line detection is row-locked: a candidate underscore must sit in the label's own row band (±14px) **and start right after the label**. Box borders and full-width section rules begin at the left margin (before the label) and are **rejected** — verified against a trap form with both.
- **Never placed blindly:** if no line is confirmed for a field, the value is still placed (aligned with the label row) but the label is added to `needs_review` — so nothing ships as "random".
- **Explicit override:** pass `anchors={"Label": {"x": px, "baseline": px, "x_end": px}}` to place at exact coordinates (from `detect_fields` / `detect_lines`) when OCR is unreliable.
- Font size auto-matches the printed label height, shrinks to fit the line.
- Output PDF is image+overlay at correct physical page size (300dpi ≈ letter).
- Always verify: render the output at 300dpi and eyeball / pixel-check before sending to a court.

## GPU / Colab notes (future)

The current `ocr_lines()` is tesseract on CPU — free and fine for clean scans. For
messy scans or big batches, replace it with a PaddleOCR `PP-Structure` or a vision-LLM
pass run inside a free Colab session (via `colab-cli`), writing the detected boxes to
JSON; `fill_flat_pdf` already consumes `{text, x0,y0,x1,y1}` lines, so the switch is
drop-in.
