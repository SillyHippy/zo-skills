#!/usr/bin/env python3
"""Search project memory."""

import argparse
import json
import re
from pathlib import Path

def search_checkpoints(memory_path: Path, query: str):
    """Search all checkpoints for query."""
    checkpoints_dir = memory_path / 'checkpoints'
    if not checkpoints_dir.exists():
        print('No checkpoints found')
        return
    
    query_lower = query.lower()
    matches = []
    
    for checkpoint_file in sorted(checkpoints_dir.glob('checkpoint-*.json')):
        with open(checkpoint_file) as f:
            checkpoint = json.load(f)
        
        # Search in summary
        if query_lower in checkpoint['summary'].lower():
            matches.append((checkpoint['checkpoint_id'], 'summary', checkpoint['summary']))
            continue
        
        # Search in decisions
        for decision in checkpoint['decisions']:
            if query_lower in decision.lower():
                matches.append((checkpoint['checkpoint_id'], 'decision', decision))
                break
        
        # Search in facts
        for fact in checkpoint['facts_learned']:
            if query_lower in fact.lower():
                matches.append((checkpoint['checkpoint_id'], 'fact', fact))
                break
    
    if not matches:
        print(f'No results for: {query}')
        return
    
    print(f'Found {len(matches)} results for: {query}')
    print()
    
    for checkpoint_id, field, content in matches:
        print(f'[{checkpoint_id}] {field}:')
        print(f'  {content[:200]}...' if len(content) > 200 else f'  {content}')
        print()

def search_facts(memory_path: Path, query: str):
    """Search facts."""
    facts_file = memory_path / 'knowledge' / 'facts.json'
    if not facts_file.exists():
        print('No facts found')
        return
    
    with open(facts_file) as f:
        facts = json.load(f)
    
    query_lower = query.lower()
    matches = [f for f in facts if query_lower in f.lower()]
    
    if not matches:
        print(f'No facts matching: {query}')
        return
    
    print(f'Found {len(matches)} facts:')
    for fact in matches:
        print(f'  - {fact}')

def search_decisions(memory_path: Path, query: str):
    """Search decisions."""
    decisions_file = memory_path / 'knowledge' / 'decisions.json'
    if not decisions_file.exists():
        print('No decisions found')
        return
    
    with open(decisions_file) as f:
        decisions = json.load(f)
    
    query_lower = query.lower()
    matches = [d for d in decisions if query_lower in d.lower()]
    
    if not matches:
        print(f'No decisions matching: {query}')
        return
    
    print(f'Found {len(matches)} decisions:')
    for decision in matches:
        print(f'  - {decision}')

def list_checkpoints(memory_path: Path):
    """List all checkpoints."""
    checkpoints_dir = memory_path / 'checkpoints'
    if not checkpoints_dir.exists():
        print('No checkpoints')
        return
    
    files = sorted(checkpoints_dir.glob('checkpoint-*.json'))
    print(f'Total checkpoints: {len(files)}')
    print()
    
    for f in files:
        with open(f) as fp:
            checkpoint = json.load(fp)
        print(f"{checkpoint['checkpoint_id']} ({checkpoint['timestamp'][:10]})")
        print(f"  {checkpoint['summary'][:80]}...")
        print()

def main():
    parser = argparse.ArgumentParser(description='Search project memory')
    parser.add_argument('--project', required=True, help='Project memory path')
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--type', choices=['checkpoints', 'facts', 'decisions', 'list'],
                       default='checkpoints', help='What to search')
    args = parser.parse_args()
    
    memory_path = Path(args.project)
    if not memory_path.exists():
        memory_path = Path.home() / 'project-memory' / Path(args.project).name
    
    if not memory_path.exists():
        print(f'Project not found: {args.project}')
        return 1
    
    if args.type == 'list':
        list_checkpoints(memory_path)
    elif args.type == 'checkpoints':
        if not args.query:
            print('--query required for checkpoints search')
            return 1
        search_checkpoints(memory_path, args.query)
    elif args.type == 'facts':
        if not args.query:
            print('--query required for facts search')
            return 1
        search_facts(memory_path, args.query)
    elif args.type == 'decisions':
        if not args.query:
            print('--query required for decisions search')
            return 1
        search_decisions(memory_path, args.query)

if __name__ == '__main__':
    main()
