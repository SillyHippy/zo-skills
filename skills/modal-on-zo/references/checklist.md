# Modal session checklist (Zo)

## Start

- [ ] User explicitly wants Modal (not "run on VPS only")
- [ ] `python3 .../modal-on-zo/scripts/preflight.py` — all OK or user acknowledged warnings
- [ ] Active profile is user's account (`modal profile current`)
- [ ] Project path is under `/home/workspace/`

## During

- [ ] No `modal volume create` unless user needs cross-run persistence on Modal
- [ ] Volume names are user-prefixed and listed in `modal volume list`
- [ ] No scripts writing large data to `/__modal`, `/mnt/web_build`, `/mnt/zo-tools`
- [ ] Results copied to workspace when user needs files on Zo

## End

- [ ] `modal volume list` — only expected user volumes remain
- [ ] `modal volume delete -y <user-volume>` for scratch volumes user is done with
- [ ] Tell user what stayed on Modal cloud vs what is in workspace

## Never

- [ ] Delete platform volume IDs from modal.com dashboard to "free Zo disk"
- [ ] `rm -rf /__modal` or `/mnt/web_build`
- [ ] Claim Zo disk was freed without `df` showing change (stale mounts need support)