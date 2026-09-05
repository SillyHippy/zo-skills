#!/usr/bin/env python3
"""Core logic for filling flat/scanned PDFs via OCR + typewriter overlay.

Free-tier, CPU-only (tesseract). GPU optional later via Colab/PaddleOCR.

PLACEMENT LAW (never violate):
- Values go ON the printed line: baseline sits `raise_px` ABOVE the underscore stroke
  so letter bodies clear the line (nothing crossed out, nothing floating).
- The fill line is found by pixel run detection in the LABEL'S OWN ROW BAND — we
  reject full-width borders, section rules, and lines that belong to other rows,
  so values never land "random".
- If no line is found for a field, the value is flagged `needs_review` instead of
  being placed blindly.
"""
import os
import re

import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageDraw, ImageFont

DEFAULT_DPI = 300
RAISE_PX = 6  # baseline sits this many px above the underscore at 300dpi
MIN_RUN_PX = 50  # minimum underscore length to trust at 300dpi
MAX_START_GAP_PX = 350  # fill line must start within this many px right of the label
MAX_RUN_FRAC = 0.6  # reject runs longer than 60% of page width (borders/rules)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
]


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def _load_font(size_px):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size_px)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size_px)
    except TypeError:
        return ImageFont.load_default()


def render_page_png(pdf_path, page=0, dpi=DEFAULT_DPI, out_png=None):
    """Render one page of a PDF to PNG at `dpi`. Honors /Rotate. Returns (png_path, width_px, height_px)."""
    doc = fitz.open(pdf_path)
    try:
        pg = doc[page]
        zoom = dpi / 72.0
        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        if out_png is None:
            base = os.path.splitext(pdf_path)[0]
            out_png = f"{base}.p{page + 1}.{dpi}dpi.png"
        pix.save(out_png)
        return out_png, pix.width, pix.height
    finally:
        doc.close()


def png_to_pdf(png_path, out_pdf, dpi=DEFAULT_DPI):
    """Wrap a PNG back into a PDF at the correct physical page size (points)."""
    img = Image.open(png_path)
    w_pt = img.width * 72.0 / dpi
    h_pt = img.height * 72.0 / dpi
    doc = fitz.open()
    try:
        page = doc.new_page(width=w_pt, height=h_pt)
        page.insert_image(fitz.Rect(0, 0, w_pt, h_pt), filename=png_path)
        doc.save(out_pdf)
    finally:
        doc.close()


def ocr_lines(png_path, lang="eng"):
    """OCR a page image. Returns list of line dicts: text, x0,y0,x1,y1, baseline, words."""
    img = Image.open(png_path)
    data = pytesseract.image_to_data(img, lang=lang, config="--psm 11",
                                     output_type=pytesseract.Output.DICT)
    groups = {}
    n = len(data["text"])
    for i in range(n):
        txt = (data["text"][i] or "").strip()
        if not txt:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        word = {"text": txt, "x": int(data["left"][i]), "y": int(data["top"][i]),
                "w": int(data["width"][i]), "h": int(data["height"][i])}
        groups.setdefault(key, []).append(word)
    out = []
    for words in groups.values():
        words.sort(key=lambda w: w["x"])
        text = " ".join(w["text"] for w in words)
        x0 = min(w["x"] for w in words)
        y0 = min(w["y"] for w in words)
        x1 = max(w["x"] + w["w"] for w in words)
        y1 = max(w["y"] + w["h"] for w in words)
        h = y1 - y0
        out.append({
            "text": text, "words": words,
            "x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "baseline": y1 - int(h * 0.2),
        })
    return out


def find_label_line(label, lines):
    """Best-matching OCR line for a label. Returns line dict or None."""
    n = _norm(label)
    if not n:
        return None
    best, best_score = None, 0.0
    for ln in lines:
        ln_n = _norm(ln["text"])
        if not ln_n:
            continue
        if ln_n.startswith(n) or n in ln_n:
            score = len(n) / max(len(ln_n), 1)
            if score > best_score:
                best, best_score = ln, score
    return best


def label_end_x(line, label):
    """X of the right edge of the label text within the OCR line."""
    n = _norm(label)
    if not n:
        return line["x1"]
    acc = ""
    last_x = line["x0"]
    for w in line["words"]:
        wn = _norm(w["text"])
        if not wn:
            continue
        if len(acc) < len(n) and (n.startswith(acc + wn) or (acc + wn).startswith(n)):
            acc += wn
            last_x = w["x"] + w["w"]
            if len(acc) >= len(n):
                break
        else:
            break
    return last_x if acc else line["x1"]


def find_underscore(img, x_start, y_center, y_band=14, max_start_gap=350):
    """Find THIS row's fill line: a horizontal dark run in the label's row band
    that starts at/after the label end.

    Guards against random placement:
    - scan only y_center ± y_band (the label's own row)
    - the run must START within [x_start-20, x_start+max_start_gap] — box borders
      and section rules begin at the left margin (before the label) and are rejected;
      a fill line begins right after the label
    - among qualifying runs pick the one starting closest to the label (this row's line)

    Returns (x0, x1, run_len, y) or None.
    """
    gray = img.convert("L")
    w, h = gray.size
    px = gray.load()
    candidates = []
    for yy in range(max(0, y_center - y_band), min(h, y_center + y_band + 1)):
        run_start = None
        for xx in range(max(0, x_start - 20), w):
            if px[xx, yy] < 128:
                if run_start is None:
                    run_start = xx
            else:
                if run_start is not None:
                    run = xx - run_start
                    if run >= MIN_RUN_PX:
                        candidates.append((run_start, xx - 1, run, yy))
                    run_start = None
        if run_start is not None:
            run = w - run_start
            if run >= MIN_RUN_PX:
                candidates.append((run_start, w - 1, run, yy))
    if not candidates:
        return None
    pool = [c for c in candidates if (x_start - 20) <= c[0] <= (x_start + max_start_gap)]
    if not pool:
        return None
    # smallest start-gap = this row's line; tie-break: shorter run
    return min(pool, key=lambda c: ((c[0] - x_start), c[2]))


def fill_flat_pdf(input_pdf, output_pdf, fields, page=1, dpi=DEFAULT_DPI,
                  font_size_px=None, raise_px=RAISE_PX, lang="eng", anchors=None):
    """Fill a flat/scanned PDF. fields: {label: value}. page is 1-indexed.

    anchors: optional {label: {"x": px, "baseline": px, "x_end": px}} — explicit
    coordinates override OCR detection (use detect_fields / detect_lines output).

    Returns result dict: placed (with per-field placement info + no_line flag),
    needs_review (fields placed without a confirmed line), missing.
    """
    page0 = max(0, int(page) - 1)
    png, pw, ph = render_page_png(input_pdf, page0, dpi)
    img = Image.open(png)
    lines = ocr_lines(png, lang=lang)
    anchors = anchors or {}

    placed, missing, needs_review = [], [], []
    detected = [l["text"] for l in lines]

    for label, value in fields.items():
        value = str(value).strip()
        if not value:
            continue

        anchor = anchors.get(label)
        if anchor:
            x_fill = int(anchor["x"])
            base_y = int(anchor.get("baseline", anchor.get("y", 0)))
            x_end = int(anchor.get("x_end", x_fill + 800))
            found_line = True
            underscore = bool(anchor.get("underscore", True))
            ln_h = 40
        else:
            ln = find_label_line(label, lines)
            if ln is None:
                missing.append(label)
                continue
            lex = label_end_x(ln, label)
            gap = max(24, int((ln["y1"] - ln["y0"]) * 0.35))
            x_start = lex + gap
            ln_h = ln["y1"] - ln["y0"]
            un = find_underscore(img, x_start, ln["y1"], y_band=14)
            if un is not None:
                x_fill, x_end, _run, uy = un
                base_y = uy - raise_px
                found_line = True
                underscore = True
            else:
                # no confirmed line: place aligned with the label row but FLAG it
                x_fill, x_end = x_start, min(x_start + 800, pw - 40)
                base_y = ln["baseline"]
                found_line = False
                underscore = False

        size = font_size_px or max(24, min(72, int(ln_h * 0.92)))
        font = _load_font(size)
        while font.getlength(value) > (x_end - x_fill) and size > 20:
            size -= 2
            font = _load_font(size)
        fits = font.getlength(value) <= (x_end - x_fill)

        draw = ImageDraw.Draw(img)
        draw.text((x_fill, base_y), value, font=font, fill=(0, 0, 0), anchor="ls")

        placed.append({
            "label": label, "value": value,
            "x": x_fill, "baseline": base_y,
            "underscore": underscore,
            "no_line": not found_line,
            "font_px": size, "fits": fits,
        })
        if not found_line:
            needs_review.append(label)

    img.save(png)
    png_to_pdf(png, output_pdf, dpi)
    return {
        "output_pdf": output_pdf,
        "placed": placed,
        "needs_review": needs_review,
        "missing": missing,
        "detected_labels": detected,
    }


def detect_fields(input_pdf, page=1, dpi=DEFAULT_DPI, lang="eng"):
    """OCR a flat PDF page and return detected lines with boxes."""
    page0 = max(0, int(page) - 1)
    png, pw, ph = render_page_png(input_pdf, page0, dpi)
    lines = ocr_lines(png, lang=lang)
    return {"page_size_px": [pw, ph], "dpi": dpi, "lines": lines}


def make_test_form(out_pdf, dpi=DEFAULT_DPI, bordered=False):
    """Generate a synthetic flat (image-only) PDF form for testing.

    bordered=True adds a full-page box border and a full-width section rule —
    the exact traps that cause 'random' placement; the fill must ignore them.
    """
    w, h = int(8.5 * dpi), int(11 * dpi)
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    font = _load_font(int(0.16 * dpi))
    labels = ["Name:", "Address:", "City, State, ZIP:", "Case No.:", "Phone:"]
    y = int(1.0 * dpi)
    for lab in labels:
        d.text((int(0.75 * dpi), y), lab, font=font, fill=(0, 0, 0), anchor="ls")
        lw = font.getlength(lab)
        d.line([(int(0.75 * dpi) + lw + 20, y + 4),
                (int(6.75 * dpi), y + 4)], fill=(0, 0, 0), width=max(2, int(dpi // 60)))
        if bordered and lab == "City, State, ZIP:":
            # full-width section rule right below this row (the trap)
            d.line([(int(0.5 * dpi), y + int(0.30 * dpi)),
                    (int(8.0 * dpi), y + int(0.30 * dpi))], fill=(0, 0, 0), width=max(2, int(dpi // 60)))
        y += int(0.85 * dpi)
    if bordered:
        # full-page box border (the trap)
        d.rectangle([int(0.4 * dpi), int(0.4 * dpi), int(8.1 * dpi), int(10.6 * dpi)],
                    outline=(0, 0, 0), width=max(3, int(dpi // 40)))
    tmp = out_pdf + ".png"
    img.save(tmp)
    png_to_pdf(tmp, out_pdf, dpi)
    os.remove(tmp)
    return out_pdf
