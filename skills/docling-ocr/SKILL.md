---
name: docling-ocr
description: Convert PDFs, Word docs, and images to clean Markdown using IBM's Docling. Runs entirely locally on CPU, no GPU required.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---

# Docling OCR Skill

This skill converts documents (PDF, DOCX, images, etc.) into clean, structured Markdown using IBM's Docling. It is optimized for CPU-only environments and does not require a GPU.

## Usage

Run the conversion script from the workspace:

```bash
python3 /home/workspace/Skills/docling-ocr/scripts/convert.py <input_file_path> [output_file_path]
```

If `output_file_path` is omitted, it will save as `<input_file_name>.md` in the same directory.

## Dependencies

The script will automatically check for and install `docling` via pip if it is not already installed. Note: Initial installation may take a few minutes as it downloads necessary models.