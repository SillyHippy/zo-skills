#!/usr/bin/env python3
"""MCP server: flat/scanned PDF auto-fill via OCR (free tier, CPU).

Tools:
- detect_fields(input_pdf, page) -> JSON of OCR lines + boxes
- fill_flat_pdf(input_pdf, output_pdf, fields, page, dpi, font_size_px) -> JSON result
- make_test_form(output_pdf) -> path

Config (Hermes ~/.hermes/config.yaml):
  mcp_servers:
    flat_pdf_fill:
      command: python3
      args: [/home/workspace/flat-pdf-fill/server.py]
      timeout: 300
"""
import json

from fastmcp import FastMCP

import core

mcp = FastMCP("flat-pdf-fill")


@mcp.tool()
def detect_fields(input_pdf: str, page: int = 1, dpi: int = 300) -> str:
    """OCR a flat/scanned PDF page and return detected field labels with pixel boxes (for verification or manual anchoring)."""
    try:
        return json.dumps(core.detect_fields(input_pdf, page=page, dpi=dpi), default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def fill_flat_pdf(input_pdf: str, output_pdf: str, fields: dict,
                  page: int = 1, dpi: int = 300, font_size_px: int = 0,
                  anchors: dict = None) -> str:
    """Fill a flat/scanned PDF: OCR-detects each field label, places the value ON the printed line (typewriter overlay), writes output_pdf. fields = {"Label as printed": "value"}. page is 1-indexed. Values are only placed on a confirmed line; if no line is found the field is flagged in needs_review instead of placed blindly. anchors = optional {label: {"x": px, "baseline": px, "x_end": px}} explicit coordinates to override detection."""
    try:
        res = core.fill_flat_pdf(input_pdf, output_pdf, fields, page=page, dpi=dpi,
                                 font_size_px=font_size_px or None, anchors=anchors)
        return json.dumps(res, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def make_test_form(output_pdf: str, bordered: bool = False) -> str:
    """Generate a synthetic flat (image-only) PDF form with sample labels/underscores for testing. bordered=True adds a full-page box border + section rule to prove line detection ignores traps."""
    try:
        return json.dumps({"output_pdf": core.make_test_form(output_pdf, bordered=bordered)})
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
