#!/usr/bin/env python3
"""Pure Python Helcim payment monitor with SQLite state tracking.

Polls Helcim API every 5 minutes. Stores invoices in a local SQLite DB.
Only sends SMS + Telegram notifications when an invoice's status
transitions to PAID — never for invoices that were already paid.

No AI involved in the monitoring loop. Uses a free Zo model via /zo/ask
ONLY for the SMS/Telegram send action when a new payment is detected.
"""

import json
import os
import sys
import time
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# --- Config ---
HELCIM_API_BASE = "https://api.helcim.com/v2"
SECRETS_FILE = "/root/.zo_secrets"
DB_FILE = "/home/workspace/Skills/helcim-invoice/scripts/helcim_monitor.db"
LOG_FILE = "/dev/shm/helcim-monitor.log"
LOOKBACK_DAYS = 30          # pull invoices from last 7 days each poll
POLL_INTERVAL = 300        # 5 minutes
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Free Zo model for notification dispatch
ZO_MODEL = "byok:a56c8f1f-a8e7-4524-a271-dd104b7f67da"  # 3.7 flash (current active model)

# --- Load secrets ---
def load_env(secrets_file=SECRETS_FILE):
    env = {}
    if os.path.exists(secrets_file):
        with open(secrets_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("export "):
                    line = line[7:]
                if "=" in line:
                    k, v = line.split("=", 1)
                    v = v.strip('"').strip("'").strip('"')
                    v = v.replace("\\", "")
                    env[k] = v
    return env

SECRETS = load_env()
HELCIM_KEY = SECRETS.get("HELCIM_API_KEY", "")
ZO_TOKEN = SECRETS.get("ZO_CLIENT_IDENTITY_TOKEN", "")

if not HELCIM_KEY:
    print("ERROR: HELCIM_API_KEY not found", file=sys.stderr)
    sys.exit(1)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def log(msg):
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


# --- SQLite ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY,
            invoice_number TEXT,
            amount REAL,
            amount_paid REAL,
            status TEXT,
            customer_name TEXT,
            description TEXT,
            date_created TEXT,
            date_paid TEXT,
            first_seen TEXT,
            status_changed TEXT,
            notified INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def get_db_invoice(conn, invoice_id):
    c = conn.cursor()
    c.execute("SELECT status FROM invoices WHERE invoice_id=?", (invoice_id,))
    row = c.fetchone()
    return row[0] if row else None


def upsert_invoice(conn, inv):
    """Insert or update an invoice. Returns True if status changed to PAID."""
    inv_id = inv.get("invoiceId")
    if inv_id is None:
        return False

    new_status = inv.get("status", "")
    old_status = get_db_invoice(conn, inv_id)

    invoice_number = inv.get("invoiceNumber", "?")
    amount = inv.get("amount", 0)
    amount_paid = inv.get("amountPaid", 0)
    customer = inv.get("billingAddress", {}).get("name", "Unknown")
    desc = ""
    if inv.get("lineItems"):
        desc = inv["lineItems"][0].get("description", "")
    date_created = inv.get("dateCreated", "")
    date_paid = inv.get("datePaid", "")
    ts = now()

    c = conn.cursor()
    if old_status is None:
        # New invoice - insert it
        c.execute("""
            INSERT INTO invoices (invoice_id, invoice_number, amount, amount_paid,
                status, customer_name, description, date_created, date_paid,
                first_seen, status_changed, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (inv_id, invoice_number, amount, amount_paid, new_status,
              customer, desc, date_created, date_paid, ts, ts,
              1 if new_status == "PAID" else 0))
        conn.commit()
        # Only notify if it's a new PAID invoice (transition from nothing to PAID)
        return new_status == "PAID"
    else:
        # Existing invoice - check for status change
        if old_status != new_status:
            c.execute("""
                UPDATE invoices SET status=?, amount_paid=?, date_paid=?,
                    status_changed=?, notified=0
                WHERE invoice_id=?
            """, (new_status, amount_paid, date_paid, ts, inv_id))
            conn.commit()
            # Notify only if it CHANGED to PAID (not was already PAID)
            return new_status == "PAID" and old_status != "PAID"
        else:
            # No status change - just update amounts if needed
            c.execute("""
                UPDATE invoices SET amount_paid=?, date_paid=? WHERE invoice_id=?
            """, (amount_paid, date_paid, inv_id))
            conn.commit()
            return False


# --- Helcim API ---
def fetch_invoices():
    ds = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    url = f"{HELCIM_API_BASE}/invoices?dateStart={ds}"
    req = urllib.request.Request(url, headers={
        "api-token": HELCIM_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            if isinstance(data, list):
                return data
            return []
    except Exception as e:
        log(f"Helcim fetch error: {e}")
        return []


# --- Notifications via Zo API (free model) ---
def send_notifications(invoices_paid):
    """Use /zo/ask with a free model to send SMS + Telegram for new payments."""
    if not invoices_paid:
        return

    for inv in invoices_paid:
        num = inv.get("invoiceNumber", "?")
        amount = inv.get("amountPaid") or inv.get("amount", 0)
        customer = inv.get("billingAddress", {}).get("name", "Unknown")
        desc = ""
        if inv.get("lineItems"):
            desc = inv["lineItems"][0].get("description", "")
        date_paid = inv.get("datePaid", "")

        msg = (
            f"💰 Payment received!\n\n"
            f"Invoice: {num}\n"
            f"Amount: ${amount}\n"
            f"Client: {customer}\n"
        )
        if desc:
            msg += f"Description: {desc}\n"
        if date_paid:
            msg += f"Paid: {date_paid}\n"

        # Send via Zo API - asks Zo to deliver via both Telegram and SMS
        prompt = (
            f"Send the following payment notification to Joe via BOTH Telegram "
            f"and SMS. Use the send_telegram_message tool and the send_sms_to_user "
            f"tool. Send this exact message:\n\n{msg}\n\n"
            f"Do not add anything. Just send the message via both channels."
        )

        if ZO_TOKEN:
            try:
                payload = json.dumps({
                    "input": prompt,
                    "model_name": ZO_MODEL,
                }).encode()
                req = urllib.request.Request(
                    "https://api.zo.computer/zo/ask",
                    data=payload,
                    headers={
                        "Authorization": ZO_TOKEN,
                        "Content-Type": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read())
                    log(f"Notification sent for {num}: {result.get('output', '')[:100]}")
            except Exception as e:
                log(f"Notification send error for {num}: {e}")
        else:
            log(f"No ZO_TOKEN - cannot send notification for {num}")


# --- Main check cycle ---
def check_once():
    invoices = fetch_invoices()
    if not invoices:
        log("No invoices returned")
        return

    conn = sqlite3.connect(DB_FILE)
    newly_paid = []

    for inv in invoices:
        try:
            if upsert_invoice(conn, inv):
                newly_paid.append(inv)
        except Exception as e:
            log(f"DB upsert error for invoice {inv.get('invoiceId')}: {e}")

    conn.close()

    if newly_paid:
        log(f"NEW payment(s): {len(newly_paid)} invoice(s) transitioned to PAID")
        send_notifications(newly_paid)
    else:
        log(f"No new payments (checked {len(invoices)} invoices)")


# --- Seed mode: populate DB with current state without notifying ---
def seed_db():
    """Fetch all current invoices and add them to DB without triggering notifications."""
    log("SEEDING DB with current invoice state (no notifications)...")
    invoices = fetch_invoices()
    conn = sqlite3.connect(DB_FILE)
    count = 0
    for inv in invoices:
        inv_id = inv.get("invoiceId")
        if inv_id is None:
            continue
        if get_db_invoice(conn, inv_id) is None:
            c = conn.cursor()
            c.execute("""
                INSERT INTO invoices (invoice_id, invoice_number, amount, amount_paid,
                    status, customer_name, description, date_created, date_paid,
                    first_seen, status_changed, notified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inv_id,
                inv.get("invoiceNumber", "?"),
                inv.get("amount", 0),
                inv.get("amountPaid", 0),
                inv.get("status", ""),
                inv.get("billingAddress", {}).get("name", "Unknown"),
                inv.get("lineItems", [{}])[0].get("description", "") if inv.get("lineItems") else "",
                inv.get("dateCreated", ""),
                inv.get("datePaid", ""),
                now(),
                now(),
                1,  # mark as notified so seeding doesn't trigger alerts
            ))
            count += 1
    conn.commit()
    conn.close()
    log(f"SEED COMPLETE: added {count} invoices to DB (none will trigger notifications)")


def main():
    # Check for --seed flag
    if "--seed" in sys.argv:
        init_db()
        seed_db()
        return

    # Check for --once flag (single check, no loop)
    once_mode = "--once" in sys.argv

    init_db()
    log(f"Helcim monitor started - polling every {POLL_INTERVAL}s")

    try:
        check_once()
    except Exception as e:
        log(f"Initial check error: {e}")

    if once_mode:
        return

    while True:
        time.sleep(POLL_INTERVAL)
        try:
            check_once()
        except Exception as e:
            log(f"Check error: {e}")


if __name__ == "__main__":
    main()