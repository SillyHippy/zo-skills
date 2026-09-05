---
name: affidavit-url-generator
description: "Generate pre-filled affidavit URL for justlegalsolutions.org/affidavit from plain text field values or extracted court document data."
version: 1.1.0
---

# Affidavit URL Generator

When the user sends field values (one per line, key: value format) OR when the user sends court documents (PDFs), generate a pre-filled URL for their website's affidavit form.

## Workflow

**From court documents:** Extract key fields from PDFs using PyMuPDF → map to allowed keys → generate URL.

**From plain text:** Parse key: value pairs → validate against allowed keys → generate URL.

**Return ONLY the URL** — no explanations, no markdown, no extra text.

## Allowed Field Names (exact, case-sensitive)
- Name of Court
- Plaintiff/Petitioner
- Defendant/Respondent
- Case Number
- Recipient Name
- Address
- Documents
- Personal Service
- Substituted at Residence
- Substituted at Business
- Posting
- Non-Service
- Unknown at address
- Moved left no forwarding
- Service canceled by litigant
- Unable to serve in a timely fashion
- Address does not exist
- Other
- Service attempt 1 Date through Service attempt 6 Date
- Service attempt 1 time through Service attempt 6 time
- Comments

## Rules
1. IGNORE any key not in the allowed list
2. Checkbox fields (Personal Service, Substituted at Residence, etc.): include with `=on` if selected, omit entirely if not
3. Encoding: Key spaces→+, /→%2F; Value space→+, comma→%2C, apostrophe→%27, semicolon→%3B, colon→%3A, slash→%2F, ampersand→%26, question mark→%3F
4. Return ONLY the URL, no explanations

## Implementation
Run: `python3 /root/just-legal-solutions/scripts/affidavit_url.py` with the field text as input.
