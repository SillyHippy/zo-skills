#!/usr/bin/env python3
"""Manage editing sessions with checkpointing."""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

def get_next_checkpoint_id(checkpoints_dir: Path) -> str:
    """Get next checkpoint ID (checkpoint-001, etc.)."""
    existing = list(checkpoints_dir.glob("checkpoint-*.json"))
    if not existing:
        return "checkpoint-001"
    
    numbers = []
    for f in existing:
        try:
            num = int(f.stem.split('-')[1])
            numbers.append(num)
        except (IndexError, ValueError):
            continue
    
    next_num = max(numbers) + 1 if numbers else 1
    return f"checkpoint-{next_num:03d}"

def start_session(book_path: Path):
    """Load checkpoint and current state for Hermes."""
    metadata_path = book_path / "current" / "metadata.json"
    
    if not metadata_path.exists():
        print(f"Error: No book project found at {book_path}")
        print("Run: hermes book-init --name 'Title' --file /path/to/draft.md")
        return 1
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    manuscript_path = book_path / metadata["current_draft"]
    
    # Load latest checkpoint
    checkpoint = None
    if metadata.get("last_checkpoint"):
        checkpoint_path = book_path / "checkpoints" / f"{metadata['last_checkpoint']}.json"
        if checkpoint_path.exists():
            with open(checkpoint_path) as f:
                checkpoint = json.load(f)
    
    # Get word count
    word_count = 0
    if manuscript_path.exists():
        with open(manuscript_path) as f:
            content = f.read()
        word_count = len(content.split())
    
    # Output session info for Hermes
    print("=" * 60)
    print("BOOK EDITING SESSION STARTED")
    print("=" * 60)
    print(f"")
    print(f"Book: {metadata['name']}")
    print(f"Word count: {word_count:,}")
    print(f"Current draft: {metadata['current_draft']}")
    print(f"")
    
    if checkpoint:
        print(f"Last checkpoint: {checkpoint['checkpoint_id']}")
        print(f"Last session: {checkpoint['session_summary']}")
        print(f"")
        if checkpoint.get('decisions_made'):
            print("Recent decisions:")
            for d in checkpoint['decisions_made'][-5:]:
                print(f"  - {d}")
            print(f"")
        if checkpoint.get('next_steps'):
            print("Next steps from last session:")
            for s in checkpoint['next_steps']:
                print(f"  - {s}")
            print(f"")
    
    print(f"Files:")
    print(f"  Current draft: {manuscript_path}")
    print(f"  Metadata: {metadata_path}")
    print(f"  Backups: {book_path / 'backups'}")
    print(f"")
    print("=" * 60)
    print("INSTRUCTIONS FOR HERMES:")
    print("=" * 60)
    print(f"1. Read the current draft: {manuscript_path}")
    print(f"2. Check metadata for context: {metadata_path}")
    print(f"3. Make edits to {manuscript_path}")
    print(f"4. When done, run: hermes book-session --book {book_path} --action end --summary 'what you did'")
    print(f"")
    
    return 0

def end_session(book_path: Path, summary: str):
    """Save checkpoint and backup."""
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
    
    # Get word count
    with open(manuscript_path) as f:
        content = f.read()
    word_count = len(content.split())
    
    # Create backup
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_name = f"{timestamp}.md"
    backup_path = book_path / "backups" / backup_name
    
    with open(backup_path, 'w') as f:
        f.write(content)
    
    # Create checkpoint
    checkpoints_dir = book_path / "checkpoints"
    checkpoint_id = get_next_checkpoint_id(checkpoints_dir)
    
    checkpoint = {
        "checkpoint_id": checkpoint_id,
        "timestamp": datetime.now().isoformat(),
        "session_summary": summary,
        "files_modified": ["manuscript.md"],
        "decisions_made": [],  # Hermes can populate this
        "next_steps": [],      # Hermes can populate this
        "word_count": word_count,
        "backup_created": str(backup_path.relative_to(book_path))
    }
    
    checkpoint_path = checkpoints_dir / f"{checkpoint_id}.json"
    with open(checkpoint_path, 'w') as f:
        json.dump(checkpoint, f, indent=2)
    
    # Update metadata
    metadata["last_checkpoint"] = checkpoint_id
    metadata["last_backup"] = str(backup_path.relative_to(book_path))
    metadata["word_count"] = word_count
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Session ended.")
    print(f"  Checkpoint: {checkpoint_id}")
    print(f"  Backup: {backup_path}")
    print(f"  Word count: {word_count:,}")
    print(f"  Summary: {summary}")
    
    return 0

def show_status(book_path: Path):
    """Show current book status."""
    metadata_path = book_path / "current" / "metadata.json"
    
    if not metadata_path.exists():
        print(f"Error: No book project found at {book_path}")
        return 1
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    print(f"Book: {metadata['name']}")
    print(f"Word count: {metadata.get('word_count', 0):,}")
    print(f"Current draft: {metadata['current_draft']}")
    print(f"Last checkpoint: {metadata.get('last_checkpoint', 'None')}")
    print(f"Last backup: {metadata.get('last_backup', 'None')}")
    print(f"Created: {metadata.get('created', 'Unknown')}")
    
    # List recent checkpoints
    checkpoints_dir = book_path / "checkpoints"
    if checkpoints_dir.exists():
        checkpoints = sorted(checkpoints_dir.glob("checkpoint-*.json"), reverse=True)[:5]
        if checkpoints:
            print(f"")
            print("Recent checkpoints:")
            for cp in checkpoints:
                with open(cp) as f:
                    data = json.load(f)
                print(f"  {data['checkpoint_id']}: {data['session_summary'][:60]}...")
    
    # List recent backups
    backups_dir = book_path / "backups"
    if backups_dir.exists():
        backups = sorted(backups_dir.glob("*.md"), reverse=True)[:5]
        if backups:
            print(f"")
            print("Recent backups:")
            for bk in backups:
                print(f"  {bk.name}")
    
    return 0

def main():
    parser = argparse.ArgumentParser(description="Manage book editing sessions")
    parser.add_argument("--book", required=True, help="Book project path")
    parser.add_argument("--action", choices=["start", "end", "status"], required=True)
    parser.add_argument("--summary", help="Session summary (for --action end)")
    args = parser.parse_args()
    
    book_path = Path(args.book)
    
    if args.action == "start":
        return start_session(book_path)
    elif args.action == "end":
        if not args.summary:
            print("Error: --summary required for end action")
            return 1
        return end_session(book_path, args.summary)
    elif args.action == "status":
        return show_status(book_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
