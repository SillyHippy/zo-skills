#!/usr/bin/env python3
"""Query RAG system for affidavit suggestions."""

import argparse
import requests
import json
import sys

QDRANT_URL = "http://localhost:6333"
ZO_EMBED_URL = "http://localhost:4400"

def get_embedding(text):
    """Get embedding from zo-embed service."""
    try:
        resp = requests.post(f"{ZO_EMBED_URL}/embed", json={"text": text}, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("embedding", [])
        return None
    except Exception as e:
        print(f"Embedding error: {e}", file=sys.stderr)
        return None

def search_similar_cases(case_number, limit=3):
    """Find cases similar to the given case number."""
    # First get the case details
    import sqlite3
    conn = sqlite3.connect("/home/workspace/Projects/PDFUSAEDIT-zo/data/pdfusaedit.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    case = cursor.execute(
        "SELECT * FROM client_cases WHERE case_number = ?",
        (case_number,)
    ).fetchone()
    conn.close()
    
    if not case:
        print(f"Case {case_number} not found")
        return []
    
    case_dict = dict(case)
    query_text = f"{case_dict.get('court_name', '')} {case_dict.get('plaintiff_petitioner', '')} vs {case_dict.get('defendant_respondent', '')}"
    
    vector = get_embedding(query_text)
    if not vector:
        return []
    
    try:
        resp = requests.post(
            f"{QDRANT_URL}/collections/cases/points/search",
            json={"vector": vector, "limit": limit + 1}  # +1 to exclude self
        )
        results = resp.json().get("result", [])
        
        # Filter out the exact case match
        filtered = [r for r in results if r.get("payload", {}).get("case_number") != case_number]
        return filtered[:limit]
    except Exception as e:
        print(f"Search error: {e}", file=sys.stderr)
        return []

def suggest_description(defendant, address, limit=1):
    """Suggest service description based on similar serves."""
    query_text = f"service description {defendant} at {address}"
    
    vector = get_embedding(query_text)
    if not vector:
        return []
    
    try:
        resp = requests.post(
            f"{QDRANT_URL}/collections/serve_attempts/points/search",
            json={
                "vector": vector,
                "filter": {"must": [{"key": "status", "match": {"value": "completed"}}]},
                "limit": limit
            }
        )
        return resp.json().get("result", [])
    except Exception as e:
        print(f"Search error: {e}", file=sys.stderr)
        return []

def check_address_history(address, limit=5):
    """Check service history for an address."""
    vector = get_embedding(address)
    if not vector:
        return []
    
    try:
        resp = requests.post(
            f"{QDRANT_URL}/collections/addresses/points/search",
            json={"vector": vector, "limit": limit}
        )
        return resp.json().get("result", [])
    except Exception as e:
        print(f"Search error: {e}", file=sys.stderr)
        return []

def main():
    parser = argparse.ArgumentParser(description="Query RAG system for affidavit suggestions")
    parser.add_argument("--type", choices=["similar-cases", "description", "address-history"], required=True)
    parser.add_argument("--case-number", help="Case number for similar-cases query")
    parser.add_argument("--defendant", help="Defendant name for description query")
    parser.add_argument("--address", help="Address for query")
    parser.add_argument("--limit", type=int, default=3, help="Number of results")
    
    args = parser.parse_args()
    
    if args.type == "similar-cases":
        if not args.case_number:
            print("--case-number required for similar-cases")
            sys.exit(1)
        results = search_similar_cases(args.case_number, args.limit)
        print(json.dumps(results, indent=2))
    
    elif args.type == "description":
        if not args.defendant or not args.address:
            print("--defendant and --address required for description")
            sys.exit(1)
        results = suggest_description(args.defendant, args.address, args.limit)
        print(json.dumps(results, indent=2))
    
    elif args.type == "address-history":
        if not args.address:
            print("--address required for address-history")
            sys.exit(1)
        results = check_address_history(args.address, args.limit)
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
