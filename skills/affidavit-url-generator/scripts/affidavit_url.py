#!/usr/bin/env python3
"""Generate pre-filled affidavit URL for justlegalsolutions.org/affidavit."""

import sys, re

ALLOWED_KEYS = [
    "Name of Court", "Plaintiff/Petitioner", "Defendant/Respondent",
    "Case Number", "Recipient Name", "Address", "Documents",
    "Personal Service", "Substituted at Residence", "Substituted at Business",
    "Posting", "Non-Service", "Unknown at address",
    "Moved left no forwarding", "Service canceled by litigant",
    "Unable to serve in a timely fashion", "Address does not exist", "Other",
    "Service attempt 1 Date", "Service attempt 1 time",
    "Service attempt 2 Date", "Service attempt 2 time",
    "Service attempt 3 Date", "Service attempt 3 time",
    "Service attempt 4 Date", "Service attempt 4 time",
    "Service attempt 5 Date", "Service attempt 5 time",
    "Service attempt 6 Date", "Service attempt 6 time",
    "Comments",
]
CHECKBOX_KEYS = {
    "Personal Service", "Substituted at Residence", "Substituted at Business",
    "Posting", "Non-Service", "Unknown at address", "Moved left no forwarding",
    "Service canceled by litigant", "Unable to serve in a timely fashion",
    "Address does not exist", "Other",
}

def encode_key(k): return k.replace(" ", "+").replace("/", "%2F")
def encode_value(v):
    r = []
    for c in v:
        if c == " ": r.append("+")
        elif c == ",": r.append("%2C")
        elif c == "'": r.append("%27")
        elif c == ";": r.append("%3B")
        elif c == ":": r.append("%3A")
        elif c == "/": r.append("%2F")
        elif c == "&": r.append("%26")
        elif c == "?": r.append("%3F")
        else: r.append(c)
    return "".join(r)

def is_cb_true(v): return v.strip().lower() in ("on", "true", "yes", "1", "checked", "selected", "✓", "✅", "x")

def generate(text):
    pairs = {}
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line: continue
        m = re.match(r"^(.+?)[:\u2014\u2013-]\s*(.*)", line)
        if m:
            k, v = m.group(1).strip(), m.group(2).strip()
            pairs[k] = v
    params = []
    for k, v in pairs.items():
        if k not in ALLOWED_KEYS: continue
        if k in CHECKBOX_KEYS:
            if is_cb_true(v): params.append(f"{encode_key(k)}=on")
        elif v:
            params.append(f"{encode_key(k)}={encode_value(v)}")
    base = "https://justlegalsolutions.org/affidavit"
    return f"{base}?{'&'.join(params)}" if params else base

if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()
    print(generate(text))
