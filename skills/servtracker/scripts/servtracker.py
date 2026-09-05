#!/usr/bin/env python3
"""ServTracker — direct SQLite database operations for the ServTracker app."""

import argparse
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone

DB_PATH = "/home/workspace/Projects/PDFUSAEDIT-zo/data/pdfusaedit.db"


def now():
    return datetime.now(timezone.utc).isoformat()


def new_id():
    return uuid.uuid4().hex


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def print_rows(rows):
    for r in rows:
        print(dict(r))


def add_client(args):
    db = get_db()
    client_id = new_id()
    t = now()
    db.execute(
        "INSERT INTO clients (id, name, email, phone, address, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [client_id, args.name, args.email or "", args.phone or "", args.address or "", args.notes or "", t, t],
    )
    db.commit()
    print(f"Client added: {client_id}")
    print(f"  Name: {args.name}")
    print(f"  Email: {args.email or ''}")
    db.close()
    return client_id


def ensure_client(args):
    db = get_db()
    # Check if client exists by email (exact match)
    row = db.execute("SELECT id, name FROM clients WHERE email = ?", [args.email]).fetchone()
    if row:
        client_id = row["id"]
        print(f"Existing client found: {client_id} ({row['name']})")
        db.close()
        return client_id

    # If not found, create new
    client_id = new_id()
    t = now()
    db.execute(
        "INSERT INTO clients (id, name, email, phone, address, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [client_id, args.name, args.email or "", args.phone or "", args.address or "", args.notes or "", t, t],
    )
    db.commit()
    print(f"New client created: {client_id}")
    print(f"  Name: {args.name}")
    print(f"  Email: {args.email}")
    db.close()
    return client_id


def add_case(args):
    db = get_db()
    case_id = new_id()
    t = now()
    db.execute(
        """INSERT INTO client_cases
        (id, client_id, case_number, case_name, court_name, plaintiff_petitioner, defendant_respondent, home_address, work_address, notes, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            case_id,
            args.client_id,
            args.case_number,
            args.case_name or "",
            args.court or "",
            args.plaintiff or "",
            args.defendant or "",
            args.home_address or "",
            args.work_address or "",
            args.notes or "",
            args.status or "Open",
            t,
            t,
        ],
    )
    db.commit()
    print(f"Case added: {case_id}")
    print(f"  Case #: {args.case_number}")
    print(f"  Defendant: {args.defendant or ''}")
    db.close()


def add_serve(args):
    db = get_db()
    serve_id = new_id()
    t = now()
    # Resolve client_name from client_id
    row = db.execute("SELECT name FROM clients WHERE id = ?", [args.client_id]).fetchone()
    client_name = row["name"] if row else ""
    db.execute(
        """INSERT INTO serve_attempts
        (id, client_id, client_name, case_number, case_name, status, notes, address, service_address, timestamp, attempt_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            serve_id,
            args.client_id,
            client_name,
            args.case_number or "",
            args.case_name or "",
            args.status or "unknown",
            args.notes or "",
            args.address or "",
            args.address or "",
            t,
            args.attempt or 1,
        ],
    )
    db.commit()
    print(f"Serve attempt added: {serve_id}")
    print(f"  Status: {args.status or 'unknown'}")
    print(f"  Address: {args.address or ''}")
    db.close()


def add_document(args):
    db = get_db()
    doc_id = new_id()
    t = now()
    file_size = 0
    try:
        file_size = os.path.getsize(args.file_path)
    except OSError:
        pass
    db.execute(
        """INSERT INTO client_documents
        (id, client_id, case_number, file_name, file_size, file_type, file_path, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            doc_id,
            args.client_id,
            args.case_number or "",
            args.file_name,
            file_size,
            args.file_type or "",
            args.file_path,
            args.description or "",
            t,
        ],
    )
    db.commit()
    print(f"Document added: {doc_id}")
    print(f"  File: {args.file_name}")
    db.close()


def list_clients(args):
    db = get_db()
    if args.search:
        rows = db.execute(
            "SELECT * FROM clients WHERE name LIKE ? OR email LIKE ? ORDER BY created_at DESC",
            [f"%{args.search}%", f"%{args.search}%"],
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM clients ORDER BY created_at DESC").fetchall()
    print_rows(rows)
    db.close()


def list_cases(args):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM client_cases WHERE client_id = ? ORDER BY created_at DESC",
        [args.client_id],
    ).fetchall()
    print_rows(rows)
    db.close()


def show_client(args):
    db = get_db()
    client = db.execute("SELECT * FROM clients WHERE id = ?", [args.client_id]).fetchone()
    if not client:
        print("Client not found")
        db.close()
        sys.exit(1)
    print(json.dumps(dict(client), indent=2))
    cases = db.execute(
        "SELECT * FROM client_cases WHERE client_id = ? ORDER BY created_at DESC",
        [args.client_id],
    ).fetchall()
    print("\n--- Cases ---")
    print_rows(cases)
    serves = db.execute(
        "SELECT * FROM serve_attempts WHERE client_id = ? ORDER BY timestamp DESC LIMIT 10",
        [args.client_id],
    ).fetchall()
    print("\n--- Recent Serves ---")
    print_rows(serves)
    db.close()


def main():
    parser = argparse.ArgumentParser(description="ServTracker database tool")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add-client")
    p.add_argument("--name", required=True)
    p.add_argument("--email", default="")
    p.add_argument("--phone", default="")
    p.add_argument("--address", default="")
    p.add_argument("--notes", default="")

    p = sub.add_parser("ensure-client")
    p.add_argument("--email", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--phone", default="")
    p.add_argument("--address", default="")
    p.add_argument("--notes", default="")

    p = sub.add_parser("add-case")
    p.add_argument("--client-id", required=True)
    p.add_argument("--case-number", required=True)
    p.add_argument("--case-name", default="")
    p.add_argument("--court", default="")
    p.add_argument("--plaintiff", default="")
    p.add_argument("--defendant", default="")
    p.add_argument("--home-address", default="")
    p.add_argument("--work-address", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--status", default="Open")

    p = sub.add_parser("add-serve")
    p.add_argument("--client-id", required=True)
    p.add_argument("--case-number", default="")
    p.add_argument("--case-name", default="")
    p.add_argument("--status", default="unknown")
    p.add_argument("--address", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--attempt", type=int, default=1)

    p = sub.add_parser("add-document")
    p.add_argument("--client-id", required=True)
    p.add_argument("--file-name", required=True)
    p.add_argument("--file-path", required=True)
    p.add_argument("--case-number", default="")
    p.add_argument("--file-type", default="")
    p.add_argument("--description", default="")

    p = sub.add_parser("list-clients")
    p.add_argument("--search", default="")

    p = sub.add_parser("list-cases")
    p.add_argument("--client-id", required=True)

    p = sub.add_parser("show-client")
    p.add_argument("--client-id", required=True)

    args = parser.parse_args()
    {"add-client": add_client, "add-case": add_case, "add-serve": add_serve, "add-document": add_document, "list-clients": list_clients, "list-cases": list_cases, "show-client": show_client, "ensure-client": ensure_client}[args.command](args)


if __name__ == "__main__":
    main()
