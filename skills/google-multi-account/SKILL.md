---
name: google-multi-account
description: "Multi-Account Gmail & Google Workspace engine (Drive, Mail, Calendar, Sheets, Docs, Filter Management)."
version: 1.0.0
license: MIT
---

# Google Multi-Account Hub (Gmail, Drive, Calendar, Docs, Sheets)

Unified multi-account management for Gmail and Google Workspace across all connected accounts.

## Locations
- Engine CLI: `/home/workspace/gmail-filters/gmail_hub.py`
- Token Store: `/home/workspace/credentials/gmail_multi_tokens.json`
- Filter Config: `/home/workspace/gmail-filters/filters.json`

## Permissions (Master Scopes)
- **Gmail:** Full mail access (`https://mail.google.com/`), settings (`gmail.settings.basic`), modify (`gmail.modify`)
- **Drive & Docs & Sheets:** `drive`, `drive.file`, `spreadsheets`, `documents`, `presentations`
- **Calendar & Contacts:** `calendar`, `calendar.events`, `tasks`, `contacts`
- **YouTube & Profile:** `youtube`, `userinfo.email`, `userinfo.profile`

## CLI Commands

### 1. List All Connected Accounts
```bash
python3 /home/workspace/gmail-filters/gmail_hub.py list-accounts
```

### 2. Generate Full-Scope Auth URL
```bash
python3 /home/workspace/gmail-filters/gmail_hub.py auth-url
# Or with login hint:
python3 /home/workspace/gmail-filters/gmail_hub.py auth-url --email user@gmail.com
```

### 3. Add Account From Redirect URL or Code
```bash
python3 /home/workspace/gmail-filters/gmail_hub.py add-account "http://localhost:1/?code=..."
```

### 4. Deploy Filters & Retroactive Clean Across All Inboxes
```bash
python3 /home/workspace/gmail-filters/gmail_hub.py sync all
```

### 5. Targeted Ad-Hoc Cleanup (e.g. Delete Old Promos)
```bash
python3 /home/workspace/gmail-filters/gmail_hub.py retroactive-clean all --query "older_than:90d category:promotions" --trash
```
