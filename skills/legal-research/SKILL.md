---
name: legal-research
description: Research case law, statutes, court rules, and legal procedures for Oklahoma and federal courts. Use when the user asks about legal procedures, court rules, filing requirements, jurisdiction, statute of citations, or needs to look up Oklahoma statutes, federal rules, or case law relevant to process serving.
metadata:
  author: sillyhippy.zo.computer
  compatibility: "Created for Zo Computer"
---

# Legal Research

Research legal information relevant to process serving work, primarily focused on Oklahoma state courts and federal courts.

## When To Use

- User asks about service of process rules
- User needs Oklahoma statute citations
- User asks about court filing procedures
- User needs to verify jurisdictional requirements
- User asks about due diligence requirements
- User needs information on eviction procedures, family law service, civil procedure

## Research Sources

### Primary Sources (free)
- **Oklahoma Statutes**: https://www.oscn.net/
- **Oklahoma Court Rules**: https://www.oscn.net/title/12/ (Civil Procedure)
- **Oklahoma Supreme Court Network (OSCN)**: https://www.oscn.net/
- **Justia**: https://law.justia.com/
- **Cornell LII**: https://www.law.cornell.edu/
- **Google Scholar Case Law**: https://scholar.google.com/ (case law search)

### Process-Specific Research

#### Oklahoma Service of Process
- Title 12 Oklahoma Statutes — Civil Procedure
- Title 4 — Corporations (business entity service)
- Title 43 — Marriage and Family (divorce service)
- Title 63 — Public Health (health-related service)

#### Federal Service
- FRCP Rule 4 — Summons and Service
- FRCP Rule 5 — Serving and Filing Pleadings

## How to Research

### Using Web Search
```
web_search: "Oklahoma service of process rules [topic]"
web_search: "FRCP Rule 4 service of process"
web_search: "Oklahoma [statute title] [section]"
```

### Using Web Research (higher quality)
```
web_research: "Oklahoma due diligence requirements process serving" — category: "research paper"
web_research: "FRCP Rule 4 amended service requirements" — category: "research paper"
```

### Reading Legal Pages
When a relevant page is found, use `read_webpage(url)` to get the full text, then summarize the key rules and citations.

## Output Format

Always provide:
1. **Specific citation** (statute number, rule number, case name + citation)
2. **Plain-English summary** of what the rule requires
3. **Practical implication** for process serving
4. **Source URL** for verification

Example:
```
**12 O.S. § 2004 — Service of Summons**

Requires personal service on the defendant or service at their usual residence
to someone over 14 years of age. For corporations, serve the registered agent
or any officer/director.

Implication: If defendant can't be found personally, attempt service at residence
to a qualifying household member before pursuing alternative methods.

Source: https://www.oscn.net/statutes/Title12/Title12-2004/
```

## Never Hallucinate

- Only cite statutes/rules that you actually find and verify
- If you can't find a specific citation, say so
- Do not invent case names, statute numbers, or rule citations
- When in doubt, recommend the user consult with an attorney

## Common Research Topics

| Topic | Where to Look |
|-------|---------------|
| Personal service requirements | 12 O.S. § 2004 |
| Subpoena service | 12 O.S. § 2004, FRCP 45 |
| Eviction / Forcible Entry | 41 O.S. § 101 et seq. |
| Divorce / Family law service | 43 O.S. § 101 et seq. |
| Business entity service | 18 O.S. (corporations), 47 O.S. (LLCs) |
| Due diligence standards | Case law on OSCN/Justia |
| Proof of service / Affidavit requirements | Local court rules |
| Federal court service | FRCP Rule 4 |
