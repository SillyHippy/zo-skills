---
name: servtracker
description: |
  Add and manage entries in the ServTracker legal process serving database.
  Use when the user wants to add a new client, case, serve attempt, or document to ServTracker.
  The database is at /home/workspace/Projects/PDFUSAEDIT-zo/data/pdfusaedit.db.
  Changes appear instantly in the app at https://servetracker-sillyhippy.zocomputer.io/dashboard.
---
# ServTracker Skill

Direct SQLite database access — no browser or API auth needed.

## Usage

```bash
python3 /home/workspace/Skills/servtracker/scripts/servtracker.py <command> [options]
```

## Commands

### Ensure client exists (Check by email, then add if missing)
```bash
python3 servtracker.py ensure-client --email "john@example.com" --name "John Doe" --phone "918-555-1234" --address "123 Main St, Tulsa, OK 74103"
```

### Add a client
```bash
python3 servtracker.py add-client --name "John Doe" --email "john@example.com" --phone "918-555-1234" --address "123 Main St, Tulsa, OK 74103"
```

### Add a case to a client
```bash
python3 servtracker.py add-case --client-id <CLIENT_ID> --case-number "CV-2026-1234" --court "Tulsa County District Court" --plaintiff "Jane Smith" --defendant "John Doe" --home-address "123 Main St" --case-name "Smith v. Doe"
```

### Add a serve attempt
```bash
python3 servtracker.py add-serve --client-id <CLIENT_ID> --case-number "CV-2026-1234" --status "served" --address "123 Main St" --notes "Served at front door"
```

### Add a document
```bash
python3 servtracker.py add-document --client-id <CLIENT_ID> --file-name "petition.pdf" --file-path "/path/to/petition.pdf" --case-number "CV-2026-1234"
```

### List clients
```bash
python3 servtracker.py list-clients [--search "name"]
```

### List cases for a client
```bash
python3 servtracker.py list-cases --client-id <CLIENT_ID>
```

### Show a client with all cases
```bash
python3 servtracker.py show-client --client-id <CLIENT_ID>
```

## Database Location

The SQLite database is at: `/home/workspace/Projects/PDFUSAEDIT-zo/data/pdfusaedit.db`

## Tables

- **clients** — id (UUID), name, email, additional_emails (JSON), phone, address, notes, created_at, updated_at
- **client_cases** — id (UUID), client_id (FK), case_number, case_name, court_name, plaintiff_petitioner, defendant_respondent, home_address, work_address, notes, status (Open/Closed), created_at, updated_at
- **serve_attempts** — id (UUID), client_id (FK), client_name, case_number, case_name, status, notes, address, service_address, coordinates, image_url, image_file_id, timestamp, attempt_number
- **client_documents** — id (UUID), client_id (FK), case_number, file_name, file_size, file_type, file_path, description, created_at

## Notes

- All `id` fields are random UUIDs (use `random_uuid()`)
- Timestamps are ISO format UTC strings
- `additional_emails` is a JSON array string
- The `defendant_respondent` field in client_cases is the person to serve
- Write operations go directly to SQLite — changes appear immediately in the web app
