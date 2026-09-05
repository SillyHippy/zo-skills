#!/usr/bin/env python3
"""Manage project sessions - start and end with checkpointing."""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

def get_next_checkpoint_id(checkpoints_dir: Path) -> str:
    existing = list(checkpoints_dir.glob('checkpoint-*.json'))
    if not existing:
        return 'checkpoint-001'
    
    numbers = []
    for f in existing:
        try:
            num = int(f.stem.split('-')[1])
            numbers.append(num)
        except (IndexError, ValueError):
            continue
    
    next_num = max(numbers) + 1 if numbers else 1
    return f'checkpoint-{next_num:03d}'

def load_state(memory_path: Path) -> dict:
    state_file = memory_path / 'current' / 'state.json'
    with open(state_file) as f:
        return json.load(f)

def save_state(memory_path: Path, state: dict):
    state_file = memory_path / 'current' / 'state.json'
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def start_session(memory_path: Path):
    state = load_state(memory_path)
    
    print(f'Project: {state["name"]}')
    print(f'Type: {state["type"]}')
    print()
    
    if state['last_checkpoint']:
        checkpoint_file = memory_path / 'checkpoints' / f'{state["last_checkpoint"]}.json'
        if checkpoint_file.exists():
            with open(checkpoint_file) as f:
                checkpoint = json.load(f)
            print(f'Last checkpoint: {state["last_checkpoint"]}')
            print(f'When: {checkpoint["timestamp"]}')
            print()
            print('Summary:')
            print(checkpoint['summary'])
            print()
            if checkpoint['decisions']:
                print('Decisions made:')
                for d in checkpoint['decisions']:
                    print(f'  - {d}')
                print()
            if checkpoint['next_priority']:
                print(f'Next priority: {checkpoint["next_priority"]}')
                print()
    
    if state['active_priority']:
        print(f'Current focus: {state["active_priority"]}')
    
    # Update last session
    state['last_session'] = datetime.utcnow().isoformat() + 'Z'
    save_state(memory_path, state)

def end_session(memory_path: Path, summary: str, decisions: str = None, 
                next_priority: str = None, files: str = None):
    state = load_state(memory_path)
    
    checkpoint_id = get_next_checkpoint_id(memory_path / 'checkpoints')
    
    checkpoint = {
        'checkpoint_id': checkpoint_id,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'project_type': state['type'],
        'summary': summary,
        'files_modified': files.split(',') if files else [],
        'decisions': decisions.split('\n') if decisions else [],
        'facts_learned': [],
        'todos_completed': [],
        'todos_created': [],
        'next_priority': next_priority,
        'word_count': None,
        'custom_data': {}
    }
    
    checkpoint_file = memory_path / 'checkpoints' / f'{checkpoint_id}.json'
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f, indent=2)
    
    # Update state
    state['last_checkpoint'] = checkpoint_id
    state['last_session'] = checkpoint['timestamp']
    state['active_priority'] = next_priority
    state['metrics']['checkpoints'] += 1
    state['metrics']['decisions'] += len(checkpoint['decisions'])
    save_state(memory_path, state)
    
    print(f'Checkpoint saved: {checkpoint_id}')

def show_status(memory_path: Path):
    state = load_state(memory_path)
    
    print(f'Project: {state["name"]}')
    print(f'Type: {state["type"]}')
    print(f'Created: {state["created"]}')
    print()
    print(f'Checkpoints: {state["metrics"]["checkpoints"]}')
    print(f'Decisions: {state["metrics"]["decisions"]}')
    print(f'Facts: {state["metrics"]["facts"]}')
    print()
    
    if state['last_checkpoint']:
        print(f'Last checkpoint: {state["last_checkpoint"]}')
    if state['active_priority']:
        print(f'Active priority: {state["active_priority"]}')

def main():
    parser = argparse.ArgumentParser(description='Manage project sessions')
    parser.add_argument('--project', required=True, help='Project memory path')
    parser.add_argument('--action', choices=['start', 'end', 'status'], required=True)
    parser.add_argument('--summary', help='Session summary (for end)')
    parser.add_argument('--decisions', help='Decisions made (for end)')
    parser.add_argument('--next', dest='next_priority', help='Next priority (for end)')
    parser.add_argument('--files', help='Files modified, comma-separated (for end)')
    args = parser.parse_args()
    
    memory_path = Path(args.project)
    if not memory_path.exists():
        # Try to find in ~/project-memory
        memory_path = Path.home() / 'project-memory' / Path(args.project).name
    
    if not memory_path.exists():
        print(f'Project not found: {args.project}')
        return 1
    
    if args.action == 'start':
        start_session(memory_path)
    elif args.action == 'end':
        if not args.summary:
            print('--summary required for end action')
            return 1
        end_session(memory_path, args.summary, args.decisions, 
                   args.next_priority, args.files)
    elif args.action == 'status':
        show_status(memory_path)

if __name__ == '__main__':
    main()
