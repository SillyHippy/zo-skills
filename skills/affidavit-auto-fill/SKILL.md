---
name: affidavit-auto-fill
description: Use when creating a ServeTracker affidavit. Use its engine only.
---

# ServeTracker Affidavit Auto-Fill — Sole Canonical Workflow

The sole source of an affidavit is the live ServeTracker engine:

- Staging: `/home/workspace/Projects/PDFUSAEDIT-staging/src/utils/affidavitEngine.ts`
- Production: `/home/workspace/Projects/PDFUSAEDIT-zo/src/utils/affidavitEngine.ts`

Use the staging source for development and testing. Never mutate production unless Joseph explicitly directs promotion.

## Prohibited paths

Never use:

- NAPPS forms, templates, field maps, or fillers.
- A court-issued Return of Service, declaration, or proof-of-service form unless Joseph expressly asks for that separate document.
- `affidavit-filler`, `affidavit-search-fill`, `fill_affidavit.py`, `make_affidavit.py`, or any static-PDF template.
- A separate HTML/WeasyPrint/Ghostscript affidavit generator.

## Required facts and verification

Read the live ServeTracker recipient, court caption, exact documents, and all attempts. Preserve chronological physical attempts and derive sworn wording from the recorded service method. Keep an entity recipient, accepting natural person, and accepting capacity separate. Never default missing method data to personal service. Do not expose the internal product name in the client/court-facing artifact.

Run `bun test tests/affidavit_engine.test.ts` in staging before reporting a workflow or code change as verified.
