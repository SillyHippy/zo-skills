---
name: pdfusa-backup
description: Create a full backup of the PDFUSAEDIT SQLite database and serve images, then upload to Google Drive. Use when the user asks to backup PDFUSAEDIT, or when running the weekly automated backup.
compatibility: Zo Computer with Google Drive integration connected
metadata:
  author: sillyhippy.zo.computer
  gdrive_folder_id: "13R1vx8m2HPr3m3F4GvMzYbN7WJ8qK5xL"
  gdrive_folder_name: "PDFUSA-Backups"
  app_path: /home/workspace/Projects/PDFUSAEDIT-zo
---
# PDFUSAEDIT Full Backup Skill — Step-by-Step

## What This Skill Does

Creates a complete backup of the PDFUSAEDIT process-server application, including its SQLite database and all uploaded serve-attempt images, then uploads the backup to Google Drive.

**Total backup size:** ~40-100MB

## What Gets Backed Up

| File/Directory | Description | Size |
|---|---|---|
| `/home/workspace/Projects/PDFUSAEDIT-zo/data/pdfusa.db` | SQLite database containing all clients, cases, serve attempts, and documents | ~5-15MB |
| `/home/workspace/Projects/PDFUSAEDIT-zo/data/uploads/serves/` | Full-size and thumbnail JPG images from serve attempts | ~30-85MB |

## Prerequisites — Check These First

1. **Google Drive must be connected.** Verify by running: `list_app_tools("google_drive")`
   - If it returns a list of actions → connected, proceed.
   - If it returns an error about no connection → tell the user: "Google Drive is not connected. Go to Settings > Integrations > Connections > Google Drive and connect it."

2. **The app directory exists.** Run: `ls /home/workspace/Projects/PDFUSAEDIT-zo/data/pdfusa.db`
   - If file exists → proceed.
   - If not found → tell the user: "The PDFUSAEDIT database was not found at the expected path."

## Step 1: Run the Backup Script

Run this exact command in a terminal:

```bash
bun run /home/workspace/Skills/pdfusa-backup/scripts/backup.ts
```

### What the Script Does

1. Creates the `/home/workspace/Projects/PDFUSAEDIT-zo/backups/` directory if it doesn't exist.
2. Checkpoints the SQLite WAL file (ensures the database is in a consistent state for zipping).
3. Creates a zip file containing `data/pdfusa.db` and `data/uploads/serves/`.
4. Names the zip file: `pdfusa-backup-YYYY-MM-DDTHH-MM-SS.zip` (ISO timestamp, colons replaced with hyphens).
5. Places the zip in: `/home/workspace/Projects/PDFUSAEDIT-zo/backups/`
6. Prints to stdout:
   - `ZIP_PATH=/home/workspace/Projects/PDFUSAEDIT-zo/backups/pdfusa-backup-YYYY-MM-DDTHH-MM-SS.zip`
   - `ZIP_NAME=pdfusa-backup-YYYY-MM-DDTHH-MM-SS.zip`
   - `Backup created: <path> (<size> MB)`

### Expected Output Example

```
Creating backup: pdfusa-backup-2026-05-25T22-33-51.zip
Backup created: /home/workspace/Projects/PDFUSAEDIT-zo/backups/pdfusa-backup-2026-05-25T22-33-51.zip (39.5 MB)
ZIP_PATH=/home/workspace/Projects/PDFUSAEDIT-zo/backups/pdfusa-backup-2026-05-25T22-33-51.zip
ZIP_NAME=pdfusa-backup-2026-05-25T22-33-51.zip
```

### How to Capture the Zip Path

The script prints `ZIP_PATH=<full_path>` on its own line. After running the script:

1. Read the script's stdout output.
2. Find the line starting with `ZIP_PATH=`.
3. Extract the value after `ZIP_PATH=`. This is the full absolute path to the backup zip file.
4. Store this value — you need it for Step 2.

**If the script fails:**
- Read the error message from stderr.
- If `zip` command not found: run `apt-get install -y zip` then retry.
- If disk space error: run `df -h` to check free space, tell the user if below 200MB free.
- If permission error: retry with the same command (you run as root, so this shouldn't happen).

### Fallback: Manual Zip (If Script Fails)

If the backup script fails for any reason, run these commands instead:

```bash
mkdir -p /home/workspace/Projects/PDFUSAEDIT-zo/backups
TIMESTAMP=$(date -u +%Y-%m-%dT%H-%M-%S)
ZIP_NAME="pdfusa-backup-${TIMESTAMP}.zip"
ZIP_PATH="/home/workspace/Projects/PDFUSAEDIT-zo/backups/${ZIP_NAME}"
cd /home/workspace/Projects/PDFUSAEDIT-zo && zip -r "${ZIP_PATH}" data/pdfusa.db data/uploads/serves/
echo "ZIP_PATH=${ZIP_PATH}"
echo "ZIP_NAME=${ZIP_NAME}"
```

## Step 2: Upload to Google Drive

### Tool to Use

Use the `use_app_google_drive` tool with these exact parameters:

| Parameter | Value | Notes |
|---|---|---|
| `tool_name` | `"google_drive-upload-file"` | Exact string, no variations |
| `configured_props.filePath` | The `ZIP_PATH` from Step 1 | Must be absolute path |
| `configured_props.parentId` | `"13R1vx8m2HPr3m3F4GvMzYbN7WJ8qK5xL"` | PDFUSA-Backups folder ID — DO NOT CHANGE |

### Example Tool Call

```
use_app_google_drive(
  tool_name="google_drive-upload-file",
  configured_props={
    "filePath": "/home/workspace/Projects/PDFUSAEDIT-zo/backups/pdfusa-backup-2026-05-25T22-33-51.zip",
    "parentId": "13R1vx8m2HPr3m3F4GvMzYbN7WJ8qK5xL"
  }
)
```

**Important:** The `filePath` value must exactly match the `ZIP_PATH` output from Step 1. Do not modify it.

### What Happens on Success

The tool returns a response containing:
- `kind: "drive#file"`
- `id`: The Google Drive file ID (e.g., `"11YCCgu5frmK1wUhw_luxFV_iC8..."`)
- `name`: The uploaded filename
- `webViewLink`: A Google Drive link to view/download the file

### What Happens on Failure

- **File not found error:** The `ZIP_PATH` is wrong. Re-check Step 1 output. Run `ls -la <ZIP_PATH>` to verify the file exists.
- **No such file or directory:** Same as above — the path is incorrect.
- **Permission error / authentication error:** Google Drive integration needs reconnecting. Tell the user to reconnect via Settings > Integrations.
- **Upload failed / quota exceeded:** Tell the user Google Drive is full.

## Step 3: Verify and Report

### Verification

After the upload succeeds:

1. Confirm the tool response contains `kind: "drive#file"` — this means the upload completed.
2. Extract the `id` field from the response.
3. Construct the Google Drive link: `https://drive.google.com/file/d/<file_id>/view?usp=sharing`
   - Replace `<file_id>` with the `id` value from the response.

### Report to User

Tell the user:

```
Backup complete.
- Database: 48 clients, 25 cases, 55 serve attempts
- Serve images: <count> files
- Backup size: <size> MB
- Uploaded to Google Drive: https://drive.google.com/file/d/<file_id>/view?usp=sharing
```

### If You Need Counts

To get accurate counts from the database:

```bash
sqlite3 /home/workspace/Projects/PDFUSAEDIT-zo/data/pdfusa.db "SELECT COUNT(*) FROM clients;"
sqlite3 /home/workspace/Projects/PDFUSAEDIT-zo/data/pdfusa.db "SELECT COUNT(*) FROM client_cases;"
sqlite3 /home/workspace/Projects/PDFUSAEDIT-zo/data/pdfusa.db "SELECT COUNT(*) FROM serve_attempts;"
ls /home/workspace/Projects/PDFUSAEDIT-zo/data/uploads/serves/ | wc -l
```

## Step 4: Clean Up Old Backups (Optional but Recommended)

Keep only the 5 most recent backups locally. Delete older ones:

```bash
cd /home/workspace/Projects/PDFUSAEDIT-zo/backups
ls -t pdfusa-backup-*.zip | tail -n +6 | xargs rm -f
```

This keeps the newest 5 files and removes the rest.

## Troubleshooting

### Script says "command not found: bun"

Bun is installed on Zo Computer. The full path is `/root/.bun/bin/bun`. Try:
```bash
/root/.bun/bin/bun run /home/workspace/Skills/pdfusa-backup/scripts/backup.ts
```

### Script says "zip: command not found"

Install zip:
```bash
apt-get install -y zip
```
Then retry the script.

### Google Drive upload fails with "file not found"

The zip file doesn't exist at the path you provided. Run:
```bash
ls -la /home/workspace/Projects/PDFUSAEDIT-zo/backups/
```
Find the most recent zip file (sorted by date). Use that full path for the upload.

### Google Drive upload fails with authentication error

The Google Drive integration is disconnected. Tell the user to reconnect it at:
Settings > Integrations > Connections > Google Drive

### Zip file is 0 bytes or corrupted

The database may have been locked during zipping. The script handles this by checkpointing WAL, but if it still fails:

1. Stop the PDFUSAEDIT service first.
2. Run the backup script.
3. Restart the service with `update_user_service(service_id="svc_Ptj61cIlMbA")`.

### Need to Restore from a Backup

1. Download the backup zip from Google Drive.
2. Copy it to the Zo Computer: place it at `/tmp/pdfusa-restore.zip`
3. Run:
   ```bash
   cd /home/workspace/Projects/PDFUSAEDIT-zo
   unzip -o /tmp/pdfusa-restore.zip
   ```
   This overwrites `data/pdfusa.db` and `data/uploads/serves/` with the backed-up versions.
4. Restart the service: `update_user_service(service_id="svc_Ptj61cIlMbA")`

## Automation Context

This skill is run by a weekly automation every Sunday at 2:00 AM Central Time (America/Chicago).

- **Automation ID:** `f833baa7-189d-453b-8d59-01aabdb3f01f`
- **RRULE:** `FREQ=WEEKLY;BYDAY=SU;BYHOUR=2;BYMINUTE=0`
- **Timezone:** America/Chicago

When the automation runs, it receives these instructions:
1. Follow this skill file.
2. Run the backup script: `bun run /home/workspace/Skills/pdfusa-backup/scripts/backup.ts`
3. Extract the `ZIP_PATH` from the script's output.
4. Upload to Google Drive using `use_app_google_drive` with `tool_name="google_drive-upload-file"` and `parentId="13R1vx8m2HPr3m3F4GvMzYbN7WJ8qK5xL"`.
5. Confirm success.

## Quick Reference Card

| Item | Value |
|---|---|
| **App directory** | `/home/workspace/Projects/PDFUSAEDIT-zo` |
| **Database path** | `/home/workspace/Projects/PDFUSAEDIT-zo/data/pdfusa.db` |
| **Images directory** | `/home/workspace/Projects/PDFUSAEDIT-zo/data/uploads/serves/` |
| **Backup script** | `bun run /home/workspace/Skills/pdfusa-backup/scripts/backup.ts` |
| **Backup output dir** | `/home/workspace/Projects/PDFUSAEDIT-zo/backups/` |
| **Google Drive folder** | `PDFUSA-Backups` |
| **Google Drive folder ID** | `13R1vx8m2HPr3m3F4GvMzYbN7WJ8qK5xL` |
| **Google Drive upload tool** | `use_app_google_drive` |
| **Google Drive tool name** | `google_drive-upload-file` |
| **Service ID** | `svc_Ptj61cIlMbA` |
| **Max local backups** | 5 (delete oldest) |
