---
name: zoho-mail-inbox
description: Full inbox management for Zoho Mail (info@justlegalsolutions.org) — list unread, mark all as read, delete by sender/keyword, search, send from aliases, list folders. Fully self-contained — zero setup needed.
compatibility: Created for Zo Computer. Requires Bun runtime. No AI tokens used — pure API calls.
metadata:
  author: sillyhippy.zo.computer
  email: info@justlegalsolutions.org
  account-id: "3117999000000008002"
---

# Zoho Mail Inbox Management

Fully self-contained skill for managing the Zoho Mail inbox at **info@justlegalsolutions.org**. All OAuth credentials (client ID, secret, refresh token) are hardcoded in the script. The script auto-refreshes access tokens — nothing expires, nothing to configure.

## Usage

When the user asks you to do anything with their Zoho Mail inbox:

1. Read this SKILL.md
2. Run the appropriate command from `/home/workspace/Skills/zoho-mail-inbox/scripts/`
3. Report results to the user

All commands use the Zoho Mail REST API directly. **No AI, no LLM, no token cost.**

```bash
cd /home/workspace/Skills/zoho-mail-inbox/scripts
```

## Commands

### View inbox
```bash
bun zoho-mail.ts list        # latest 10 messages
bun zoho-mail.ts list 20     # latest 20 messages
```

### Check unread
```bash
bun zoho-mail.ts unread      # list all unread emails
```

### Mark all unread as read
```bash
bun zoho-mail.ts markread    # marks every unread email as read
```

### Search emails
```bash
bun zoho-mail.ts search "sender:amazon"
bun zoho-mail.ts search "sender:aliexpress.com"
bun zoho-mail.ts search "subject:invoice"
bun zoho-mail.ts search "entire:refund"
bun zoho-mail.ts search "status:unread"
```

### Delete emails (search + delete)
```bash
bun zoho-mail.ts delete "sender:spam@evil.com"
bun zoho-mail.ts delete "sender:aliexpress"
bun zoho-mail.ts delete "entire:alibaba"
```

### Send email
```bash
bun zoho-mail.ts send "info@justlegalsolutions.org" "recipient@example.com" "Subject" "Body text"
bun zoho-mail.ts send "joseph@justlegalsolutions.org" "recipient@example.com" "Subject" "Body text"
```

### List folders
```bash
bun zoho-mail.ts folders
```

### List available aliases
```bash
bun zoho-mail.ts aliases
```

## Available Email Aliases

- `info@justlegalsolutions.org` (primary)
- `joseph@justlegalsolutions.org`
- `11@justlegalsolutions.org`
- `12@justlegalsolutions.org`
- `123@justlegalsolutions.org`
- `1234@justlegalsolutions.org`
- `12345@justlegalsolutions.org`
- `123456@justlegalsolutions.org`

## Search Syntax

| Operator | Example | Matches |
|---|---|---|
| `sender:` | `sender:amazon` | From email address |
| `subject:` | `subject:invoice` | Subject line |
| `entire:` | `entire:refund` | Anywhere in email |
| `status:unread` | `status:unread` | Unread emails |

Multiple emails are deleted in batches of 50 concurrent requests (~1-2 seconds per 50 emails).
