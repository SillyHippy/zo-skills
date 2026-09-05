---
name: field-sheet-generator
description: Generate legal Field Sheet PDFs from client emails and petition/summons PDFs using a local script. Use when the user says "field sheet", "make field sheet", "generate field sheet", or uploads case documents and asks for a field sheet. Also for manual service requests. This skill runs entirely locally via regex and optional OCR — no AI vision API calls required.
metadata:
  author: sillyhippy.zo.computer
  compatibility: "Created for Zo Computer"
---
# Field Sheet Generator

Generates a printable Field Sheet PDF for Just Legal Solutions process serving jobs and uploads it + case documents to Google Drive.

## PRIMARY PATH — ServeTracker native engine (MANDATORY when case exists in ServeTracker)

**Never use WeasyPrint or the old HTML template when the case is already in ServeTracker.**

```bash
cd /home/workspace/Projects/PDFUSAEDIT-zo
bun scripts/generate_field_sheet_cli.ts \
  --case-number "FD-2026-1091" \
  --out "/home/workspace/justlegalsolutions/cases/FD-2026-1091/FD-2026-1091_Field_Sheet.pdf"
```

Or by case id:
```bash
bun scripts/generate_field_sheet_cli.ts --case-id "CASE_UUID" --out "/path/to/Field_Sheet.pdf"
```

This uses `fieldSheetPdfEngine.ts` (pdf-lib) — the same engine as the ServeTracker UI. Output includes:
- TARGET RECIPIENT TO SERVE banner
- Residential / work address boxes
- Docs to Serve from `documents_to_serve`
- Requirements from case notes
- 4 attempt log rows + physical description block

**Verify:** `pdftotext` must show `TARGET RECIPIENT TO SERVE` and the correct case number.

**Do NOT** attach field sheet PDFs to ServeTracker `client_documents` — ServeTracker renders them dynamically.

---

## FALLBACK PATH — petition/email extraction (only when case is NOT in ServeTracker yet)

### STEP 1: Extract case info from the petition PDF

Run `pdftotext` to read the PDF text:
```bash
pdftotext "/path/to/petition.pdf" - | head -30
```
Look for: case number (e.g. FD-2017-609), court (e.g. District Court in and for Tulsa County), plaintiff (e.g. Paul Kinman), defendant (e.g. Ellen Kinman).

### STEP 2: Save the email body to a temp file

```bash
cat > /tmp/field_job_email.txt << 'ENDOFFILE'
[paste the full email here]
ENDOFFILE
```

### STEP 3: Run the field sheet generator

```bash
python3 /home/workspace/Skills/field-sheet-generator/scripts/generate_field_sheet.py \
  --email-file /tmp/field_job_email.txt \
  --petition-pdf "/path/to/petition.pdf" \
  --out-dir /home/workspace/justlegalsolutions/cases \
  --case-number "FD-2017-609" \
  --court "District Court in and for Tulsa County, State of Oklahoma" \
  --plaintiff "Paul Kinman" \
  --defendant "Ellen Kinman"
```

**CRITICAL: After the script runs, ALWAYS read the output HTML** and fix address merging before converting to PDF:
```bash
cat /home/workspace/justlegalsolutions/cases/{casenumber}.html
```

### STEP 4: Fix addresses in the HTML (if needed)

If the email has BOTH a home and work address, the script WILL merge them into Address 1. You MUST fix this:

Use `edit_file_llm` on the HTML file with instructions:
```
Separate the addresses: put just the residential address in Address 1 and just the work/business address in Address 2. Remove any merged combo.
```

### STEP 5: Regenerate the PDF

If the HTML was edited, regenerate:
```bash
cd /home/workspace/justlegalsolutions/cases && python3 -c "
# Use weasyprint or markdown to convert
from weasyprint import HTML
HTML('{casenumber}.html').write_pdf('{casenumber}.pdf')
"
```
If weasyprint not available, try:
```bash
pip install weasyprint && python3 -c "from weasyprint import HTML; HTML('/home/workspace/justlegalsolutions/cases/{casenumber}.html').write_pdf('/home/workspace/justlegalsolutions/cases/{casenumber}.pdf')"
```

### STEP 6: Find or create ONE folder in Site Upload

Site Upload parent ID is always: `1ZB7XTSC_eD6m3F-6_yI2VP065cKEQzVq`

**6a. LIST first** — search under Site Upload for an existing folder named with the case number. If found, USE that folder ID. Do NOT create another.

**6b. Create only if missing:**
```json
// Tool: use_app_google_drive(tool_name="google_drive-create-folder", configured_props=...)
// Parameter name: "parentId" (NOT "parents", NOT "folderId")
{
  "name": "FD-2017-609",
  "parentId": "1ZB7XTSC_eD6m3F-6_yI2VP065cKEQzVq"
}
```

**After create, copy the new folder ID from the response** and use it for every upload.

### STEP 7: Upload all files to that folder

For each file, use EXACTLY this pattern:
```json
// Tool: use_app_google_drive(tool_name="google_drive-upload-file", configured_props=...)
// Parameter name: "parentId" (NOT "parents", NOT "folderId")
{
  "name": "FD-2017-609_Field_Sheet.pdf",
  "parentId": "THE_FOLDER_ID_FROM_STEP_6",
  "filePath": "/home/workspace/justlegalsolutions/cases/FD-2017-609.pdf"
}
```

Files to upload (in this order):
1. Field sheet PDF from `/home/workspace/justlegalsolutions/cases/{case_number}.pdf`
2. Motion/Summons PDFs from chat uploads
3. Any photos or exhibits from chat uploads

### Template Rendering & Verification Rule (MANDATORY)
1. **Always test rendered text before PDF generation**: The script populates Jinja2 (`{{ data.x }}`), PHP (`<?= data.x ?>`), and single brace (`{x}`) placeholders. Verify `pdftotext` on the output PDF contains zero `{placeholder}` or `{{ data.x }}` text strings.
2. **Ghostscript PDF 1.4 Normalization**: Always run `gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dNOPAUSE -dQUIET -dBATCH -sOutputFile=fixed.pdf input.pdf` followed by `qpdf --check` to ensure Android/Windows viewer compatibility.
3. **Verify Google Drive replacement**: When replacing a broken field sheet in Drive, trash the old file ID (`google_api.py drive delete FILE_ID`) and re-verify the parent folder search.

## HARD RULES — NEVER BREAK THESE

### NEVER FAIL THESE AGAIN (RID1702318 lessons — MANDATORY)
1. **ServeTracker cases:** use `generate_field_sheet_cli.ts` (native engine). **Non-ServeTracker:** use the fallback script below. Never hand-build a field sheet HTML/PDF.
2. **User-provided address ALWAYS wins.** If Joe types or texts an address, pass it with `--address` exactly. Do NOT put court header addresses (e.g. Blythe CA courthouse) in Address 1. OCR/header city is not the service address.
3. **Double-check Address 1** after generation: open the HTML and confirm it is a real residential/service address that matches the user or the body service address — not the form caption, not the court street.
4. **Special Instructions = state service rule ONLY.** One short line. Format example: `Sub service YES 1st attempt age 15+ (OK 12 O.S. 2004 via CA CCP 413.10(b)).` NEVER write a research paragraph, diligence essay, or multi-sentence legal memo in that field.
5. **ONE Site Upload folder per case.** Search/list existing folder by case number under Site Upload (`1ZB7XTSC_eD6m3F-6_yI2VP065cKEQzVq`) first. If it exists, USE that folder ID. NEVER create a second folder for the same case.
6. **Before upload:** delete prior field-sheet PDFs in that folder (name contains Field_Sheet / Field Sheet). Leave the user's packet PDFs alone unless told to delete them.
7. **Pass full overrides** when known: `--case-number --court --plaintiff --defendant --recipient --address --documents --instructions --client`.
8. **Verify loop before claiming done:** read HTML → check Address 1 + Special Instructions + Party + Case Number → only then PDF + upload + Telegram attach the actual PDF.



### Address Rule (MANDATORY)
When the input has BOTH a home/residential address and a work/business address:
- **Address 1** = residential address ONLY
- **Address 2** = work/business address ONLY
- NEVER merge them into one field.
- If the script combines them, edit the HTML to separate them BEFORE generating the PDF.

### Google Drive Tool Parameters (MANDATORY)
- `google_drive-create-folder`: use `parentId` parameter (NOT `parents`, NOT `folderId`)
- `google_drive-upload-file`: use `parentId` parameter (NOT `parents`)
- The parent folder ID for Site Upload is always: `1ZB7XTSC_eD6m3F-6_yI2VP065cKEQzVq`
- After creating a folder, copy its ID from the tool response and use it for all subsequent uploads.
- Never search for the folder by name — use the ID you saved.

### Party to Serve Rule (MANDATORY)
The "Party to Serve" / "Recipient" is ALWAYS the defendant/respondent being served. Do not leave this blank. If the email names a respondent, that's the party to serve.

## Manual Overrides (CLI flags for script)

| Flag | Purpose |
|------|---------|
| `--case-number` | Override extracted case number |
| `--court` | Override court name |
| `--plaintiff` | Override plaintiff name |
| `--defendant` | Override defendant name |
| `--recipient` | Override party to serve |
| `--address` | Override service address |
| `--client` | Override client reference |
| `--documents` | Override documents text |
| `--instructions` | Override special instructions |
| `--job-id` | Override job ID |

## Template Location
```
/home/workspace/Skills/field-sheet-generator/assets/template.html
```

## Dependencies
```bash
pip install jinja2 pymupdf pdf2image pytesseract weasyprint
apt-get install -y tesseract-ocr poppler-utils
```
