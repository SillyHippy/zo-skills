#!/usr/bin/env python3
"""Check for EXISTING Helcim invoices before creating a new one (idempotency gate).

Usage:
  python3 check_invoice.py --email client@example.com [--case SC26-0087JP2]

Prints every invoice whose billingAddress.email matches (case-insensitive),
optionally narrowed to invoices whose line descriptions or notes mention --case.

Exit codes:
  0 = matching invoice(s) found (REUSE, do not create)
  1 = no matches (safe to create)
  2 = API/credential error
"""
import json
import re
import sys
import urllib.request

SECRETS_FILE = "/root/.zo_secrets"
API_BASE = "https://api.helcim.com/v2"


def get_api_token():
    with open(SECRETS_FILE, "r") as f:
        text = f.read()
    for key in ("HELCIM_API_TOKEN", "HELCIM_API_KEY"):
        m = re.search(rf'(?:export\s+)?{key}=["\']([^"\']+)["\']', text)
        if m:
            return m.group(1).replace("\\", "")
        m = re.search(rf'(?:export\s+)?{key}=(\S+)', text)
        if m:
            return m.group(1).replace("\\", "")
    print("ERROR: HELCIM_API_TOKEN/KEY not found in " + SECRETS_FILE, file=sys.stderr)
    sys.exit(2)


def api_request(method, path, token, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(
        API_BASE + path,
        data=body,
        headers={
            "api-token": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "hermes-helcim-check",
        },
        method=method,
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def build_pay_url(invoice):
    token = invoice.get("token")
    if not token:
        return None
    return "https://just-legal-solutions.myhelcim.com/order/?token=" + str(token)


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True, help="Client email to match")
    p.add_argument("--case", default=None, help="Case number substring to require (searched in notes + line descriptions)")
    args = p.parse_args()

    try:
        tok = get_api_token()
        invoices = api_request("GET", "/invoices", tok)
    except Exception as e:
        print(f"ERROR: API call failed: {e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(invoices, list):
        print(f"ERROR: unexpected API response: {invoices}", file=sys.stderr)
        sys.exit(2)

    needle = args.email.lower()
    matches = []
    for inv in invoices:
        ba = inv.get("billingAddress") or {}
        email = (ba.get("email") or "").lower()
        if email != needle:
            continue
        if args.case:
            hay = " ".join(
                [
                    str(inv.get("notes") or ""),
                    " ".join(str(l.get("description") or "") for l in (inv.get("lineItems") or [])),
                ]
            ).lower()
            if args.case.lower() not in hay:
                continue
        matches.append(inv)

    for inv in sorted(matches, key=lambda x: str(x.get("invoiceNumber") or "")):
        ba = inv.get("billingAddress") or {}
        print(
            f"{inv.get('invoiceId')} | {inv.get('invoiceNumber')} | {inv.get('status')} | "
            f"{inv.get('amount')} | {ba.get('email')} | {build_pay_url(inv)}"
        )
        notes = inv.get("notes") or ""
        if notes:
            print(f"    notes: {notes[:120]}")

    if matches:
        print(f"\nFOUND {len(matches)} existing invoice(s) for {args.email}"
              + (f" with case {args.case}" if args.case else "")
              + ". REUSE a DUE one — do NOT create a new invoice.")
        sys.exit(0)
    else:
        print(f"No existing invoices for {args.email}"
              + (f" with case {args.case}" if args.case else "")
              + ". Safe to create.")
        sys.exit(1)


if __name__ == "__main__":
    main()
