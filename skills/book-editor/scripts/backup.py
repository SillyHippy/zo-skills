#!/usr/bin/env python3
"""Manage book backups and restore."""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

def list_backups(book_path: Path):
    """List all backups."""
    backups_dir = book_path / "backups"
    
    if not backups_dir.exists():
        print("No backups directory found")
        return 1
    
    backups = sorted(backups_dir.glob("*.md"), reverse=True)
    
    if not backups:
        print("No backups found")
        return 0
    
    print(f"Backups ({len(backups)} total):")
    print()
    
    for i, backup in enumerate(backups[:20], 1):
        # Get file size
        size = backup.stat().st_size
        size_kb = size / 1024
        
        # Parse timestamp from filename
        try:
            timestamp_str = backup.stem
            if '-' in timestamp_str:
                parts = timestamp_str.split('-')
                if len(parts) >= 2:
                    date_str = parts[0]
                    time_str = parts[1] if len(parts) > 1 else ""
                    display = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}" if len(date_str) == 8 else timestamp_str
                else:
                    display = timestamp_str
            else:
                display = timestamp_str
        except:
            display = backup.stem
        
        print(f"  {i}. {display} ({size_kb:.1f} KB)")
        print(f"     Path: {backup}")
    
    if len(backups) > 20:
        print(f"\n... and {len(backups) - 20} more backups")
    
    return 0

def restore_backup(book_path: Path, backup_name: str):
    """Restore a backup to current draft."""
    metadata_path = book_path / "current" / "metadata.json"
    
    if not metadata_path.exists():
        print(f"Error: No book project found at {book_path}")
        return 1
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    # Find backup
    backups_dir = book_path / "backups"
    
    # Try exact match first
    backup_path = backups_dir / backup_name
    if not backup_path.exists():
        # Try with .md extension
        backup_path = backups_dir / f"{backup_name}.md"
    if not backup_path.exists():
        # Try index
        try:
            index = int(backup_name)
            backups = sorted(backups_dir.glob("*.md"), reverse=True)
            if 1 <= index <= len(backups):
                backup_path = backups[index - 1]
        except ValueError:
            pass
    
    if not backup_path.exists():
        print(f"Error: Backup not found: {backup_name}")
        print(f"Run 'hermes book-backup --book {book_path} --action list' to see available backups")
        return 1
    
    manuscript_path = book_path / metadata["current_draft"]
    
    # Backup current first
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    current_backup = backups_dir / f"pre-restore-{timestamp}.md"
    
    if manuscript_path.exists():
        shutil.copy2(manuscript_path, current_backup)
        print(f"Current draft backed up to: {current_backup}")
    
    # Restore
    shutil.copy2(backup_path, manuscript_path)
    
    # Update metadata
    with open(manuscript_path) as f:
        content = f.read()
    word_count = len(content.split())
    
    metadata["word_count"] = word_count
    metadata["last_backup"] = str(backup_path.relative_to(book_path))
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Restored from: {backup_path}")
    print(f"Current draft: {manuscript_path}")
    print(f"Word count: {word_count:,}")
    
    return 0

def main():
    parser = argparse.ArgumentParser(description="Manage book backups")
    parser.add_argument("--book", required=True, help="Book project path")
    parser.add_argument("--action", choices=["list", "restore"], required=True)
    parser.add_argument("--backup", help="Backup to restore (name, path, or index)")
    args = parser.parse_args()
    
    book_path = Path(args.book)
    
    if args.action == "list":
        return list_backups(book_path)
    elif args.action == "restore":
        if not args.backup:
            print("Error: --backup required for restore action")
            return 1
        return restore_backup(book_path, args.backup)
    
    return 0

if __name__ == "__main__":
    main()
