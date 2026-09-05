---
name: declaration-of-service
description: >
  Generate Declaration of Service PDFs for Oklahoma process serving. Document title
  is always DECLARATION OF SERVICE (or AMENDED DECLARATION OF SERVICE). No notary block.
  Triggers on "proof of service", "declaration of service", "make proof",
  "amended proof of service", "amended declaration". NOT the Willow Ave
  landlord template. NOT an Affidavit of Process Server unless user asks.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---

# Declaration of Service — LaTeX Skill

Generate **Declaration of Service** PDFs for Oklahoma court cases. Perjury declaration — **no notary block, no jurat, no seal area**.

**Document title is `DECLARATION OF SERVICE`** — this matches Joseph's ACTUAL accepted court filings (see `Declaration_CJ-2026-02866.pdf`, `declaration-FD-2023-1652/declaration_of_service.tex`). Do NOT use "PROOF OF SERVICE" in the header — that was an earlier skill error corrected 2026-08-03 after the user rejected a mis-titled document at a glance. (eFile dropdown label may say Proof of Service, but the document header is DECLARATION OF SERVICE.)

## Rules (STRICT)

1. **Header = DECLARATION OF SERVICE** (or AMENDED DECLARATION OF SERVICE). The eFile dropdown may call this "Proof of Service," but the document header must use the accepted declaration title.
2. **No notary block.** No jurat. No "Subscribed and sworn before me..."
3. **Do NOT use Willow Ave template** for court cases. Willow Ave is landlord/pre-litigation only (`declaration-1340-willow/`).
4. **Three roles — never conflate:** (1) client who hired/paid, (2) person actually served, (3) name on prior filing. Accept corrections immediately.
5. **Yes/no questions → "Yes" or "No" only.**
6. **"Make proof" / "declaration of service" → generate the PDF.** Do not pivot to affidavit or filing steps unless asked.
7. **Person served ≠ defendant by default.** Use who was actually served in the narrative.

## Canonical template (court cases)

Copy from:

```
/home/workspace/Skills/declaration-of-service/assets/proof_of_service_template.tex
```

Working examples:
- `/home/workspace/Documents/declaration-FD-2023-1652/` (regenerate with PROOF header)
- `/home/workspace/Documents/Declaration_CJ-2026-02866.pdf` (layout reference)

Layout:
- `lualatex` + `bidi=basic` + Noto Sans
- Centered **PROOF OF SERVICE** + court line
- Two-column `tabular` case block
- Signature row: Name | PSL-2026-2 / Server ID # | Date
- "Executed in Tulsa County, State of Oklahoma."

## 🩸 GUARDIANSHIP / "IN THE MATTER OF" CASES (2026-08-03 INCIDENT — READ FIRST)

**NEVER copy the field sheet's PLAINTIFF/DEFENDANT labels into a declaration.** The field sheet is intake data, not the court caption — its plaintiff/defendant fields are frequently wrong/backwards for guardianships. On 2026-08-03 the roles were reversed in a printed declaration (perjury risk) and the header used the wrong title; the user rejected both at a glance.

**Guardianship roles (Oklahoma):**
- Case style: `IN THE MATTER OF THE GUARDIANSHIP OF <NAME>, AN INCAPACITATED PERSON` — no "vs." structure.
- **Petitioner** = person who filed (family member / client who hired you). **Respondent** = alleged incapacitated person = the one served.
- Person served is almost always the RESPONDENT (incapacitated person).

**Mandatory verification before delivering ANY declaration:**
1. Read/OCR the court PDF page 1 → confirm exact case style and the "TO:" name (that's the respondent).
2. Field sheet CLIENT REFERENCE = usually the petitioner.
3. Header must read **DECLARATION OF SERVICE** (never "PROOF OF SERVICE").
4. Body uses the accepted phrasing: "On the {M/D/YYYY} at {H:MM AM/PM}, I, Joseph William Iannazzi, SERVED {person}."
5. Documents line = exact wording from the field sheet DOCUMENTS section (verbatim, no paraphrase, listing all 4+ attached documents such as Summons, Petition, Motion for SPS, Order Appointing SPS).
6. Narrative names the person actually served explicitly, in the caption AND the body.
7. Compare rendered output against `Declaration_CJ-2026-02866.pdf` layout before delivering.

## Willow Ave — different document

`/home/workspace/Documents/declaration-1340-willow/` is for **pre-litigation landlord notices** only. Do not use for FD/CJ/civil court proofs.

## Generate with script

```bash
cd /home/workspace/Skills/declaration-of-service
python scripts/fill_proof.py \
  --plaintiff "Melinda R. Scott" \
  --defendant "Nicholas E. Scott" \
  --person-served "Melinda R. Scott" \
  --address "16129 S 79th E Pl, Bixby, OK 74008" \
  --case-number "FD-2023-1652" \
  --documents "Motion to Modify Child Support and Notice of Hearing" \
  --service-type substituted-residence \
  --service-date "06/23/2026" --service-time "6:51 PM" \
  --today "07/07/2026" \
  --comments "Substituted service at residence. Served Brody Scott, co-resident." \
  --narrative "I made successful substitute service at the abode of the plaintiff..." \
  --output /home/workspace/Documents/proof-FD-2023-1652/proof_of_service.pdf
```

Amended: add `--amended --original-date "06/23/2026" --wrong-name "Nicholas E. Scott"`

Compile: `lualatex -interaction=nonstopmode`

## Amended proof

See `references/amended-proof.md`. Title: **AMENDED PROOF OF SERVICE**. Include correction paragraph naming wrong vs correct person served.

## Proof vs Affidavit

| Document | Title | Notary | When |
|---|---|---|---|
| **Proof of Service** | PROOF OF SERVICE | No | User asks for proof/declaration — court filing OK in OK |
| **Affidavit of Process Server** | AFFIDAVIT OF PROCESS SERVER | Yes | User explicitly asks for sworn affidavit |

eFile label for amended docs: **Amended Proof of Service**.

## Output

- Write to `/home/workspace/Documents/proof-{CASE}/`
- Return PDF as MEDIA
- Report exact LaTeX error if compile fails
