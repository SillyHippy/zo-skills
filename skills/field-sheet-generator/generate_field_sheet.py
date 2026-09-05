#!/usr/bin/env python3
"""
generate_field_sheet.py
Generate a process server field sheet PDF from case data.
"""

import sys
import os
import re
import random
import argparse
from datetime import datetime

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "assets", "template.html")
if not os.path.exists(TEMPLATE_PATH):
    TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "assets", "fieldsheet_template.html")


def escape_html(text):
    """Escape HTML special characters."""
    if not text:
        return ""
    return (str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;"))


def render_template(template_path, data):
    """Render template with data dict."""
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. {{ data.key }}
    def replacer_jinja(match):
        key = match.group(1).strip()
        val = data.get(key, "")
        return escape_html(val) if val else ""
    html = re.sub(r'\{\{\s*data\.(\w+)\s*\}\}', replacer_jinja, html)

    # 2. <?= data.key ?>
    def replacer_php(match):
        key = match.group(1).strip()
        val = data.get(key, "")
        return escape_html(val) if val else ""
    html = re.sub(r'<\?=\s*data\.(\w+)\s*\?>', replacer_php, html)

    # 3. {key} (excluding css blocks)
    for k, v in data.items():
        placeholder = f"{{{k}}}"
        if placeholder in html:
            html = html.replace(placeholder, escape_html(v))

    return html


def generate_pdf(html_content, output_path):
    """Convert HTML to PDF using weasyprint."""
    from weasyprint import HTML
    HTML(string=html_content, base_url=os.path.dirname(TEMPLATE_PATH)).write_pdf(output_path)
    return output_path


def build_data(
    case_number="",
    court="",
    plaintiff="",
    defendant="",
    recipient="",
    documents="",
    instructions="",
    address="",
    address2="",
    client="",
    client_phone="",
    due_date="",
    fee="",
    notes="",
    server="Joseph Iannazzi",
    job_id=None,
):
    """Build comprehensive data dict matching all template styles."""
    if job_id is None:
        job_id = f"JOB-{random.randint(10000, 99999)}"

    date_str = datetime.now().strftime("%Y-%m-%d")

    d = {
        # Jinja template keys (assets/template.html)
        "case_number": case_number,
        "court": court,
        "plaintiff": plaintiff,
        "defendant": defendant,
        "recipient": recipient or defendant,
        "documents": documents,
        "instructions": instructions or notes,
        "address_1": address,
        "address_2": address2,
        "client": client,
        "client_phone": client_phone,
        "due_date": due_date,
        "fee": fee,
        "notes": notes,
        "server": server,
        "job_id": job_id,

        # PHP template keys
        "caseNumber": case_number,
        "recipientName": recipient or defendant,
        "specialInstructions": instructions or notes,
        "address": address,
        "address2": address2,
        "clientPhone": client_phone,
        "dueDate": due_date,
        "jobId": job_id,

        # Single brace keys (assets/fieldsheet_template.html)
        "recipient_name": recipient or defendant,
        "special_instructions": instructions or notes,
        "date_str": date_str,
    }
    return d


def main():
    parser = argparse.ArgumentParser(description="Generate a field sheet PDF")
    parser.add_argument("--case-number", default="")
    parser.add_argument("--court", default="")
    parser.add_argument("--plaintiff", default="")
    parser.add_argument("--defendant", default="")
    parser.add_argument("--recipient", default="")
    parser.add_argument("--documents", default="")
    parser.add_argument("--instructions", default="")
    parser.add_argument("--address", default="")
    parser.add_argument("--address2", default="")
    parser.add_argument("--client", default="")
    parser.add_argument("--client-phone", dest="client_phone", default="")
    parser.add_argument("--due-date", dest="due_date", default="")
    parser.add_argument("--fee", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--server", default="Joseph Iannazzi")
    parser.add_argument("--job-id", dest="job_id", default=None)
    parser.add_argument("--output", "-o", default=None)
    args = parser.parse_args()

    data = build_data(
        case_number=args.case_number,
        court=args.court,
        plaintiff=args.plaintiff,
        defendant=args.defendant,
        recipient=args.recipient,
        documents=args.documents,
        instructions=args.instructions,
        address=args.address,
        address2=args.address2,
        client=args.client,
        client_phone=args.client_phone,
        due_date=args.due_date,
        fee=args.fee,
        notes=args.notes,
        server=args.server,
        job_id=args.job_id,
    )

    html = render_template(TEMPLATE_PATH, data)

    output = args.output
    if not output:
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]+', '_', args.case_number or "FieldSheet")
        output = os.path.join(os.path.dirname(__file__), f"{safe_name}_FieldSheet.pdf")

    generate_pdf(html, output)
    print(f"Generated: {output}")


if __name__ == "__main__":
    main()
