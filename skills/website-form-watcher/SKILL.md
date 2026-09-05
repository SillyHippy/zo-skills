---
name: website-form-watcher
description: Poll justlegalsolutionsok@gmail.com for unread emails with subject "New Service Request from Website Form". No AI unless a new unread message is found; then one Zo session (DeepSeek V4 Flash) summarizes and texts Joe via send_sms_to_user.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---

# Website form watcher

## Subject line (exact)

`New Service Request from Website Form`

## Gmail account

`justlegalsolutionsok@gmail.com`

## Auth

Script reads OAuth refresh token from Zo secret **`GMAIL_REFRESH_TOKEN`** (add in Settings → Advanced if missing), plus `GMAIL_DESKTOP_CLIENT_ID` / `GMAIL_DESKTOP_CLIENT_SECRET` from `/root/.zo_secrets`.

## Run once (test)

```bash
python3 /home/workspace/Skills/website-form-watcher/scripts/watch.py --once
```

## Service (every 5 minutes, no AI on empty inbox)

Managed service **website-form-watcher** runs the same script in a loop (`POLL_SECONDS=300`).

## On new unread email

1. Mark message read after processing (state file prevents duplicates).
2. POST `https://api.zo.computer/zo/ask` with `model_name`: `zo:deepseek/deepseek-v4-flash`
3. Prompt instructs Zo to summarize the email for SMS and call `send_sms_to_user` only.

## State

`/home/workspace/Skills/website-form-watcher/.processed_ids.json`