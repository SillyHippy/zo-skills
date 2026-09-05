#!/usr/bin/env python3
"""Search book content using keyword search (RAG optional)."""

import argparse
import json
import os
import re
from pathlib import Path
from typing import List, Tuple

def keyword_search(content: str, query: str, context_lines: int = 3) -> List[Tuple[int, str]]:
    """Simple keyword search with context."""
    lines = content.split('\n')
    query_lower = query.lower()
    results = []
    
    for i, line in enumerate(lines):
        if query_lower in line.lower():
            # Get context
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            context = '\n'.join(lines[start:end])
            results.append((i + 1, context))
    
    return results

def chapter_search(content: str) -> List[Tuple[str, int, int]]:
    """Find chapters in the manuscript."""
    chapters = []
    
    # Common chapter patterns
    patterns = [
        r'^#\s+Chapter\s+(\d+|[IVX]+)[.:]?\s*(.*?)$',  # # Chapter 1: Title
        r'^Chapter\s+(\d+|[IVX]+)[.:]?\s*(.*?)$',       # Chapter 1: Title
        r'^#\s+(\d+)\.[\s\t]*(.*?)$',                   # # 1. Title
        r'^CHAPTER\s+(\d+|[IVX]+)',                     # CHAPTER 1
    ]
    
    lines = content.split('\n')
    
    for pattern in patterns:
        for i, line in enumerate(lines):
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                chapter_num = match.group(1)
                chapter_title = match.group(2) if len(match.groups()) > 1 else ""
                chapters.append((chapter_num, chapter_title.strip(), i + 1))
    
    return chapters

def main():
    parser = argparse.ArgumentParser(description="Search book content")
    parser.add_argument("--book", required=True, help="Book project path")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--context", type=int, default=3, help="Context lines (default: 3)")
    parser.add_argument("--chapters", action="store_true", help="List chapters")
    args = parser.parse_args()
    
    book_path = Path(args.book)
    metadata_path = book_path / "current" / "metadata.json"
    
    if not metadata_path.exists():
        print(f"Error: No book project found at {book_path}")
        return 1
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    manuscript_path = book_path / metadata["current_draft"]
    
    if not manuscript_path.exists():
        print(f"Error: Current draft not found: {manuscript_path}")
        return 1
    
    with open(manuscript_path) as f:
        content = f.read()
    
    if args.chapters:
        chapters = chapter_search(content)
        if chapters:
            print(f"Chapters found ({len(chapters)}):")
            print()
            for num, title, line_num in chapters:
                if title:
                    print(f"  Chapter {num}: {title} (line {line_num})")
                else:
                    print(f"  Chapter {num} (line {line_num})")
        else:
            print("No chapters found (no recognized chapter headings)")
        return 0
    
    # Search
    results = keyword_search(content, args.query, args.context)
    
    if results:
        print(f"Found {len(results)} matches for '{args.query}':")
        print()
        
        for line_num, context in results[:20]:  # Limit to 20 results
            print(f"--- Line {line_num} ---")
            print(context)
            print()
        
        if len(results) > 20:
            print(f"... and {len(results) - 20} more matches")
    else:
        print(f"No matches found for '{args.query}'")
        print()
        print("Tip: Try searching for partial words or different terms")
    
    return 0

if __name__ == "__main__":
    main()
