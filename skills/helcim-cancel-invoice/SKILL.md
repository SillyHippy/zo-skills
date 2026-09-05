---
name: helcim-cancel-invoice
description: |
  Cancel a draft invoice in Helcim payment processor by invoice ID or invoice number.
  Use when the user says "cancel invoice", "delete invoice", "void invoice", or needs to
  cancel a draft that was created by mistake. Only works on draft invoices.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---

# Helcim Cancel Invoice Skill

Cancels draft invoices in Helcim via API. Sets invoice status to CANCELLED.

## Usage

```bash
python3 /home/workspace/Skills/helcim-cancel-invoice/scripts/cancel_invoice.py \
  --invoice-number "2025CA005502"
```

Or by invoice ID:

```bash
python3 /home/workspace/Skills/helcim-cancel-invoice/scripts/cancel_invoice.py \
  --invoice-id 66571784
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--invoice-id` | No (one required) | Helcim invoice ID to cancel |
| `--invoice-number` | No (one required) | Invoice number to cancel (e.g. 2025CA005502) |

You must provide either `--invoice-id` or `--invoice-number`. If you provide invoice number, the script will look up the ID automatically.

## Output

Stdout prints JSON with the cancelled invoice details including:
- `invoiceId` — Helcim's internal ID
- `invoiceNumber` — The invoice number
- `status` — Should be "CANCELLED"
- `amount` — Invoice amount

## Auth

Uses `HELCIM_API_KEY` from `/root/.zo_secrets`. The script reads it directly to avoid bash escaping issues with special characters in the token.

## What This Does

- Sets invoice status to CANCELLED
- Invoice remains in Helcim history but is marked as cancelled
- Cannot be reversed — if you need to recreate it, use helcim-invoice skill

## Limitations

- Only works on draft invoices (status: DUE)
- Cannot cancel paid or partially paid invoices
- Does not delete the invoice from Helcim (just marks it cancelled)
