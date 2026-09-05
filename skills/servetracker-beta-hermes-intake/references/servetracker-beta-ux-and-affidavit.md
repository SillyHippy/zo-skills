# ServeTracker Beta — UX + affidavit preferences (2026-08-11)

Session-hardened rules for the beta app (`PDFUSAEDIT-zo-beta`, `:3151`).  
Court wet-ink affidavits still use **`process-serving-toolkit` + `fill_affidavit.py` + ORIGINAL template** — not the in-app HTML generator.

## New Serve / attempt logging

1. **Active cases only** in the case search list (`Open` / `active`; hide `closed`, case-insensitive). Closed clutter was a hard reject.
2. **PBS dropdown** defaults to **that case’s** `defendant_respondent` / case Person Being Served. Never first recipient from another case or leftover test rows.
3. **Saved addresses** — tappable Home + Secondary (API `work_address`) fill buttons; do not force typing.
4. **Skip intermediate Camera Capture page** — Field Capture goes straight to Log Attempt; lock GPS when that page opens.
5. **Photos** — gallery `multiple` up to 5; Take Photo + Choose Photos on the same page; canvas compress + strip device EXIF; restamp as ServeTracker Photo N with **per-photo** time + GPS at upload.
6. **Edit attempt** — restore Edit on dashboard/history; may add photos; **never overwrite original GPS** on edit.
7. **One save only** — prevent double POST (ServeAttempt + NewServe both creating) → double email.
8. **Attempt emails** — photo **links** labeled `ServeTracker Photo N · <date/time CT> · <lat, lon>`; **no** file attachments by default; **no** EXIF-strip blurb; **no** PSL/PSS in the email body (contractors later).

## Case intake field names (UI)

| UI label | DB / API |
|---|---|
| Person Being Served | `case_name` + `defendant_respondent` |
| Court Name (full caption) | `court_name` |
| Documents to Serve | `documents_to_serve` (feeds affidavit Documents line) |
| Secondary Address | `work_address` |

## Affidavit — Joseph preference

**Yes/no fact (2026-08-11):** In-app ServeTracker “Print affidavit” used an HTML generator — **NOT** `Affidavit_Joseph_Iannazzi_Template_ORIGINAL.pdf`. User prefers the **ORIGINAL fillable template** for court use.

When generating a court affidavit (Hermes / toolkit):
- Use `scripts/fill_affidavit.py` on **ORIGINAL** only.
- Layout intent: process server **LEFT** (signature + Joseph + **PSL-2026-2**); notary **RIGHT** (swear line blank for **Kimberly Deason** stamp).
- Joseph **cannot** notarize his own affidavit. Kimberly Deason notarizes; commission **#26001890** exp **02/24/2030** — typed commission optional/omit when stamp is readable.
- Physical visits only in attempt rows; phone/neighbor/management → Comments.
- Documents line = exact titles from packet / Drive cover sheet / case `documents_to_serve` — never empty when docs exist.
- “Subscribed and sworn…” / Date / Date_2 → day of print/signing (wet-ink workflow per toolkit).

## Wave A/B shipped preferences (keep)

9. **Attempt numbers** — server-owned per recipient/job; **renumber on delete** to 1…N by occurred_at. Client cannot force the number.
10. **Log another attempt** — History/Dashboard deep-link to New Serve with same client/case/PBS/address; skip re-search.
11. **Sticky last active case** — reopen New Serve with last selected active case; never sticky a closed case.
12. **Auto-close on successful serve** — close **that case row by UUID** (`case_id`), not by shared case number alone.
13. **Same case #, multiple people/addresses** is intentional — **no** duplicate-case-number guard.
14. **Tap targets** ≥44px on primary mobile controls.

## Deferred (do not implement unless Joseph asks)

- ORIGINAL fillable Court PDF wired into the beta app Print button (~7/10 AI difficulty) — keep Hermes/`fill_affidavit.py` for wet-ink.
- History search (low priority).
- Drive-on-success (flag OFF).
- Contractor / multi-server RBAC.

## Operating style for this app

If beta already works for Joseph on Galaxy S26 Ultra Chrome, leave optional hard items alone. Honest confidence levels; no “100% / good to go” without live verify + re-verify. Backup zip before risky waves. Touch/finger verification > mouse scroll claims.

## Pitfalls

- Status values in DB are mixed case (`closed` / `Open` / `active`) — always compare case-insensitive.
- Partial PUT with `body.x || ""` wipes omitted fields — merge with existing.
- Clearing notes with `""` must use `!== undefined`, not `|| existing`.
- `DRIVE_UPLOAD_ON_SUCCESS` stays **OFF** until hash-verify proven.
- General Documents UI white screen: case filter must use defined state (fixed 2026-08-11); that tab is client misc files, not case pleadings.
