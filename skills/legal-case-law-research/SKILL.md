---
name: legal-case-law-research
description: Performs deep legal research with jurisdiction-specific case law verification, statute analysis, and authoritative source citation. Focuses on high-accuracy results with proper legal methodology.
compatibility: Created for Zo Computer with Hermes Agent integration
metadata:
  author: sillyhippy.zo.computer
---
# Legal Case Law Research Skill

## Purpose

This skill provides comprehensive legal research capabilities including:

- Jurisdiction-specific statute and court rule identification
- Leading case law discovery and analysis
- Authority verification with proper legal methodology
- Contradictory authority scanning
- Professional legal memo generation

## Workflow

1. **Clarify Scope**: Identify jurisdiction, authority type, and procedural posture
2. **Primary Sources**: Locate current statutes and court rules
3. **Case Law Research**: Find leading relevant cases with proper citations
4. **Verification**: Cross-reference conclusions with multiple authoritative sources
5. **Contradiction Check**: Scan for later contradictory or limiting authority
6. **Document Generation**: Produce professional legal research memos in PDF format

## Integration Notes

- Uses existing cloud API models via OpenRouter configuration
- Generates HTML output for PDF conversion via wkhtmltopdf
- Supports optional OCR for scanned document processing
- Designed for free-tier operation with paid upgrades available

## Usage

Call this skill when you need:

- Legal research memos
- Case law verification
- Statute interpretation
- Court rule analysis
- Professional legal document generation

## Dependencies

- Hermes Agent (already running)
- wkhtmltopdf (for PDF generation)
- Optional: Tesseract OCR (for document processing)