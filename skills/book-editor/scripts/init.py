#!/usr/bin/env python3
"""Initialize a new book project with RAG indexing."""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Initialize book project")
    parser.add_argument("--name", required=True, help="Book title")
    parser.add_argument("--path", required=True, help="Project directory path")
    parser.add_argument("--file", help="Initial manuscript file to import")
    args = parser.parse_args()
    
    # Create directory structure
    project_path = Path(args.path)
    project_path.mkdir(parents=True, exist_ok=True)
    
    (project_path / "current").mkdir(exist_ok=True)
    (project_path / "backups").mkdir(exist_ok=True)
    (project_path / "checkpoints").mkdir(exist_ok=True)
    (project_path / "index").mkdir(exist_ok=True)
    
    # Create metadata
    metadata = {
        "name": args.name,
        "created": datetime.now().isoformat(),
        "current_draft": "current/manuscript.md",
        "word_count": 0,
        "last_checkpoint": None,
        "last_backup": None
    }
    
    # Import initial file if provided
    if args.file and os.path.exists(args.file):
        with open(args.file, 'r') as f:
            content = f.read()
        
        manuscript_path = project_path / "current" / "manuscript.md"
        with open(manuscript_path, 'w') as f:
            f.write(content)
        
        metadata["word_count"] = len(content.split())
        
        # Create initial backup
        backup_name = f"initial-import-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        backup_path = project_path / "backups" / backup_name
        with open(backup_path, 'w') as f:
            f.write(content)
        
        metadata["last_backup"] = str(backup_path.relative_to(project_path))
        
        # Create initial checkpoint
        checkpoint = {
            "checkpoint_id": "checkpoint-001",
            "timestamp": datetime.now().isoformat(),
            "session_summary": "Initial import",
            "files_modified": ["manuscript.md"],
            "decisions_made": [],
            "next_steps": ["Begin editing"],
            "word_count": metadata["word_count"],
            "backup_created": str(backup_path.relative_to(project_path))
        }
        
        checkpoint_path = project_path / "checkpoints" / "checkpoint-001.json"
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        metadata["last_checkpoint"] = "checkpoint-001"
    
    # Save metadata
    metadata_path = project_path / "current" / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Book project initialized: {project_path}")
    print(f"  Name: {args.name}")
    print(f"  Word count: {metadata['word_count']}")
    print(f"  Current draft: {metadata['current_draft']}")
    print(f"")
    print(f"Next steps:")
    print(f"  1. Start editing: hermes book-session --book {args.path} --action start")
    print(f"  2. Search content: hermes book-search --book {args.path} --query 'your query'")
    print(f"")
    print(f"Project structure:")
    for item in sorted(project_path.rglob('*')):
        if item.is_dir():
            rel = item.relative_to(project_path)
            print(f"  {rel}/")

if __name__ == "__main__":
    main()
