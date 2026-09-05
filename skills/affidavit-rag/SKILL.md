---
name: affidavit-rag
description: RAG (Retrieval-Augmented Generation) system for affidavit workflows. Enables semantic search across cases, service attempts, and addresses to suggest descriptions and find similar cases.
---

## Commands

### Index existing data
```bash
python3 Skills/affidavit-rag/scripts/index_servtracker.py
```

### Query for similar cases
```bash
python3 Skills/affidavit-rag/scripts/query.py --case-number "DC-26-08548" --type similar-cases
```

### Suggest service description
```bash
python3 Skills/affidavit-rag/scripts/query.py --defendant "John Smith" --address "Tulsa OK" --type description
```

### Check address history
```bash
python3 Skills/affidavit-rag/scripts/query.py --address "123 Main St" --type address-history
```

## API Endpoints

- POST http://localhost:4400/search — Semantic search
- POST http://localhost:4400/store — Store document
- POST http://localhost:4400/ingest-ocr — Ingest OCR text

## Collections

- cases — Case metadata and embeddings
- serve_attempts — Service attempt notes
- addresses — Address history with outcomes
