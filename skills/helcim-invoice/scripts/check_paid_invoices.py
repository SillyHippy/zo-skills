#!/usr/bin/env python3
"""Poll Helcim for newly PAID invoices and output them for SMS notification.

Keeps a state file of already-notified invoice IDs so each payment only
triggers one notification. Outputs JSON array of new paid invoices (empty
array if nothing new). Designed to be run by a Zo automation on a schedule.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

API_BASE = "https://api.helcim.com/v2"
SECRETS_FILE = "/root/.zo_secrets"
STATE_FILE = "/home/workspace/Skills/helcim-invoice/scripts/.paid_invoices_state.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
LOOKBACK_DAYS = 3


def get_api_key():
    with open(SECRETS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("export HELCIM_API_KEY="):
                val = line.split("=", 1)[1]
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                val = val.replace("\\", "")
                return val
    print("ERROR: HELCIM_API_KEY not found", file=sys.stderr)
    sys.exit(1)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_state(ids):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(ids), f)


def fetch_paid_invoices(key):
    ds = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    url = f"{API_BASE}/invoices?status=PAID&dateStart={ds}"
    req = urllib.request.Request(url, headers={
        "api-token": key,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"ERROR {e.code}: {e.read().decode(errors='replace')[:500]}", file=sys.stderr)
        sys.exit(1)


def main():
    key = get_api_key()
    invoices = fetch_paid_invoices(key)
    if not isinstance(invoices, list):
        invoices = []

    state = load_state()
    new_paid = []
    for inv in invoices:
        inv_id = inv.get("invoiceId")
        if inv_id is not None and inv_id not in state:
            new_paid.append({
                "invoiceNumber": inv.get("invoiceNumber", "?"),
                "amount": inv.get("amount", 0),
                "amountPaid": inv.get("amountPaid", 0),
                "customerName": inv.get("billingAddress", {}).get("name", "Unknown"),
                "description": inv.get("lineItems", [{}])[0].get("description", "") if inv.get("lineItems") else "",
                "datePaid": inv.get("datePaid", ""),
                "invoiceId": inv_id,
            })
            state.add(inv_id)

    save_state(state)
    print(json.dumps(new_paid, indent=2))


if __name__ == "__main__":
    main()