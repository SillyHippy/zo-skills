---
name: disk-usage-report
description: Accurate disk usage for Zo hosts where df is inflated. Reports REAL walkable trees vs DF container view and opaque gap. Use for daily memory logs, disk alerts, "how much disk am I using", df lies, quota questions.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---

# Disk usage report (accurate)

On this Zo host, `df -h /` is a **9p container view**. It often shows ~140–160G used while walkable trees only sum ~60G. That gap is **opaque platform overhead**, not your files. Do **not** log DF alone as "Disk: 146G / 512G".

## Command

```bash
python3 /home/workspace/Skills/disk-usage-report/scripts/report_disk.py
# REAL 61.9G (workspace 13G) | DF 150G/512G (29.3%, gap 88G opaque)

python3 /home/workspace/Skills/disk-usage-report/scripts/report_disk.py --full
python3 /home/workspace/Skills/disk-usage-report/scripts/report_disk.py --json
```

## Daily memory log format

Put the **one-liner** in the Disk field:

```
Disk: REAL 61.2G (workspace 13G) | DF 154G/512G (31%, gap 93G opaque) | Modal platform 20.6G (not counted)
```

Never write only `Disk: 146G / 512G used (29%)` from `df -h /`. The DF number includes Modal platform overhead (Modal volumes, daemons, runtime) that does **not** count toward your Zo quota.

## Alerts

Weekly free-space check should still use DF avail as a crude capacity signal (when the container is actually full, DF avail drops), but always include the REAL line:

```bash
python3 /home/workspace/Skills/disk-usage-report/scripts/report_disk.py --full --alert-gb 15
# exit 2 if DF available <= 15G
```

## What counts as REAL

`du` of: `/home/workspace`, `/home/.z`, `/root`, `/usr`, `/var`, `/tmp`, `/opt`, `/swapfile`, `/__substrate`.

Do **not** `du` `/__modal/volumes` for quota — those mounts over-count shared platform content (see `Skills/modal-on-zo/`).

### Modal platform (excluded from REAL, shown separately)

Modal's cloud-side storage lives behind separate 9p mounts under `/__modal/volumes`, `/__modal/mounts`, `/__modal/.bin`, and the daemon at `/root/.modal`. These are **platform overhead, not user files** — they do not count toward your Zo quota. The reporter measures them explicitly so the `Modal platform` line tells you how much of the DF-vs-REAL gap is Modal, but they are excluded from REAL.

```
Modal platform (NOT counted toward quota): 20.6G
```

If the opaque gap grows much larger than the Modal platform figure, something else (caches, build artifacts, etc.) is generating transient disk pressure — that is the signal worth investigating.
