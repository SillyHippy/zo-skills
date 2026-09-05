#!/usr/bin/env python3
"""Initialize project memory for any project type."""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

PROJECT_TYPES = ['book', 'code', 'research', 'legal', 'general']

def main():
    parser = argparse.ArgumentParser(description='Initialize project memory')
    parser.add_argument('--name', required=True, help='Project name')
    parser.add_argument('--path', required=True, help='Project directory path')
    parser.add_argument('--type', choices=PROJECT_TYPES, default='general',
                       help='Project type')
    args = parser.parse_args()
    
    project_path = Path(args.path)
    memory_path = Path.home() / 'project-memory' / project_path.name
    
    # Create directory structure
    dirs = [
        memory_path / 'current',
        memory_path / 'checkpoints',
        memory_path / 'knowledge',
        memory_path / 'knowledge' / 'references',
        memory_path / 'index'
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    # Create state.json
    state = {
        'name': args.name,
        'type': args.type,
        'path': str(project_path),
        'memory_path': str(memory_path),
        'created': datetime.utcnow().isoformat() + 'Z',
        'last_checkpoint': None,
        'last_session': None,
        'active_priority': None,
        'metrics': {
            'checkpoints': 0,
            'decisions': 0,
            'facts': 0
        },
        'context_summary': 'Project initialized'
    }
    
    with open(memory_path / 'current' / 'state.json', 'w') as f:
        json.dump(state, f, indent=2)
    
    # Create empty context.md
    with open(memory_path / 'current' / 'context.md', 'w') as f:
        f.write(f'# {args.name}\n\nProject initialized.\n')
    
    # Create empty knowledge files
    with open(memory_path / 'knowledge' / 'facts.json', 'w') as f:
        json.dump([], f)
    with open(memory_path / 'knowledge' / 'decisions.json', 'w') as f:
        json.dump([], f)
    
    print(f'Project memory initialized: {memory_path}')
    print(f'Type: {args.type}')
    print(f'Original path: {project_path}')

if __name__ == '__main__':
    main()
