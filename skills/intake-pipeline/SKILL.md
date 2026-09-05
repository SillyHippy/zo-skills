---
name: intake-pipeline
description: >
  Automatic intake for process serving. Drop a client email + petition PDF,
  I extract details, create the case in ServTracker, generate the field sheet,
  and upload docs to Google Drive. Chains existing skills — no new code needed.
---

# Intake Pipeline

## When to run

Client emails a case to Joe. He forwards/pastes the email here, often with a petition PDF attached. Run this workflow.

## Mandatory classification gate

Before creating a case, field sheet, Drive folder, or uploading anything, classify the packet:

- **ABC Legal** — PDF processing only. Do not create a field sheet, Drive folder, or ServTracker case.
- **Proof Serve** — Process the PDFs and create/reuse a Site Upload evidence folder for recordings/evidence only. Do not create a field sheet or ServTracker case.
- **Normal client** — Continue with the standard workflow below.

If the classification is unclear, stop and ask Joe. Never silently treat an exception packet as a normal client.

## Pipeline steps — normal client only

1. **Extract & Preserve Court Pleadings** — Read the client email and identify the actual court pleading PDF (e.g. `pdf24_converted.pdf` or complete court scan). Never attach a 1-page Gmail cover printout with attachment thumbnails as the court pleading document. Extract:
   - **Court Name (full caption)** from petition (e.g. `IN THE DISTRICT COURT IN AND FOR TULSA COUNTY STATE OF OKLAHOMA` — not county-only)
   - Plaintiff/Petitioner (from petition)
   - **Person Being Served** / Defendant/Respondent (from petition)
   - Case number (from petition / verified court docket)
   - Service address from the email or explicit override, never a courthouse/header address
   - Separate primary + **secondary** addresses (ServeTracker: `home_address` + `work_address`); fail closed if ambiguous
   - Documents being served (from petition — scan all pages)
   - Client name/reference (from email)
   - Operational notes: target aliases, hearing dates/locations, vehicle descriptions. **Never include internal Drive folder IDs, invoice tokens, or system debug strings.**

2. **Helcim invoice** — Run idempotency check `check_invoice.py` first. If an invoice is DUE, reuse it; never create duplicates. Verify INV # + pay URL.

3. **Field sheet** — ServeTracker dynamically renders Field Sheets in the browser (`fieldSheetPdfEngine.ts`). Do NOT attach field sheets to `client_documents`.

4. **Google Drive** — Upload the actual multi-page court pleading PDF under `Site Upload` case folder; verify non-zero size.

5. **ServeTracker** — Search before create on **production** `:3150`. Map `case_name` = Person Being Served, `defendant_respondent` same, `court_name` = full caption, `status` = Open. **Attach only legal court pleadings to `client_documents` — never attach generated Field Sheets.**

6. **Affidavit** — Later, after service: `affidavit-auto-fill` using the live ServeTracker engine — not a NAPPS form, court return, declaration/proof form, or static PDF template.

7. **Report** — Claim generation/upload only after inspecting outputs and returned Drive/file IDs / INV read-back.

## Tools used

| Tool | What it does |
|------|-------------|
| `file Skills/field-sheet-generator/SKILL.md` | Generate field sheet PDF |
| `file Skills/servtracker/SKILL.md` | SQLite access to ServTracker DB |
| OCR (localhost:4300) | Extract text from scanned PDFs |
| Google Drive | Upload case files |

## Canonical output contract

- Field sheet: `/home/workspace/justlegalsolutions/cases/{CaseNumber}_Field_Sheet.pdf`
- Affidavit: `/home/workspace/justlegalsolutions/cases/{CaseNumber}_Affidavit.pdf`
- HTML review artifact: `/home/workspace/justlegalsolutions/cases/{CaseNumber}_Field_Sheet.html`
- Extracted metadata, if retained: `/home/workspace/justlegalsolutions/cases/{CaseNumber}_fields.json`
- ServTracker and Drive changes are separate authorized operations, not implied by local generation.
