---
name: legal-pipeline
description: |
  Legacy legal PDF ingestion wrapper. Use the dedicated generators for normal jobs and preserve exception routing.
---

# Legal Pipeline

## Authority

The authoritative normal-client generators are:

- `field-sheet-generator/scripts/generate_field_sheet.py` — canonical field sheet with address separation, HTML review, and PDF verification.
- `affidavit-auto-fill` — the sole canonical ServeTracker affidavit engine workflow.

Legacy PDF-ingestion wrappers that generated affidavits have been removed. Do not recreate them.

## Mandatory classification

- ABC Legal: PDF-only. No field sheet, Drive folder, or ServTracker case.
- Proof Serve: PDF processing plus evidence folder only. No field sheet or ServTracker case.
- Normal client: use the dedicated generators and the authorized ServTracker/Drive workflow.
- Unclear classification: stop and ask Joe.

## Canonical outputs

All local normal-client outputs belong under:

`/home/workspace/justlegalsolutions/cases/`

- `{CaseNumber}_Field_Sheet.html`
- `{CaseNumber}_Field_Sheet.pdf`
- `{CaseNumber}_Affidavit.pdf`
- `{CaseNumber}_fields.json`

Do not use the old `output/`, `/home/workspace/Output/`, or `Documents/FieldSheets` paths for new generation.


## Safety

- No ServeTracker/SQLite writes without Joe's explicit authorization.
- No Google Drive creation, deletion, or upload without Joe's explicit authorization.
- Do not claim a document was generated until it is reopened and validated.
- ABC Legal and Proof Serve exceptions must be classified before any normal-client step.