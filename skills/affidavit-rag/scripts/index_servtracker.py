#!/usr/bin/env python3
"""Index ServTracker data into Qdrant for RAG."""

import sqlite3
import requests
import json
import os
from datetime import datetime

QDRANT_URL = "http://localhost:6333"
ZO_EMBED_URL = "http://localhost:4400"
DB_PATH = "/home/workspace/Projects/PDFUSAEDIT-zo/data/pdfusaedit.db"

def get_embedding(text):
    """Get embedding from zo-embed service."""
    try:
        resp = requests.post(f"{ZO_EMBED_URL}/embed", json={"text": text}, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("embedding", [])
        return None
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

def create_collections():
    """Create Qdrant collections if they don't exist."""
    collections = ["cases", "serve_attempts", "addresses"]
    
    for collection in collections:
        try:
            # Check if collection exists
            resp = requests.get(f"{QDRANT_URL}/collections/{collection}")
            if resp.status_code == 404:
                # Create collection
                requests.put(f"{QDRANT_URL}/collections/{collection}", json={
                    "vectors": {
                        "size": 128,
                        "distance": "Cosine"
                    }
                })
                print(f"Created collection: {collection}")
            else:
                print(f"Collection exists: {collection}")
        except Exception as e:
            print(f"Collection error: {e}")

def index_cases():
    """Index all cases from ServTracker."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cases = cursor.execute("SELECT * FROM client_cases").fetchall()
    print(f"Found {len(cases)} cases to index")
    
    for case in cases:
        case_dict = dict(case)
        
        # Create embedding text
        text = f"Case {case_dict.get('case_number', '')}: {case_dict.get('plaintiff_petitioner', '')} vs {case_dict.get('defendant_respondent', '')} in {case_dict.get('court_name', '')}. Address: {case_dict.get('home_address', '')}. Status: {case_dict.get('status', '')}."
        
        vector = get_embedding(text)
        if vector:
            # Store in Qdrant
            payload = {
                "case_number": case_dict.get('case_number', ''),
                "court": case_dict.get('court_name', ''),
                "plaintiff": case_dict.get('plaintiff_petitioner', ''),
                "defendant": case_dict.get('defendant_respondent', ''),
                "address": case_dict.get('home_address', ''),
                "status": case_dict.get('status', ''),
                "text": text
            }
            
            try:
                requests.put(f"{QDRANT_URL}/collections/cases/points", json={
                    "points": [{
                        "id": case_dict.get('id', str(hash(text))),
                        "vector": vector,
                        "payload": payload
                    }]
                })
                print(f"Indexed case: {case_dict.get('case_number', 'unknown')}")
            except Exception as e:
                print(f"Error indexing case: {e}")
    
    conn.close()

def index_serve_attempts():
    """Index all serve attempts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    attempts = cursor.execute("SELECT * FROM serve_attempts").fetchall()
    print(f"Found {len(attempts)} serve attempts to index")
    
    for attempt in attempts:
        attempt_dict = dict(attempt)
        
        # Create embedding text
        text = f"Service attempt on {attempt_dict.get('case_number', '')} at {attempt_dict.get('address', '')}. Outcome: {attempt_dict.get('status', '')}. Notes: {attempt_dict.get('notes', '')}"
        
        vector = get_embedding(text)
        if vector:
            payload = {
                "case_number": attempt_dict.get('case_number', ''),
                "address": attempt_dict.get('address', ''),
                "service_address": attempt_dict.get('service_address', ''),
                "status": attempt_dict.get('status', ''),
                "notes": attempt_dict.get('notes', ''),
                "attempt_number": attempt_dict.get('attempt_number', 1),
                "text": text
            }
            
            try:
                requests.put(f"{QDRANT_URL}/collections/serve_attempts/points", json={
                    "points": [{
                        "id": attempt_dict.get('id', str(hash(text))),
                        "vector": vector,
                        "payload": payload
                    }]
                })
                print(f"Indexed serve attempt: {attempt_dict.get('case_number', 'unknown')}")
            except Exception as e:
                print(f"Error indexing attempt: {e}")
    
    conn.close()

def index_addresses():
    """Index unique addresses with service history."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all unique addresses from cases and attempts
    addresses = cursor.execute("""
        SELECT home_address as address, COUNT(*) as case_count,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success_count
        FROM client_cases 
        WHERE home_address IS NOT NULL AND home_address != ''
        GROUP BY home_address
    """).fetchall()
    
    print(f"Found {len(addresses)} unique addresses to index")
    
    for addr in addresses:
        addr_dict = dict(addr)
        address = addr_dict.get('address', '')
        
        if not address:
            continue
        
        text = f"Address: {address}. Served {addr_dict.get('case_count', 0)} times. Success rate: {addr_dict.get('success_count', 0)}/{addr_dict.get('case_count', 1)}."
        
        vector = get_embedding(text)
        if vector:
            payload = {
                "address": address,
                "case_count": addr_dict.get('case_count', 0),
                "success_count": addr_dict.get('success_count', 0),
                "text": text
            }
            
            try:
                requests.put(f"{QDRANT_URL}/collections/addresses/points", json={
                    "points": [{
                        "id": str(hash(address)),
                        "vector": vector,
                        "payload": payload
                    }]
                })
                print(f"Indexed address: {address[:50]}...")
            except Exception as e:
                print(f"Error indexing address: {e}")
    
    conn.close()

if __name__ == "__main__":
    print("Starting ServTracker RAG indexing...")
    print(f"Database: {DB_PATH}")
    print(f"Qdrant: {QDRANT_URL}")
    print(f"Embed: {ZO_EMBED_URL}")
    
    create_collections()
    index_cases()
    index_serve_attempts()
    index_addresses()
    
    print("\nIndexing complete!")
