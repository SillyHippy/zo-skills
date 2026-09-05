---
name: servetracker-beta-hermes-intake
description: >
  Foolproof Hermes checklist for ServeTracker BETA intake: documents → Helcim
  invoice → field sheet → Google Drive folder → ServeTracker beta client/case.
  Use when Joseph says intake, new case, put in ServeTracker beta, make invoice,
  field sheet, Drive folder, or tests the beta app. Eventually promote to
  production after beta is proven — keep targets explicit.
version: 1.1.0
---

# ServeTracker Beta — Hermes Intake Skill (Foolproof Checklist)

**Audience:** Any AI model running in Hermes. Follow this skill literally.  
**Scope today:** **BETA only** unless Joseph says “production.”  
**Goal:** One clean intake that cannot be half-done or silently wrong.

Load companion skills when needed:
- `agent-accuracy-guard` (before completion claims)
- `process-serving-toolkit` → `references/new-service-job-intake.md`
- `process-serving-intake-operations`
- `helcim-invoice`, `google-workspace` (`google_api.py` only — Drive via Composio is BANNED)

---

## Hard rules (never violate)

1. **Confirm target environment** before any write: beta vs production.
2. **Search before create** (clients AND cases). Never invent duplicates.
3. **Confirm fee** with Joseph before Helcim create — never invent amounts.
4. **Client name REQUIRED** or ServeTracker cannot log attempts.
5. **Shell `$` in notes:** use single-quoted JSON / Helcim notes (`'$80'`).
6. **Drive:** only `google_api.py`. Never Composio Drive. Verify non-zero file size.
7. **Do not claim done** until every read-back check in §VERIFY passes.
8. **ABC Legal / Proof Serve exceptions:** classify first — those skip ServeTracker/field sheet as documented in `intake-pipeline`.
9. **No PSL/PSS in client emails.** Affidavit license blank unless filing a named server’s wet-ink copy.
10. **Production stays untouched** during beta intake tests.

---

## Environments (copy exactly)

| | API | Public URL | DB / DATA_DIR |
|---|---|---|---|
| **BETA (default for this skill)** | `http://localhost:3151` | `https://servetracker-beta-sillyhippy.zocomputer.io` | Confirm isolation: `/home/workspace/Projects/PDFUSAEDIT-zo-beta/data/` — do not write test junk into production DB |
| **PRODUCTION (only if Joseph says so)** | `http://localhost:3150` | production reverse-proxy host | `/home/workspace/Projects/PDFUSAEDIT-zo/data/pdfusaedit.db` |

Login: `POST {API}/api/auth/login` body `{"password":"$APP_PASSWORD"}` (from env / service config). Save cookie jar. Never print passwords into MEMORY.md or Telegram.

---

## Field map (UI → API/DB) — get this wrong and PBS breaks

| Meaning | API / DB field | Rule |
|---|---|---|
| **Person Being Served** | `case_name` **and** `defendant_respondent` | Same person. ALL CAPS when known. Primary identity in New Serve. |
| **Court Name (full caption)** | `court_name` | Free text, e.g. `IN THE DISTRICT COURT IN AND FOR TULSA COUNTY STATE OF OKLAHOMA` — **not** county-only. |
| Plaintiff / Petitioner | `plaintiff_petitioner` | Caption plaintiff / hiring-side party. |
| Primary / Home service address | `home_address` | Navigation / map address. |
| **Secondary Address** | `work_address` | Second location OR legal residence when home is stakeout. |
| **Documents to Serve** | `documents_to_serve` | Exact pleading titles; feeds affidavit Documents line. Also keep titles in notes if needed. |
| Notes | `notes` | Filing date, vehicle/plate, rush, fee note — not a substitute for Documents to Serve. |
| Status | `status` | Intake: `active` (canonical in ServeTracker UI). Both `client_cases.status` AND `serve_recipients.status` MUST be set to `active` (never 'open', 'Open', or 'Pending'). Closed later: `closed` (case-insensitive). |

Roles never conflated: (1) **client who hired**, (2) **person served**, (3) **affidavit recipient**.

UX + email + affidavit preferences: **`references/servetracker-beta-ux-and-affidavit.md`** (active-cases-only, PBS default, photo links, ORIGINAL template for court affidavits).

---

## Master checklist (do in order — tick every box)

### 0) Preflight
- [ ] Load this skill + `agent-accuracy-guard`
- [ ] Confirm Joseph wants **beta** (this skill) or production
- [ ] Classify packet: Normal / ABC Legal / Proof Serve — stop if exception
- [ ] List incoming files (email + PDFs). Extract with `pdftotext -layout`

### 1) Extract (do not invent)
- [ ] Case number
- [ ] Court Name **full caption**
- [ ] Plaintiff / Petitioner
- [ ] **Person Being Served** (defendant/respondent)
- [ ] Primary service address (+ secondary if present)
- [ ] Exact document titles to serve
- [ ] Client name + billing email + phone
- [ ] Fee (only if Joseph stated it) + rush notes / vehicle / DL info if present

If any of case #, PBS, address, or client email is missing → **STOP and ask**. Do not guess.

### 2) Fee / Helcim
- [ ] Fee confirmed with Joseph (or already stated this turn)
- [ ] Run:  
  `python3 /home/workspace/Skills/helcim-invoice/scripts/create_invoice.py --name 'CLIENT' --email 'BILLING@EMAIL' --line 'Standard Process Service - CASE|AMOUNT' --notes '...'`  
  (exact flags per `helcim-invoice` skill; single-quote `$`)
- [ ] Read back: INV #, amount, status DUE, billing email, pay URL `https://just-legal-solutions.myhelcim.com/order/?token=...`
- [ ] Client said “invoice after service” → still **create Helcim at intake**; deliver affidavit+invoice to client after serve

### 3) ServeTracker beta — client
- [ ] `GET /api/clients` — search name substring; reuse if found
- [ ] Else `POST /api/clients` with **name**, email, phone, address, notes
- [ ] Read back client `id` + name non-empty

### 4) ServeTracker beta — case
- [ ] `GET /api/cases` — search case_number + defendant; reuse if found
- [ ] Else `POST /api/cases` with **all** of:
  - `client_id`
  - `case_number`
  - `case_name` = Person Being Served
  - `defendant_respondent` = same
  - `court_name` = full caption
  - `plaintiff_petitioner`
  - `home_address`, `work_address` (Secondary)
  - `documents_to_serve` = exact document titles (semicolon-separated)
  - `notes`, `status: "active"`
- [ ] Read back: case id, case_number, defendant, addresses, documents_to_serve, status active (both case and recipient row)
- [ ] Confirm New Serve would show this case under **Active** (not closed)

### 5) Field sheet
- [ ] Generate via `/home/workspace/Skills/field-sheet-generator/scripts/generate_field_sheet.py` (or project’s documented entrypoint)
- [ ] Leave Notes/Comments + Attempt Log **blank** for handwriting
- [ ] Ghostscript normalize to PDF 1.4 when WeasyPrint used
- [ ] `pdftotext` — no leftover `{placeholders}`
- [ ] Canonical path under `/home/workspace/justlegalsolutions/cases/{Case}_Field_Sheet.pdf` when applicable
- [ ] Deliver `MEDIA:/absolute/path` on Telegram when user is on mobile

### 6) Google Drive folder
- [ ] Parent Site Upload: `1ZB7XTSC_eD6m3F-6_yI2VP065cKEQzVq`
- [ ] Create folder named by **case number**:  
  `python3 .../google_api.py drive create-folder "CASE#" --parent "1ZB7XTSC_eD6m3F-6_yI2VP065cKEQzVq"`
- [ ] Upload petition/summons/docs + field sheet with `--parent FOLDER_ID`
- [ ] `drive search --raw-query "'FOLDER_ID' in parents and trashed=false"`
- [ ] Every uploaded file **size > 0** (hash/round-trip when possible)

### 7) Optional fast-affidavit capture
- [ ] If petition available: `capture_caption.py --case-number CASE --petition PDF` (affidavit-filler) — curate documents line; do not invent parties

### 8) VERIFY report (required before “done”)
Report to Joseph with **verified** values only:
- [ ] Environment: BETA
- [ ] ServeTracker client id + name
- [ ] Case number + PBS + court caption + status
- [ ] Helcim INV # + pay URL
- [ ] Drive folder id/URL + file count (non-zero sizes)
- [ ] Field sheet path + MEDIA delivered
- [ ] Still for Joseph: physical attempts → later affidavit

**Incomplete = not done.** Missing any read-back → do not say complete.

---

## Curl patterns (beta)

```bash
# Login
curl -s -c /tmp/st_beta.txt -H 'Content-Type: application/json' \
  -d '{"password":"'"$APP_PASSWORD"'"}' \
  http://localhost:3151/api/auth/login

# Search clients / cases
curl -s -b /tmp/st_beta.txt http://localhost:3151/api/clients | python3 -m json.tool | head
curl -s -b /tmp/st_beta.txt http://localhost:3151/api/cases | python3 -m json.tool | head

# Create client (example — fill real values; single-quote JSON)
curl -s -b /tmp/st_beta.txt -H 'Content-Type: application/json' \
  -d '{"name":"Client Name","email":"a@b.com","phone":"","address":"","notes":""}' \
  http://localhost:3151/api/clients
```

---

## Explicitly OUT OF SCOPE (do not build during intake)

| Item | Status |
|---|---|
| Court Name field in UI | Already exists — fill `court_name` only |
| Drive upload on **successful serve** auto-hook | Deferred — flag OFF; see Plans/ServeTracker_Drive_On_Success.md |
| Contractor / multi-server RBAC | Deferred — research later; email already has no PSL |

---

## Promotion to production (later)

When Joseph says beta is proven:
1. Change API targets in this skill from `:3151` → `:3150`
2. Re-verify one real intake end-to-end on production
3. Keep confirm gates; keep search-before-create
4. Do **not** enable Drive-on-success until hash-verify is proven

---

## Related references in this skill

- `references/VERIFY_CHECKLIST.md` — short copy-paste gate
- `references/servetracker-beta-ux-and-affidavit.md` — New Serve UX, email photo links, affidavit ORIGINAL-template preference
- Toolkit: `process-serving-toolkit/references/new-service-job-intake.md` + `affidavit-of-process-server-pdf.md`
- Plans: `/home/workspace/Plans/ServeTracker_Phase2_Plan.md`
