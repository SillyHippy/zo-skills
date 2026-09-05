#!/usr/bin/env python3
"""
PDF Form Filler — Image Compositing Approach
Renders PDF at high res, uses OCR anchors for positioning, composites text with PIL.
"""
import sys
import json
import os
from pathlib import Path

import pytesseract
import pymupdf
from PIL import Image, ImageDraw, ImageFont


def render_page(pdf_path, page_num, scale=4):
    """Render PDF page at high resolution. Returns PIL Image."""
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))
    img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    doc.close()
    return img


def ocr_with_boxes(img):
    """Run OCR and return word-level bounding boxes."""
    data = pytesseract.image_to_data(img, lang='eng', config='--psm 6', output_type=pytesseract.Output.DICT)
    words = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if text:
            words.append({
                'text': text,
                'x': data['left'][i],
                'y': data['top'][i],
                'w': data['width'][i],
                'h': data['height'][i],
                'x2': data['left'][i] + data['width'][i],
                'y2': data['top'][i] + data['height'][i],
            })
    return words


def find_anchor(words, anchor_text, tolerance=0.7):
    """Find a word/phrase matching anchor_text. Returns best match or None."""
    anchor_lower = anchor_text.lower()
    best = None
    best_score = 0
    for w in words:
        w_lower = w['text'].lower().rstrip(',:;')
        if anchor_lower in w_lower or w_lower in anchor_lower:
            # Exact match gets highest score
            score = len(set(anchor_lower) & set(w_lower)) / max(len(anchor_lower), 1)
            if score > best_score:
                best_score = score
                best = w
    return best if best_score >= tolerance else None


def find_blank_after(words, anchor_text, line_tolerance=5, scale=4):
    """Find the blank space after an anchor word on the same line."""
    anchor = find_anchor(words, anchor_text)
    if not anchor:
        return None
    
    # Find words on the same line (within line_tolerance pixels)
    same_line = [w for w in words if abs(w['y'] - anchor['y2']) < line_tolerance or 
                 abs(w['y2'] - anchor['y']) < line_tolerance]
    
    # Find the next word after this anchor on the same line
    after_words = [w for w in same_line if w['x'] > anchor['x2'] + 2]
    after_words.sort(key=lambda w: w['x'])
    
    if after_words:
        next_word = after_words[0]
        # Blank is between anchor's right edge and next word's left edge
        blank_x = anchor['x2'] + 4
        blank_y = anchor['y']
        blank_w = next_word['x'] - blank_x - 4
        blank_h = max(anchor['h'], next_word['h'])
        return {'x': blank_x, 'y': blank_y, 'w': blank_w, 'h': blank_h, 'baseline_y': anchor['y2']}
    else:
        # No word after — blank extends to right margin
        blank_x = anchor['x2'] + 4
        blank_y = anchor['y']
        blank_w = 400  # reasonable default
        blank_h = anchor['h']
        return {'x': blank_x, 'y': blank_y, 'w': blank_w, 'h': blank_h, 'baseline_y': anchor['y2']}


def composite_text(img, x, y, text, fontsize=10, color=(0, 0, 0)):
    """Draw text on image at exact pixel position."""
    draw = ImageDraw.Draw(img)
    # Use default font scaled to size
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    
    # y is the top of the text box, baseline is roughly y + fontsize*0.8
    baseline_y = y + int(fontsize * 0.8)
    draw.text((x, baseline_y), text, fill=color, font=font)
    return img


def composite_text_on_blank(img, blank, text, fontsize=None, color=(0, 0, 0)):
    """Place text centered in a blank area."""
    if fontsize is None:
        # Auto-size: fit text to blank width
        draw = ImageDraw.Draw(img)
        try:
            font_test = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            font_test = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font_test)
        text_w = bbox[2] - bbox[0]
        if text_w > 0 and blank['w'] > 0:
            fontsize = max(8, min(20, int(blank['w'] * 20 / text_w)))
        else:
            fontsize = 12
    
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    
    # Center text horizontally in blank, vertically align to baseline
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = blank['x'] + max(0, (blank['w'] - text_w) // 2)
    y = blank['y'] + max(0, (blank['h'] - text_h) // 2)
    
    draw.text((x, y), text, fill=color, font=font)
    return img


def composite_text_at_position(img, x, y, text, fontsize=12, color=(0, 0, 0)):
    """Place text at absolute pixel position (x=left, y=top of text box)."""
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    draw.text((x, y), text, fill=color, font=font)
    return img


def draw_checkbox(img, x, y, size=14):
    """Draw an X mark at position."""
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except:
        font = ImageFont.load_default()
    draw.text((x, y), "X", fill=(0, 0, 0), font=font)
    return img


def save_as_pdf(img, output_path):
    """Save PIL Image as PDF."""
    img.save(output_path, "PDF", resolution=150)


def fill_pdf(pdf_path, fields, output_path, scale=4, page_num=None):
    """
    Fill a PDF form using image compositing.
    
    fields: list of dicts, each with:
        - type: 'text' | 'checkbox'
        - anchor: text to search for (for auto-positioning)
        - offset_x: pixels right of anchor's right edge (default 0)
        - offset_y: pixels below anchor's top (default 0)
        - x, y: absolute pixel position (overrides anchor)
        - value: text to insert
        - fontsize: font size (default auto)
        - page: page number (default 0)
    
    Returns path to output PDF.
    """
    pages_to_fill = {}
    for f in fields:
        pg = f.get('page', page_num if page_num is not None else 0)
        if pg not in pages_to_fill:
            pages_to_fill[pg] = []
        pages_to_fill[pg].append(f)
    
    # Render all pages
    doc = pymupdf.open(pdf_path)
    total_pages = doc.page_count
    doc.close()
    
    images = {}
    for pg in range(total_pages):
        img = render_page(pdf_path, pg, scale=scale)
        if pg in pages_to_fill:
            # Run OCR once per page
            words = ocr_with_boxes(img)
            
            for f in pages_to_fill[pg]:
                ftype = f.get('type', 'text')
                value = f.get('value', '')
                
                if ftype == 'checkbox':
                    # Checkbox: place X at anchor position or absolute coords
                    if 'anchor' in f:
                        anchor = find_anchor(words, f['anchor'])
                        if anchor:
                            x = anchor['x2'] + f.get('offset_x', -2)
                            y = anchor['y'] + f.get('offset_y', 0)
                            img = draw_checkbox(img, x, y, size=f.get('size', 14))
                    elif 'x' in f and 'y' in f:
                        img = draw_checkbox(img, f['x'], f['y'], size=f.get('size', 14))
                
                elif ftype == 'text':
                    if 'x' in f and 'y' in f:
                        # Absolute positioning
                        img = composite_text_at_position(
                            img, f['x'], f['y'], value,
                            fontsize=f.get('fontsize', 12)
                        )
                    elif 'anchor' in f:
                        # Anchor-based positioning
                        blank = find_blank_after(words, f['anchor'])
                        if blank:
                            # Apply offsets
                            blank['x'] += f.get('offset_x', 0)
                            blank['y'] += f.get('offset_y', 0)
                            blank['w'] = max(blank['w'] - f.get('offset_x', 0), 20)
                            img = composite_text_on_blank(img, blank, value, fontsize=f.get('fontsize'))
                        else:
                            print(f"WARNING: anchor '{f['anchor']}' not found on page {pg}")
        
        images[pg] = img
    
    # Save all pages as PDF
    page_list = [images[pg] for pg in range(total_pages)]
    page_list[0].save(output_path, "PDF", resolution=150, save_all=True, append_images=page_list[1:])
    print(f"Saved: {output_path}")
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: pdf_form_filler.py <input.pdf> <fields.json> [output.pdf]")
        print("  fields.json: list of field definitions")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    fields_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else pdf_path.replace('.pdf', '_FILLED.pdf')
    
    with open(fields_path) as f:
        fields = json.load(f)
    
    fill_pdf(pdf_path, fields, output_path)
