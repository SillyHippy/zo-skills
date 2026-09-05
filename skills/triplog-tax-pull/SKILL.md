---
name: triplog-tax-pull
description: Pulls profit & loss data from TripLog native API, calculates mileage deduction at IRS rate, and estimates self-employment tax liability for Just Legal Solutions (VXM LLC DBA).
compatibility: Created for Zo Computer. Requires TripLog API key and requests library.
metadata:
  author: sillyhippy.zo.computer
  last_updated: 2026-05-09
---

## TripLog Tax Pull Skill

Pulls all income, expenses, trips, and mileage from TripLog's native REST API (not the broken viasocket MCP). Calculates:

- Gross income by merchant (ABC Legal, Helcim, etc.)
- Business expenses by category (LegalProf, Hardware, Software, etc.)
- Mileage deduction at current IRS rate (72.5¢/mile for 2026)
- Self-employment tax estimate

### Usage

Run directly:

```bash
cd /home/workspace/Skills/triplog-tax-pull && python3 scripts/pull.py
```

### Output

Prints a formatted P&L summary to stdout and saves raw data to `/home/workspace/triplog_tax_data_2026.json`.

### API Key

Stored in the script header: `API_KEY = "7b6d5f4152aa4483bce69861556aa45a"`
Account: `iannazzi.joseph@gmail.com`

If the key changes, update it at the top of `scripts/pull.py`.

### Notes

- TripLog native API endpoint: `https://app.triplog.net/web/api`
- Auth header: `apikey <key>`
- The viasocket MCP server is unreliable — always use the native API directly
- Date range defaults to Nov 2025–Dec 2026; adjust `startDate`/`endDate` in the script if needed
