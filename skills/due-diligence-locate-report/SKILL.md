---
name: due-diligence-locate-report
description: Automate OK skip-trace collection (OSCN via Tailscale S26 SOCKS :1055) and draft Due-Diligence Locate Report DOCX. Use when Joseph needs reports like the Jessica Rachal Jones memo — addresses, phones, relatives, court history.
compatibility: Zo Computer — requires Galaxy S26 exit node on 127.0.0.1:1055
---

# Due-Diligence Locate Report

## Proxy (mandatory for OSCN)

```bash
export SKIP_TRACE_SOCKS=socks5h://127.0.0.1:1055
```

- **S26 Ultra** (`tailscale-proxy1-galaxy`, exit `100.101.208.121`) — verified Aug 2026
- **Do not use** Note9 `:1058` until `rx` traffic returns on Tailscale status
- **Do not use** `:1057` microsocks (same VPS IP as datacenter)

## Collect (automated)

```bash
python3 /home/workspace/Scripts/skip-trace-locate/collect_locate_intel.py \
  --first FIRST --last LAST --middle MIDDLE \
  --counties tulsa,creek,nowata \
  --city Tulsa --state OK \
  --case-no "CASE" --style "Style text" \
  --out /home/workspace/skip-trace-out/SLUG
```

Outputs: `findings.json`, `people_search_urls.json`, `FINDINGS.md`

## People-search (manual — required for addresses/phones/relatives)

Automation hits **DataDome** on TPS/FPS/FTN even through home IP + Scrapling.

1. Open URLs from `people_search_urls.json` on the **phone** (or desktop on home Wi‑Fi)
2. Copy addresses, phones, relatives (+ relative phones) into `findings.json` → `people_search_manual`
3. Or paste raw notes; Hermes can structure them into JSON

Joseph's FTN/FPS URL parser remains the fastest path for those sites.

## Draft DOCX

```bash
python3 /home/workspace/Scripts/skip-trace-locate/generate_due_diligence_docx.py \
  --findings /home/workspace/skip-trace-out/SLUG/findings.json \
  --out /home/workspace/skip-trace-out/SLUG/Due-Diligence-Locate-Report.docx \
  --locate-outcome failed
```

Hermes should merge OSCN narrative (traffic pattern like Jessica report) from case detail pages when user asks for full prose.

## Tools map (Joseph's stack)

| Need | Tool |
|------|------|
| Courts, DL/VIN on filings, traffic history | **OSCN** via collector + SOCKS :1055 |
| Addresses / phones / relatives | **FTN / FPS / TPS** manual + paste into findings |
| Property owner / mailing | County Spatialest (add to collector later) |
| Custody | VINELink / OK DOC |
| Browser on blocked sites | **Scrapling** MCP (Hermes) — backup only; often still captcha |
| General web fetch | **Exa / Parallel** (Hermes web tools) — not for people-search |
| Report file | **generate_due_diligence_docx.py** |

## Pay-per-report data (optional)

When a client pays for credit-header depth (TLO-class PDF): import into `people_search_manual` or attach as exhibit; do not subscribe monthly at ~8 traces/year.
