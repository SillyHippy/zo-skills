---
name: zo-tools
description: Internal process tools for Zo and Hermes — local search, document processing, OCR, and embeddings. All services run on localhost, zero HTTP slots consumed.
compatibility: Zo Computer, Hermes Agent
---

# Zo Tools

Four localhost services deployed as `mode="process"` — always running, instant access.

## 🔍 zo-search (port 4100)
Full-text search across workspace files using ripgrep + PDF text extraction.

```
GET /search?q=query&path=/home/workspace  — search file contents
GET /search-pdf?q=query                  — search PDF text
```

## 📄 zo-docs (port 4200)
PDF and document manipulation using qpdf, pandoc, pdftotext.

```
GET  /extract?file=/path/to/doc.pdf       — extract text from PDF
POST /extract  {file: "..."}              — same, POST with body
POST /merge    {files: ["a.pdf","b.pdf"]} — merge PDFs
POST /split    {file: "...", pages: "1-3"}— split PDF
POST /convert  {file: "...", to: "md"}    — convert formats via pandoc
GET  /info?file=...                       — page count, size
```

## 👁️ zo-ocr (port 4300)
OCR via Tesseract — extract text from images and scanned PDFs.

```
POST /ocr      {file: "/path/to/scan.png", lang: "eng"}
POST /ocr-url  {url: "https://...", lang: "eng"}
```

## 🧠 zo-embed (port 4400)
Text embeddings + semantic search. Uses local hash-based embeddings (no model download needed).

```
POST /embed    {text: "hello world"}       → {id, vector}
POST /search   {text: "query", limit: 10}  → ranked results
POST /store    {text: "...", source: "..."} → store for later search
GET  /stats                                → entry count
```

## How Zo/Hermes calls these
Services are bound to `127.0.0.1` only. Use:

```
http://127.0.0.1:4100/search?q=affidavit
http://127.0.0.1:4200/extract?file=/home/workspace/Documents/file.pdf
http://127.0.0.1:4300/ocr
http://127.0.0.1:4400/embed
```

All services auto-start on boot and restart on crash. No HTTP service slots consumed.
