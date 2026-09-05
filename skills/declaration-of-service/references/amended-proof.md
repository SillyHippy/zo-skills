# Amended Proof of Service

Perjury declaration — **no notary block**. Valid for Oklahoma court filing.

## When to use

User says "amended proof of service", "amended declaration", or needs to correct a prior filing where the **person served** was wrong.

## Three roles — never conflate

| Role | Example (FD-2023-1652) |
|---|---|
| **Client** (hired you) | Nicholas E. Scott |
| **Person actually served** | Melinda R. Scott (plaintiff) |
| **Wrong name on prior filing** | Nicholas E. Scott (client listed as recipient) |

Defendant ≠ person served. Client who paid ≠ person served.

## Header

```latex
{\large \textbf{AMENDED PROOF OF SERVICE}}
```

Right column of case block:

```latex
AMENDED PROOF OF SERVICE OF \\
\textbf{[documents]}
```

## Correction paragraph (after case block)

```latex
This amended proof of service corrects the recipient name on the Proof of Service dated MM/DD/YYYY, which incorrectly identified [WRONG NAME] as the person served. The person actually served was [CORRECT NAME]. All other facts of service remain unchanged.
```

## Service narrative

- **Received by** → person **actually served** (not defendant by default)
- **Substitute**: name, relationship, physical description
- **Hearing date**: omit unless user provides one
- **Sign date** = amendment date; **service date/time** = original attempt

## Output

`/home/workspace/Documents/proof-{CASE}/proof_of_service_amended.pdf` → return as MEDIA.

## Do NOT

- Use "Declaration of Service" in the document title
- Use Willow Ave template (landlord/pre-litigation only)
- Add notary block unless user explicitly asks for affidavit
- Push amended affidavit when user wants proof/declaration filing
