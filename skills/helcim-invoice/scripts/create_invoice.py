#!/usr/bin/env python3
"""Create / update Helcim invoices for Just Legal Solutions.

HARD RULES (Joe — do not regress):
1. Email is REQUIRED. Helcim only stores it on billingAddress.email (and
   shippingAddress.email). Top-level "email" is ignored.
2. Pay URL is ALWAYS:
   https://just-legal-solutions.myhelcim.com/order/?token={token}
   NEVER secure.myhelcim.com/invoice/...
3. Linking customerId does NOT auto-copy billing email onto the invoice —
   billingAddress must be sent on every create.
4. If an existing customer is found, their billingAddress.email is updated
   when missing or different before the invoice is created.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SECRETS_FILE = "/root/.zo_secrets"
API_BASE = "https://api.helcim.com/v2"
USER_AGENT = "ZoComputer/1.0"
# ONLY correct pay URL base — never secure.myhelcim.com
DEFAULT_INVOICE_BASE_URL = "https://just-legal-solutions.myhelcim.com/order/?token="


def get_api_token():
    """Read HELCIM token raw from .zo_secrets (avoid bash $ corruption)."""
    with open(SECRETS_FILE, "r") as f:
        text = f.read()
    for key in ("HELCIM_API_TOKEN", "HELCIM_API_KEY"):
        m = re.search(rf'(?:export\s+)?{key}=["\']([^"\']+)["\']', text)
        if m:
            return m.group(1).replace("\\", "")
        # unquoted
        m = re.search(rf'(?:export\s+)?{key}=(\S+)', text)
        if m:
            return m.group(1).replace("\\", "")
    print("ERROR: HELCIM_API_TOKEN/KEY not found in " + SECRETS_FILE, file=sys.stderr)
    sys.exit(1)


def build_payment_link(invoice):
    """ONLY correct Helcim online invoice URL."""
    token = invoice.get("token") if isinstance(invoice, dict) else None
    if not token:
        return None
    # Ignore any env override that points at secure.myhelcim.com
    base_url = os.environ.get("HELCIM_INVOICE_BASE_URL", DEFAULT_INVOICE_BASE_URL).strip()
    if "secure.myhelcim.com" in base_url or "/invoice/" in base_url:
        base_url = DEFAULT_INVOICE_BASE_URL
    if "{token}" in base_url:
        return base_url.replace("{token}", urllib.parse.quote(str(token), safe=""))
    if "just-legal-solutions.myhelcim.com/order/?token=" not in base_url:
        base_url = DEFAULT_INVOICE_BASE_URL
    if not base_url.endswith("=") and "?token=" not in base_url:
        base_url = base_url.rstrip("/") + "/order/?token="
    return base_url + str(token)


def api_request(method, path, data=None, token=None):
    url = API_BASE + path
    body = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {
        "api-token": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        e.error_body = err_body
        print(f"ERROR {e.code}: {err_body}", file=sys.stderr)
        raise


def customer_email(c):
    if not isinstance(c, dict):
        return ""
    for key in ("billingAddress", "shippingAddress"):
        addr = c.get(key)
        if isinstance(addr, dict) and addr.get("email"):
            return (addr.get("email") or "").strip()
    return ""


def make_address(name, email, phone="", street1="N/A", city="", province="OK",
                 country="USA", postal_code="00000"):
    addr = {
        "name": name or email or "Customer",
        "street1": street1 or "N/A",
        "street2": "",
        "city": city or "",
        "province": province or "OK",
        "country": country or "USA",
        "postalCode": postal_code or "00000",
    }
    digits = re.sub(r"\D", "", phone or "")[:16]
    if digits:
        addr["phone"] = digits
    addr["email"] = email
    return addr


def find_customer_by_name(token, name):
    result = api_request("GET", f"/customers/?contactName={urllib.parse.quote(name)}", token=token)
    customers = result if isinstance(result, list) else []
    name_lower = name.lower().strip()
    for c in customers:
        if (c.get("contactName") or "").lower().strip() == name_lower:
            return c
    return None


def find_customer_by_email(token, email):
    result = api_request("GET", "/customers/", token=token)
    customers = result if isinstance(result, list) else []
    email_lower = email.lower().strip()
    for c in customers:
        if customer_email(c).lower() == email_lower:
            return c
    return None


def update_customer_email(token, customer_id, name, email, phone="",
                          address=None, city=None, province=None, country="USA", postal_code=None):
    addr = make_address(
        name, email, phone,
        street1=address or "N/A",
        city=city or "",
        province=province or "OK",
        country=country or "USA",
        postal_code=postal_code or "00000",
    )
    payload = {
        "contactName": name,
        "billingAddress": addr,
        "shippingAddress": addr,
    }
    digits = re.sub(r"\D", "", phone or "")
    if 10 <= len(digits) <= 16:
        payload["cellPhone"] = digits
    return api_request("PUT", f"/customers/{customer_id}", data=payload, token=token)


def create_customer(token, name, email, phone="", address=None, city=None,
                    province=None, country="USA", postal_code=None):
    addr = make_address(
        name, email, phone,
        street1=address or "N/A",
        city=city or "",
        province=province or "OK",
        country=country or "USA",
        postal_code=postal_code or "00000",
    )
    data = {
        "contactName": name,
        "billingAddress": addr,
        "shippingAddress": addr,
    }
    digits = re.sub(r"\D", "", phone or "")
    if 10 <= len(digits) <= 16:
        data["cellPhone"] = digits
    return api_request("POST", "/customers/", data=data, token=token)


def ensure_customer(token, name, email="", phone="", address=None, city=None,
                    province=None, country="USA", postal_code=None):
    """Find or create customer."""
    if not email:
        email = ""
    if not name:
        name = "Customer"

    if email and "@" in email:
        customer = find_customer_by_name(token, name)
        if not customer:
            customer = find_customer_by_email(token, email)
    else:
        customer = find_customer_by_name(token, name)

    if customer:
        cid = customer["id"]
        existing = customer_email(customer)
        if email and existing.lower() != email.strip().lower():
            customer = update_customer_email(
                token, cid, name, email.strip(), phone,
                address=address, city=city, province=province,
                country=country, postal_code=postal_code,
            )
            print(json.dumps({
                "status": "updated_customer_email",
                "customerId": cid,
                "email": email.strip(),
            }), file=sys.stderr)
        else:
            print(json.dumps({
                "status": "existing_customer",
                "customerId": cid,
                "email": existing,
            }), file=sys.stderr)
        return customer

    new_c = create_customer(
        token, name, email.strip() if email else "", phone=phone,
        address=address, city=city, province=province,
        country=country, postal_code=postal_code,
    )
    cid = new_c["id"]
    fresh = api_request("GET", f"/customers/{cid}", token=token)
    return fresh


def parse_line_items(args):
    """Support --line 'desc|price' repeated, or single --amount/--description."""
    items = []
    if getattr(args, "line", None):
        for raw in args.line:
            if "|" not in raw:
                raise SystemExit(f"ERROR: --line must be 'description|price', got: {raw}")
            desc, price_s = raw.rsplit("|", 1)
            items.append({
                "description": desc.strip(),
                "quantity": 1,
                "price": float(price_s.strip()),
                "total": float(price_s.strip()),
            })
    if args.amount is not None and args.description:
        items.append({
            "description": args.description,
            "quantity": 1,
            "price": float(args.amount),
            "total": float(args.amount),
        })
    if not items:
        raise SystemExit("ERROR: provide --line 'desc|price' (repeatable) and/or --amount + --description")
    return items


def create_invoice(token, customer_id, line_items, invoice_number=None, notes=None,
                   billing_name=None, billing_email=None, phone="",
                   address=None, city=None, province=None, country="USA", postal_code=None):
    addr = make_address(
        billing_name or billing_email or "Customer", billing_email or "", phone,
        street1=address or "N/A",
        city=city or "",
        province=province or "OK",
        country=country or "USA",
        postal_code=postal_code or "00000",
    )
    # Helcim line items: description, quantity, price (total optional)
    api_items = []
    amount = 0.0
    for li in line_items:
        price = float(li["price"])
        qty = float(li.get("quantity", 1) or 1)
        amount += price * qty
        api_items.append({
            "description": li["description"],
            "quantity": qty,
            "price": price,
            "total": round(price * qty, 2),
        })

    payload = {
        "currency": "USD",
        "status": "DUE",
        "type": "INVOICE",
        "amount": round(amount, 2),
        "lineItems": api_items,
        "customerId": customer_id,
        "billingAddress": addr,
        "shipping": {"amount": 0, "details": "N/A", "address": addr},
    }
    if invoice_number:
        payload["invoiceNumber"] = invoice_number
    if notes:
        payload["notes"] = notes

    try:
        return api_request("POST", "/invoices/", data=payload, token=token)
    except urllib.error.HTTPError as e:
        err_body = getattr(e, "error_body", "") or ""
        if e.code == 400 and "already existed" in err_body and "invoiceNumber" in payload:
            print("Invoice number conflict — retrying with auto number", file=sys.stderr)
            payload.pop("invoiceNumber", None)
            return api_request("POST", "/invoices/", data=payload, token=token)
        raise


def finalize_result(result, email):
    payment_link = build_payment_link(result)
    if payment_link:
        result["paymentLink"] = payment_link
        result["pay_url"] = payment_link
    result["sendToEmail"] = email
    # Guardrails in output
    if payment_link and "just-legal-solutions.myhelcim.com/order/?token=" not in payment_link:
        raise SystemExit(f"ERROR: bad pay URL generated: {payment_link}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Helcim invoices — email + correct pay URL enforced")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("create", help="Create invoice (default)")

    up = sub.add_parser("update", help="Update invoice by id")
    up.add_argument("--invoice-id", required=True)
    up.add_argument("--amount", type=float, default=None)
    up.add_argument("--description", default=None)
    up.add_argument("--status", default=None,
                    choices=["CANCELLED", "DUE", "PAID", "SHIPPED", "COMPLETED", "REFUNDED", "IN_PROGRESS"])
    up.add_argument("--notes", default=None)
    up.add_argument("--invoice-number", default=None)
    up.add_argument("--customer-id", type=int, default=None)
    up.add_argument("--email", default=None, help="Force billing email on invoice")
    up.add_argument("--name", default=None, help="Billing name when setting email")

    cancel = sub.add_parser("cancel")
    cancel.add_argument("--invoice-id", required=True)

    getp = sub.add_parser("get")
    getp.add_argument("--invoice-id", required=True)

    # create args (also on root for backward compat)
    parser.add_argument("--name", default=None)
    parser.add_argument("--email", default=None)
    parser.add_argument("--phone", default=None)
    parser.add_argument("--amount", type=float, default=None)
    parser.add_argument("--description", default=None)
    parser.add_argument("--line", action="append", default=None,
                        help="Line item as 'description|price' (repeatable). Prefer over single amount.")
    parser.add_argument("--invoice-number", default=None)
    parser.add_argument("--notes", default=None)
    parser.add_argument("--address", default=None)
    parser.add_argument("--city", default=None)
    parser.add_argument("--province", default=None)
    parser.add_argument("--country", default="USA")
    parser.add_argument("--postal-code", default=None)

    args = parser.parse_args()
    command = args.command or "create"
    token = get_api_token()

    if command == "get":
        result = api_request("GET", f"/invoices/{args.invoice_id}", token=token)
        ba = result.get("billingAddress") or {}
        email = (ba.get("email") if isinstance(ba, dict) else "") or ""
        print(json.dumps(finalize_result(result, email), indent=2))
        return

    if command == "cancel":
        current = api_request("GET", f"/invoices/{args.invoice_id}", token=token)
        line_items = current.get("lineItems") or [{"description": "Cancelled", "quantity": 1, "price": 0}]
        payload = {
            "currency": current.get("currency", "USD"),
            "lineItems": line_items,
            "status": "CANCELLED",
        }
        result = api_request("PUT", f"/invoices/{args.invoice_id}", data=payload, token=token)
        ba = result.get("billingAddress") or {}
        email = (ba.get("email") if isinstance(ba, dict) else "") or ""
        print(json.dumps(finalize_result(result, email), indent=2))
        return

    if command == "update":
        current = api_request("GET", f"/invoices/{args.invoice_id}", token=token)
        line_items = current.get("lineItems") or []
        if args.amount is not None or args.description is not None:
            if line_items:
                li = dict(line_items[0])
                if args.amount is not None:
                    li["price"] = args.amount
                if args.description is not None:
                    li["description"] = args.description
                line_items = [li] + list(line_items[1:])
            else:
                line_items = [{
                    "description": args.description or "Service",
                    "quantity": 1,
                    "price": args.amount or 0,
                }]
        if not line_items:
            line_items = [{"description": "Service", "quantity": 1, "price": 0}]
        payload = {
            "currency": current.get("currency", "USD"),
            "lineItems": line_items,
        }
        if args.status is not None:
            payload["status"] = args.status
        if args.notes is not None:
            payload["notes"] = args.notes
        if args.invoice_number is not None:
            payload["invoiceNumber"] = args.invoice_number
        if args.customer_id is not None:
            payload["customerId"] = args.customer_id
        if args.email:
            name = args.name or (current.get("billingAddress") or {}).get("name") or args.email
            payload["billingAddress"] = make_address(name, args.email)
        result = api_request("PUT", f"/invoices/{args.invoice_id}", data=payload, token=token)
        ba = result.get("billingAddress") or {}
        email = (ba.get("email") if isinstance(ba, dict) else "") or (args.email or "")
        print(json.dumps(finalize_result(result, email), indent=2))
        return

    # create
    if not args.name:
        args.name = "N/A"
    if not args.email:
        args.email = ""
    line_items = parse_line_items(args)

    customer = ensure_customer(
        token, args.name, args.email or "", phone=args.phone or "",
        address=args.address, city=args.city, province=args.province,
        country=args.country, postal_code=args.postal_code,
    )
    customer_id = customer["id"]

    result = create_invoice(
        token=token,
        customer_id=customer_id,
        line_items=line_items,
        invoice_number=args.invoice_number,
        notes=args.notes,
        billing_name=args.name,
        billing_email=args.email.strip() if args.email else "",
        phone=args.phone or "",
        address=args.address,
        city=args.city,
        province=args.province,
        country=args.country,
        postal_code=args.postal_code,
    )

    # Post-create verify: email on invoice billingAddress
    ba = result.get("billingAddress") or {}
    got_email = (ba.get("email") if isinstance(ba, dict) else "") or ""
    if args.email and got_email.lower() != args.email.strip().lower():
        # try PUT fix with full line items preserved
        print("WARN: invoice missing billing email — forcing PUT", file=sys.stderr)
        put_payload = {
            "currency": "USD",
            "lineItems": result.get("lineItems") or line_items,
            "customerId": customer_id,
            "billingAddress": make_address(args.name, args.email.strip(), args.phone or ""),
            "status": result.get("status") or "DUE",
        }
        if args.notes:
            put_payload["notes"] = args.notes
        result = api_request("PUT", f"/invoices/{result['invoiceId']}", data=put_payload, token=token)
        ba = result.get("billingAddress") or {}
        got_email = (ba.get("email") if isinstance(ba, dict) else "") or ""
        if got_email.lower() != args.email.strip().lower():
            raise SystemExit(
                f"ERROR: invoice {result.get('invoiceId')} created but email still missing on billingAddress"
            )

    out = finalize_result(result, args.email.strip() if args.email else "")
    # Final hard asserts before printing to Joe
    assert "just-legal-solutions.myhelcim.com/order/?token=" in (out.get("pay_url") or "")
    assert "secure.myhelcim.com" not in (out.get("pay_url") or "")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
