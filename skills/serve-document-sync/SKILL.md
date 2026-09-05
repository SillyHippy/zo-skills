---
name: serve-document-sync
description: Download serve documents from Proof (app.proofserve.com) and upload them to the correct pre-made Google Drive folders under the "Site Upload" directory. Requires Proof credentials and Google Drive OAuth.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
  category: Process Serving
---

# Serve Document Sync

Downloads serve-document PDFs from Proof jobs and places each one into its matching pre-made Google Drive folder.

## Requirements

- **Proof account** (app.proofserve.com) with credentials stored in [Settings > Advanced](/?t=settings&s=advanced):
  - `PROOF_USERNAME` — e.g. `Joseph@JustLegalSolutions.org`
  - `PROOF_PASSWORD` — e.g. `Crazy8809!`
- **Google Drive OAuth** already connected to Zo (iannazzi.joseph@gmail.com)
- Pre-made folders in Google Drive under "Site Upload" matching job names

## What it does

1. Logs into Proof
2. Navigates to the jobs list
3. For each configured job, clicks into the job and clicks "Download Serve Documents"
4. Waits for the download to complete
5. Finds the matching Google Drive folder by name
6. Uploads the PDF directly into that folder
7. Cleans up any duplicate files left at the Drive root

## Usage

Run the sync for all configured jobs:

```bash
cd /home/workspace/Skills/serve-document-sync/scripts
bun run sync.ts
```

Or run for a single job:

```bash
bun run sync.ts --job "NICOLE DIANE HANSEN"
```

## Files

- `scripts/sync.ts` — Main sync script
- `scripts/config.ts` — Job configuration (name, Proof job ID, Drive folder ID)