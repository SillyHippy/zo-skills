#!/usr/bin/env python3
"""Cancel a draft invoice in Helcim by ID or invoice number."""

import argparse
import json
import sys
import urllib.request
import urllib.error
import urllib.parse

SECRETS_FILE = "/root/.zo_secrets"
API_BASE = "https://api.helcim.com/v2"
USER_AGENT = "ZoComputer/1.0"


def get_api_token():
    """Read HELCIM_API_KEY raw from .zo_secrets."""
    with open(SECRETS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("export HELCIM_API_KEY="):
                val = line.split("=", 1)[1]
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                val = val.replace("\\", "")
                return val
    print("ERROR: HELCIM_API_KEY not found in " + SECRETS_FILE, file=sys.stderr)
    sys.exit(1)


def api_request(method, path, data=None, token=None):
    """Make a request to the Helcim API."""
    url = API_BASE + path
    body = json.dumps(data).encode("utf-8") if data else None
    headers = {
        "api-token": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def find_invoice_by_number(token, invoice_number):
    """Search invoices by invoiceNumber, return matching invoice or None."""
    result = api_request("GET", f"/invoices/?invoiceNumber={urllib.parse.quote(invoice_number)}", token=token)
    invoices = result if isinstance(result, list) else []
    for inv in invoices:
        if inv.get("invoiceNumber") == invoice_number:
            return inv
    return None


def cancel_invoice(token, invoice_id):
    """Cancel an invoice by setting status to CANCELLED."""
    payload = {"status": "CANCELLED"}
    return api_request("PATCH", f"/invoices/{invoice_id}", data=payload, token=token)


def main():
    parser = argparse.ArgumentParser(description="Cancel a draft invoice in Helcim")
    parser.add_argument("--invoice-id", type=int, help="Invoice ID to cancel")
    parser.add_argument("--invoice-number", help="Invoice number to cancel (e.g. 2025CA005502)")
    args = parser.parse_args()

    if not args.invoice_id and not args.invoice_number:
        print("ERROR: Must provide --invoice-id or --invoice-number", file=sys.stderr)
        sys.exit(1)

    token = get_api_token()
    invoice_id = args.invoice_id

    if not invoice_id:
        invoice = find_invoice_by_number(token, args.invoice_number)
        if not invoice:
            print(f"ERROR: Invoice {args.invoice_number} not found", file=sys.stderr)
            sys.exit(1)
        invoice_id = invoice["id"]

    result = cancel_invoice(token, invoice_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
