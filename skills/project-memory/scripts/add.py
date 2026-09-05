#!/usr/bin/env python3
"""Add facts, decisions, or references to project memory."""

import argparse
import json
from datetime import datetime
from pathlib import Path

def add_fact(memory_path: Path, fact: str, source: str = None):
    """Add a fact to knowledge."""
    facts_file = memory_path / 'knowledge' / 'facts.json'
    
    with open(facts_file) as f:
        facts = json.load(f)
    
    entry = {
        'fact': fact,
        'source': source,
        'added': datetime.utcnow().isoformat() + 'Z'
    }
    facts.append(entry)
    
    with open(facts_file, 'w') as f:
        json.dump(facts, f, indent=2)
    
    print(f'Fact added: {fact[:60]}...' if len(fact) > 60 else f'Fact added: {fact}')

def add_decision(memory_path: Path, decision: str, reason: str = None):
    """Add a decision to knowledge."""
    decisions_file = memory_path / 'knowledge' / 'decisions.json'
    
    with open(decisions_file) as f:
        decisions = json.load(f)
    
    entry = {
        'decision': decision,
        'reason': reason,
        'made': datetime.utcnow().isoformat() + 'Z'
    }
    decisions.append(entry)
    
    with open(decisions_file, 'w') as f:
        json.dump(decisions, f, indent=2)
    
    print(f'Decision added: {decision[:60]}...' if len(decision) > 60 else f'Decision added: {decision}')

def add_reference(memory_path: Path, name: str, path: str, description: str = None):
    """Add a file reference."""
    refs_file = memory_path / 'knowledge' / 'references.json'
    
    refs = []
    if refs_file.exists():
        with open(refs_file) as f:
            refs = json.load(f)
    
    entry = {
        'name': name,
        'path': path,
        'description': description,
        'added': datetime.utcnow().isoformat() + 'Z'
    }
    refs.append(entry)
    
    with open(refs_file, 'w') as f:
        json.dump(refs, f, indent=2)
    
    print(f'Reference added: {name} -> {path}')

def main():
    parser = argparse.ArgumentParser(description='Add to project memory')
    parser.add_argument('--project', required=True, help='Project memory path')
    parser.add_argument('--type', choices=['fact', 'decision', 'reference'], required=True)
    parser.add_argument('--content', help='Content (for fact/decision)')
    parser.add_argument('--name', help='Name (for reference)')
    parser.add_argument('--path', help='Path (for reference)')
    parser.add_argument('--source', help='Source (for fact)')
    parser.add_argument('--reason', help='Reason (for decision)')
    parser.add_argument('--description', help='Description (for reference)')
    args = parser.parse_args()
    
    memory_path = Path(args.project)
    if not memory_path.exists():
        memory_path = Path.home() / 'project-memory' / Path(args.project).name
    
    if not memory_path.exists():
        print(f'Project not found: {args.project}')
        return 1
    
    if args.type == 'fact':
        if not args.content:
            print('--content required for fact')
            return 1
        add_fact(memory_path, args.content, args.source)
    elif args.type == 'decision':
        if not args.content:
            print('--content required for decision')
            return 1
        add_decision(memory_path, args.content, args.reason)
    elif args.type == 'reference':
        if not args.name or not args.path:
            print('--name and --path required for reference')
            return 1
        add_reference(memory_path, args.name, args.path, args.description)

if __name__ == '__main__':
    main()
