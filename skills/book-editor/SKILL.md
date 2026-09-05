---
name: book-editor
description: |
  Comprehensive book editing system with RAG memory for Hermes. Manages multi-chapter 
  books with automatic checkpointing, backup tracking, and semantic search across 
  drafts. Prevents confusion about current state in long editing sessions.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---

# Book Editor Skill

## Problem Solved

When editing a 90k word book with multiple backups, Hermes gets confused about:
- Which file is the current draft?
- What was edited last session?
- What are the priorities for this session?
- Where are the backups?

This skill provides structured project management with checkpointing and search.

## Commands

### Initialize a new book project
```bash
hermes-book-init --name "My Book Title" --path /home/workspace/Books/my-book [--file initial-draft.md]
```

Creates directory structure:
```
Books/my-book/
├── current/
│   ├── manuscript.md      # Current working draft
│   └── metadata.json      # Project state
├── backups/               # All backup versions
├── checkpoints/           # Session summaries
└── notes/                 # Character notes, outlines, etc.
```

### Start an editing session
```bash
hermes-book-session --book /home/workspace/Books/my-book --action start
```

Outputs what Hermes needs to know:
- Current word count
- Last checkpoint summary
- Session priority
- File locations

### End an editing session
```bash
hermes-book-session --book /home/workspace/Books/my-book --action end \
  --summary "Edited Chapter 3, fixed timeline issues" \
  --next "Continue Chapter 4 tomorrow"
```

Creates checkpoint with:
- What was done
- What to do next
- Word count change
- Timestamp

### Search the book
```bash
hermes-book-search --book /home/workspace/Books/my-book --query "character name"
hermes-book-search --book /home/workspace/Books/my-book --chapters
```

### List backups
```bash
hermes-book-backup --book /home/workspace/Books/my-book --action list
```

### Restore a backup
```bash
hermes-book-backup --book /home/workspace/Books/my-book --action restore --backup 1
# or by filename:
hermes-book-backup --book /home/workspace/Books/my-book --action restore --backup 20240620-143022
```

## Hermes Workflow

**At session start, Hermes runs:**
```bash
hermes-book-session --book /home/workspace/Books/my-book --action start
```

This tells Hermes:
- Where the current draft is
- What was worked on last time
- What the priority is
- Word count and progress

**During the session:**
- Hermes edits `current/manuscript.md`
- Can search for content: `hermes-book-search --book ... --query "..."`
- Can check chapters: `hermes-book-search --book ... --chapters`

**At session end, Hermes runs:**
```bash
hermes-book-session --book /home/workspace/Books/my-book --action end \
  --summary "..." --next "..."
```

This:
- Backs up the current draft
- Creates a checkpoint with summary
- Sets up next session

## File Structure

```
Books/
└── my-book/
    ├── current/
    │   ├── manuscript.md          ← Hermes edits this file
    │   └── metadata.json          ← Auto-updated state
    ├── backups/
    │   ├── 20240620-143022.md     ← Auto-created backups
    │   ├── 20240621-091500.md
    │   └── pre-restore-20240621-102300.md
    ├── checkpoints/
    │   ├── checkpoint-001.json    ← Session summaries
    │   ├── checkpoint-002.json
    │   └── checkpoint-003.json
    └── notes/
        ├── characters.md            ← Optional: character notes
        ├── outline.md               ← Optional: outline
        └── style-guide.md           ← Optional: style notes
```

## metadata.json Format

```json
{
  "title": "My Book Title",
  "created": "2024-06-20T14:30:22",
  "current_draft": "current/manuscript.md",
  "word_count": 90423,
  "last_backup": "backups/20240620-143022.md",
  "checkpoints": ["checkpoints/checkpoint-001.json"],
  "session_priority": "Fix Chapter 3 timeline issues"
}
```

## checkpoint.json Format

```json
{
  "id": "checkpoint-003",
  "timestamp": "2024-06-21T09:15:00",
  "word_count_start": 90423,
  "word_count_end": 91200,
  "summary": "Edited Chapter 3, fixed timeline inconsistencies with Chapter 2",
  "next_priority": "Continue Chapter 4 - introduce secondary antagonist",
  "files_modified": ["current/manuscript.md"]
}
```

## Complete Example

**1. Initialize:**
```bash
hermes-book-init --name "The Epic Novel" --path /home/workspace/Books/epic-novel --file draft-v1.md
```

**2. Start session:**
```bash
hermes-book-session --book /home/workspace/Books/epic-novel --action start
```

Output:
```
=== BOOK SESSION START ===
Title: The Epic Novel
Current draft: current/manuscript.md
Word count: 90,423

Last checkpoint (checkpoint-003):
  Summary: Edited Chapter 3, fixed timeline inconsistencies
  Next priority: Continue Chapter 4 - introduce secondary antagonist

Session priority: Continue Chapter 4 - introduce secondary antagonist

=== FILES ===
Edit this: /home/workspace/Books/epic-novel/current/manuscript.md
Checkpoints: /home/workspace/Books/epic-novel/checkpoints/
Backups: /home/workspace/Books/epic-novel/backups/
```

**3. Hermes edits the file** (manually or via Zo)

**4. End session:**
```bash
hermes-book-session --book /home/workspace/Books/epic-novel --action end \
  --summary "Wrote 2,000 words in Chapter 4, introduced antagonist Victor" \
  --next "Write confrontation scene in Chapter 5"
```

**5. Next session:**
```bash
hermes-book-session --book /home/workspace/Books/epic-novel --action start
```

Hermes now knows exactly what to do.

## Hermes Integration

Add to Hermes config (`~/.hermes/config.yaml`):

```yaml
book_projects:
  epic-novel:
    path: /home/workspace/Books/epic-novel
    current: current/manuscript.md
```

Or use the skill directly:
```bash
# Before editing
hermes-book-session --book /home/workspace/Books/epic-novel --action start

# After editing  
hermes-book-session --book /home/workspace/Books/epic-novel --action end --summary "..." --next "..."
```

## Troubleshooting

**"No book project found"**
- Run `hermes-book-init` first to create the project structure

**"Current draft not found"**
- The manuscript.md file may have been deleted
- Restore from backup: `hermes-book-backup --action restore --backup 1`

**Search returns no results**
- The query might be too specific
- Try partial words or different terms
- Check file encoding (should be UTF-8)

## Scripts Location

- `/home/workspace/Skills/book-editor/scripts/init.py` - Initialize project
- `/home/workspace/Skills/book-editor/scripts/session.py` - Session management
- `/home/workspace/Skills/book-editor/scripts/search.py` - Content search
- `/home/workspace/Skills/book-editor/scripts/backup.py` - Backup management
