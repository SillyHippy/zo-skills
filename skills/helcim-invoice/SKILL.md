---
name: helcim-invoice
description: Create and manage Helcim invoices for Just Legal Solutions process serving business.
version: 1.3.0
---

# Helcim Invoice Skill

## CANONICAL COMMAND — use this only

```bash
python3 /home/workspace/Skills/helcim-invoice/scripts/create_invoice.py \
  --name "Client Name" \
  --email "client@example.com" \
  --phone "5555555555" \
  --line "Standard Process Service - CASE|110" \
  --line "OID Service of Process Fee|20" \
  --notes "case notes"
```

Or via generator wrapper (same enforcement):
```bash
cd /root/just-legal-solutions/invoices
python3 -c "
from generator import create_helcim_invoice
print(create_helcim_invoice(
    customer_name='Client',
    customer_email='client@example.com',
    line_items=[
        {'description':'Standard Process Service','price':110},
        {'description':'OID fee','price':20},
    ],
    notes='...',
))
"
```

## TWO BUGS THAT MADE JOE FIX THINGS MANUALLY — NEVER AGAIN

### 1. Email
- Helcim **ignores** top-level `email` on customer create.
- Email **only** sticks on `billingAddress.email` (+ shippingAddress.email).
- Customer link on invoice does **not** auto-copy billing — send `billingAddress` on every invoice create.
- Script **requires** `--email`, updates existing customers if email missing/wrong, verifies after create, aborts if email not on invoice.
- **Never** create an invoice without a real client email. Ask if missing.

### 2. Pay URL
```
https://just-legal-solutions.myhelcim.com/order/?token={token}
```
- Script always returns `pay_url` / `paymentLink` in that format.
- **FORBIDDEN:** `https://secure.myhelcim.com/invoice/...`
- When reporting to Joe, only print `pay_url` from the script JSON. Do not hand-build URLs.

## After create — return to Joe
From script JSON only:
- `invoiceNumber`, `amount`, `status`
- `sendToEmail` (must match what he gave)
- `pay_url` (must contain `just-legal-solutions.myhelcim.com/order/?token=`)

If any of those missing → fix before telling him done.

## List
```bash
cd /root/just-legal-solutions/invoices && python3 generator.py list DUE
```

## Other commands
```bash
python3 .../create_invoice.py get --invoice-id ID
python3 .../create_invoice.py update --invoice-id ID --email client@x.com --name "Name"
python3 .../create_invoice.py cancel --invoice-id ID
```

## Storm Law (OID jobs)
- vtripi@stormlawpartners.com
- rlink@stormlawpartners.com
- phone 832-323-3000

Related: process-serving-toolkit, joe-workflows.
