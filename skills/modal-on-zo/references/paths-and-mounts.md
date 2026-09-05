# Paths and mounts (Modal on Zo)

## Safe (user disk)

- `/home/workspace/` — primary project and export location
- `/home/workspace/Projects/modal-exports/` — recommended default for pulled artifacts
- `/home/workspace/Documents/modal-safe-usage.md` — user doc

## Platform (do not delete from inside Zo)

| Guest path | Typical size | Notes |
|------------|--------------|--------|
| `/__modal/volumes/vo-hUAIGF3JyIfa2OZaTGr6op` | ~37 GB | Stale; maps to `/mnt/web_build` |
| `/__modal/volumes/vo-YZGBuOFIMj36ysFJx7jnlI` | ~1.5 GB | Stale; maps to `/mnt/zo-tools` |
| `/run/modal_daemon` | small | 9p socket to host |

Filesystem: `9p`, often read-only for guest `rm`. `umount` denied from container.

## Modal CLI (cloud)

- `modal volume list` — user's Modal workspace volumes (empty after dashboard delete is OK)
- `modal volume delete -y NAME` — only for names user created
- `modal volume rm VOLUME path` — delete files inside a live Modal volume, not host stale mount

## Support

If `df` shows ~39G under `/__modal/volumes` after Modal dashboard cleanup:

- Use `Documents/Zo-support-ticket-modal-volumes.md`
- help@zocomputer.com / https://support.zocomputer.com

Using Modal again with this skill does **not** replace that one-time host cleanup.