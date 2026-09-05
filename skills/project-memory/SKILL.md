---
name: project-memory
description: |
  Universal project memory system for Hermes. Replaces the 2,200 char memory limit 
  with structured checkpoints, search, and context management for any project type.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---

# Project Memory Skill

## Problem Solved

Hermes has a 2,200 character memory limit. For any complex project, this is insufficient.
This skill provides unlimited structured memory with:
- Session checkpointing
- Semantic search
- Context retrieval
- Decision tracking

## Quick Start

### 1. Initialize project memory
```bash
python3 /home/workspace/Skills/project-memory/scripts/init.py \
  --name "Project Name" \
  --path /home/workspace/projects/my-project \
  --type [book|code|research|legal|general]
```

### 2. Start session
```bash
python3 /home/workspace/Skills/project-memory/scripts/session.py \
  --project /home/workspace/projects/my-project \
  --action start
```

### 3. Search memory
```bash
python3 /home/workspace/Skills/project-memory/scripts/search.py \
  --project /home/workspace/projects/my-project \
  --query "what was decided about..."
```

### 4. End session
```bash
python3 /home/workspace/Skills/project-memory/scripts/session.py \
  --project /home/workspace/projects/my-project \
  --action end \
  --summary "What was accomplished" \
  --decisions "Key decisions made" \
  --next "Next steps"
```

## Project Types

### book
For writing/editing books. Tracks:
- Word count
- Chapters
- Character notes
- Plot points
- Editing priorities

### code
For software projects. Tracks:
- Files modified
- Architecture decisions
- TODOs
- Bug fixes

### research
For research projects. Tracks:
- Sources found
- Notes organized
- Questions answered
- Next research directions

### legal
For legal cases. Tracks:
- Case documents
- Deadlines
- Client communications
- Filing status

### general
For any other project. Flexible structure.

## Directory Structure

```
~/project-memory/
└── {project-name}/
    ├── current/
    │   ├── state.json          # Current project state
    │   └── context.md          # Active context for Hermes
    ├── checkpoints/
    │   ├── checkpoint-001.json
    │   └── checkpoint-002.json
    ├── knowledge/
    │   ├── facts.json          # Key facts
    │   ├── decisions.json      # Decisions made
    │   └── references/         # External references
    └── index/                  # Search index (optional)
```

## Commands

### pm-init
Initialize project memory.

```bash
pm-init --name "Project" --path /home/workspace/projects/x --type code
```

### pm-session
Manage sessions.

```bash
# Start - loads context for Hermes
pm-session --project /home/workspace/projects/x --action start

# End - saves checkpoint
pm-session --project /home/workspace/projects/x --action end \
  --summary "Built login system" \
  --decisions "Used JWT auth" \
  --next "Build password reset"

# Status - show current state
pm-session --project /home/workspace/projects/x --action status
```

### pm-search
Search project memory.

```bash
pm-search --project /home/workspace/projects/x --query "JWT"
pm-search --project /home/workspace/projects/x --query "decisions"
pm-search --project /home/workspace/projects/x --query "todos"
```

### pm-note
Add a note to memory.

```bash
pm-note --project /home/workspace/projects/x \
  --type fact \
  --content "API rate limit is 1000 requests/hour"
```

### pm-list
List all projects.

```bash
pm-list
```

## Hermes Integration

Hermes should run at session start:
```bash
pm-session --project /path/to/project --action start
```

This outputs:
- Current project state
- Last checkpoint summary
- Active priorities
- Relevant context

Hermes reads this and knows exactly what to do.

At session end:
```bash
pm-session --project /path/to/project --action end \
  --summary "..." \
  --decisions "..." \
  --next "..."
```

## Checkpoint Format

```json
{
  "checkpoint_id": "checkpoint-042",
  "timestamp": "2026-06-20T22:00:00Z",
  "project_type": "code",
  "summary": "Built user authentication system",
  "files_modified": ["auth.js", "login.html"],
  "decisions": [
    "Used JWT for stateless auth",
    "Passwords hashed with bcrypt"
  ],
  "facts_learned": [
    "Rate limit is 1000 req/hour"
  ],
  "todos_completed": ["Setup auth middleware"],
  "todos_created": ["Add password reset", "Add email verification"],
  "next_priority": "Build password reset flow",
  "word_count": null,
  "custom_data": {}
}
```

## state.json Format

```json
{
  "name": "My Project",
  "type": "code",
  "created": "2026-06-20T22:00:00Z",
  "last_checkpoint": "checkpoint-042",
  "last_session": "2026-06-20T22:00:00Z",
  "active_priority": "Build password reset",
  "metrics": {
    "checkpoints": 42,
    "decisions": 15,
    "facts": 23
  },
  "context_summary": "Building auth system, JWT implemented, next is password reset"
}
```

## How It Works

1. **Hermes runs `pm-session --action start`**
   - Loads current state
   - Shows last checkpoint
   - Displays active priority
   - Outputs context for this session

2. **Hermes works with full context**
   - No 2,200 char limit
   - Can search entire project history
   - Knows what was decided

3. **Hermes runs `pm-session --action end`**
   - Saves checkpoint with summary
   - Records decisions
   - Sets next priority
   - Updates state

4. **Next session starts fresh**
   - Loads checkpoint
   - Knows exactly where to continue
   - No confusion

## Scripts

- `init.py` - Initialize project
- `session.py` - Start/end sessions
- `search.py` - Search memory
- `note.py` - Add notes
- `list.py` - List projects
