---
name: google-drive-case-upload
description: Uploads case documents to the "Site Upload" folder in Google Drive. Creates a case-number subfolder and uploads files there.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---

# Google Drive Case Upload

Uploads PDFs or other case documents into the `Site Upload > FD-XXXX-XXXX` folder structure in Google Drive.

## How It Works

1. Uses `google_drive-find-folder` to locate the "Site Upload" folder
2. Creates a subfolder named with the case number (e.g., `FD-08-3695`)
3. Uploads the specified files into that subfolder

## Usage

The agent should:
1. Copy source files to `/tmp/` first
2. Use `google_drive-create-folder` with parentId of "Site Upload" (`1ZB7XTSC_eD6m3F-6_yI2VP065cKEQzVq`)
3. Use `google_drive-upload-file` with the new folder's parentId

## Key Folder IDs

- **Site Upload** (root): `1ZB7XTSC_eD6m3F-6_yI2VP065cKEQzVq`

## Steps

```bash
# 1. Copy files to /tmp
cp /home/workspace/path/to/file.pdf /tmp/FileName.pdf

# 2. Create case folder (use google_drive-create-folder)
# parentId: 1ZB7XTSC_eD6m3F-6_yI2VP065cKEQzVq
# name: FD-XX-XXXXX

# 3. Upload files (use google_drive-upload-file)
# parentId: <new folder ID from step 2>
# filePath: /tmp/FileName.pdf
# name: FileName.pdf
```
