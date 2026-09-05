#!/usr/bin/env python3
"""Poll Gmail for website form submissions; call Zo only when a new unread hit exists."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
STATE_FILE = SKILL_DIR / ".processed_ids.json"
SECRETS_FILE = Path("/root/.zo_secrets")
GMAIL_USER = "justlegalsolutionsok@gmail.com"
SUBJECT_EXACT = "New Service Request from Website Form"
ZO_ASK_URL = "https://api.zo.computer/zo/ask"
ZO_MODEL = "zo:deepseek/deepseek-v4-flash"
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "300"))


def load_secrets() -> dict[str, str]:
    out: dict[str, str] = {}
    if not SECRETS_FILE.exists():
        return out
    for line in SECRETS_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        v = v.replace("\\", "")
        out[k] = v
    for k, v in os.environ.items():
        if k.startswith("GMAIL_") or k.startswith("ZO_CLIENT"):
            out.setdefault(k, v)
    return out


def gmail_access_token(secrets: dict[str, str]) -> str:
    refresh = secrets.get("GMAIL_REFRESH_TOKEN", "").strip()
    client_id = secrets.get("GMAIL_DESKTOP_CLIENT_ID") or secrets.get("GMAIL_CLIENT_ID", "")
    client_secret = secrets.get("GMAIL_DESKTOP_CLIENT_SECRET") or secrets.get("GMAIL_CLIENT_SECRET", "")
    if not refresh:
        raise RuntimeError(
            "Missing GMAIL_REFRESH_TOKEN in Zo secrets. Add it under Settings → Advanced, "
            "then restart the website-form-watcher service."
        )
    if not client_id or not client_secret:
        raise RuntimeError("Missing GMAIL_DESKTOP_CLIENT_ID / GMAIL_DESKTOP_CLIENT_SECRET")

    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh,
            "grant_type": "refresh_token",
        }
    ).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"Token refresh failed: {data}")
    return token


def gmail_api(token: str, path: str, method: str = "GET", payload: dict | None = None) -> dict:
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/{path}"
    headers = {"Authorization": f"Bearer {token}"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def decode_body(payload: dict) -> str:
    def walk(part: dict) -> str:
        if part.get("body", {}).get("data"):
            raw = base64.urlsafe_b64decode(part["body"]["data"] + "==")
            mime = part.get("mimeType", "")
            if "text/plain" in mime or mime == "":
                return raw.decode(errors="replace")
        for sub in part.get("parts") or []:
            t = walk(sub)
            if t:
                return t
        return ""

    return walk(payload).strip()


def load_state() -> set[str]:
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()


def save_state(ids: set[str]) -> None:
    STATE_FILE.write_text(json.dumps(sorted(ids), indent=2))


def find_unread_hits(token: str) -> list[dict]:
    q = f'is:unread subject:"{SUBJECT_EXACT}"'
    listed = gmail_api(token, f"messages?q={urllib.parse.quote(q)}&maxResults=10")
    hits: list[dict] = []
    for meta in listed.get("messages") or []:
        mid = meta["id"]
        full = gmail_api(token, f"messages/{mid}?format=full")
        headers = {h["name"].lower(): h["value"] for h in full.get("payload", {}).get("headers", [])}
        subj = headers.get("subject", "")
        if subj.strip() != SUBJECT_EXACT:
            continue
        body = decode_body(full.get("payload", {}))
        if not body:
            body = full.get("snippet", "")
        hits.append(
            {
                "id": mid,
                "from": headers.get("from", ""),
                "subject": subj,
                "date": headers.get("date", ""),
                "body": body[:12000],
            }
        )
    return hits


def mark_read(token: str, msg_id: str) -> None:
    gmail_api(token, f"messages/{msg_id}/modify", method="POST", payload={"removeLabelIds": ["UNREAD"]})


def zo_ask_summarize_and_sms(secrets: dict[str, str], email: dict) -> None:
    auth = secrets.get("ZO_CLIENT_IDENTITY_TOKEN", "").strip()
    if not auth:
        raise RuntimeError("Missing ZO_CLIENT_IDENTITY_TOKEN")
    prompt = f"""You received a new website form submission email. Do exactly two steps:
1) Write a short SMS (under 480 characters) with the key fields from the email.
2) Call send_sms_to_user with that message only.

Do not email, Telegram, or do any other work.

From: {email.get('from', '')}
Subject: {email.get('subject', '')}
Date: {email.get('date', '')}

Email body:
{email.get('body', '')}
"""
    req = urllib.request.Request(
        ZO_ASK_URL,
        data=json.dumps({"input": prompt, "model_name": ZO_MODEL}).encode(),
        headers={
            "authorization": auth,
            "content-type": "application/json",
            "accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        out = json.loads(resp.read().decode())
    print(json.dumps({"zo_ask": "ok", "output_preview": str(out.get("output", ""))[:500]}))


def process_once() -> int:
    secrets = load_secrets()
    try:
        token = gmail_access_token(secrets)
    except RuntimeError as e:
        print(json.dumps({"error": str(e), "action": "add_gmail_refresh_token"}), file=sys.stderr)
        return 2

    state = load_state()
    hits = find_unread_hits(token)
    new_hits = [h for h in hits if h["id"] not in state]

    if not new_hits:
        print(json.dumps({"checked": True, "new": 0}))
        return 0

    for email in new_hits:
        print(json.dumps({"processing": email["id"], "subject": email["subject"]}))
        zo_ask_summarize_and_sms(secrets, email)
        mark_read(token, email["id"])
        state.add(email["id"])
    save_state(state)
    print(json.dumps({"checked": True, "new": len(new_hits)}))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Single poll then exit")
    args = parser.parse_args()
    if args.once:
        raise SystemExit(process_once())

    while True:
        try:
            process_once()
        except urllib.error.HTTPError as e:
            print(json.dumps({"http_error": e.code, "body": e.read().decode(errors="replace")[:800]}), file=sys.stderr)
        except Exception as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()