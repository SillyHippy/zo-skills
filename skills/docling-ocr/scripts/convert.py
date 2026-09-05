#!/usr/bin/env python3
import sys
import os
import subprocess
from pathlib import Path

def ensure_docling():
    try:
        import docling
    except ImportError:
        print("Installing docling (this may take a moment)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "docling"])
        import docling

def convert_to_markdown(input_path: str, output_path: str = None):
    ensure_docling()
    from docling.document_converter import DocumentConverter
    
    input_file = Path(input_path).resolve()
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
        
    if output_path is None:
        output_file = input_file.with_suffix(".md")
    else:
        output_file = Path(output_path).resolve()
        
    print(f"Converting {input_file.name} to Markdown...")
    converter = DocumentConverter()
    result = converter.convert(str(input_file))
    
    markdown_text = result.document.export_to_markdown()
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_text)
        
    print(f"Successfully saved to: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 convert.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_to_markdown(input_file, output_file)