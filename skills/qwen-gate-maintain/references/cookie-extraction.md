# Extracting Qwen session cookies from qwen-gate's browser profiles

qwen-gate persists Qwen Web session cookies on disk in **Chromium browser profiles**. They are NOT locked inside the Playwright process — they're readable (after Chromium-encryption handling) from the SQLite `Cookies` file. This reference exists because a previous session twice wrongly claimed "cookies are not persisted / can't be extracted" — that was false and frustrated the user.

## Where the cookies live

```
/home/workspace/Projects/qwen-gate/.qwen/browser-profiles/<account_sanitized>/Default/Cookies
```

`<account_sanitized>` is the email with `@` and `.` replaced by `_` (e.g. `rawr88098809_gmail_com`, `rawr88098809_1_gmail_com`). There is one profile per account (6 accounts total on this VPS).

The `Cookies` file is a standard Chromium SQLite database. The relevant table is `cookies`. The cookie value is in the `encrypted_value` BLOB column (the `value` TEXT column is empty for non-host-only cookies). The `host_key` column is the domain (e.g. `.qwen.ai`).

## Required cookies for OmniRoute "Qwen Web (Free)"

OmniRoute's hint says `cna, ssxmod_itna, token`, but Qwen actually uses:
- `cna` — session anchor
- `token` — a JWT (`eyJ...`)
- `tfstk` — the session-continuity cookie (NOT `ssxmod_itna` — that's a different Alibaba property)

All three are stored under host `.qwen.ai` in the profile's `Cookies` DB.

## Decryption on Linux gVisor

Chromium encrypts cookie values with a key derived from `os_crypt` — on Linux this is either:
- **Default (no keyring):** a hardcoded passphrase `peanuts` run through PBKDF2 (SHA1, 1 iteration, salt `saltysalt`, 16 bytes) → AES-128-CBC, IV = 16 spaces (`0x20` × 16). The ciphertext has a `v10` or `v11` prefix.
- **With keyring:** the key is stored in the user's keyring. On a headless gVisor VPS there is no keyring, so the `peanuts` default applies.

Decryption recipe (Python 3, no external deps beyond `cryptography`):

```python
import sqlite3, sys
from cryptography.hurricane import ...  # see below; or use pyca/cryptography

# AES-128-CBC, key from PBKDF2
from hashlib import pbkdf2_hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

KEY = pbkdf2_hmac('sha1', b'peanuts', b'saltysalt', 1, dklen=16)
IV = b' ' * 16

def decrypt(blob: bytes) -> str:
    if blob[:3] in (b'v10', b'v11'):
        blob = blob[3:]
    dec = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend()).decryptor()
    plain = dec.update(blob) + dec.finalize()
    # PKCS7 unpad
    pad = plain[-1]
    return plain[:-pad].decode('utf-8', errors='replace')

def extract(profile_path: str) -> dict:
    con = sqlite3.connect(f"{profile_path}/Default/Cookies")
    rows = con.execute(
        "SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%qwen.ai'"
    ).fetchall()
    out = {}
    for host, name, ev in rows:
        if ev:
            out[name] = decrypt(ev)
    con.close()
    return out
```

If `cryptography` isn't installed: `pip install cryptography` (or use `pycryptodome` with the equivalent AES-CBC). The `peanuts` default is what applies on this VPS — verify by checking that `encrypted_value` starts with `v10` or `v11`.

## Formatting for OmniRoute bulk-add

OmniRoute's "Qwen Web (Free)" → Bulk Add tab expects `name|cookie-string`, one per line. Build the cookie string as `k1=v1; k2=v2; ...` for the required cookies only:

```python
cookies = extract(profile_path)
needed = ['cna', 'token', 'tfstk', 'isg', 'qwen-locale', 'qwen-theme', '_bl_uid']
# also include atpsida, sca, x-ap if present (accounts +3/+4/+5 have them)
parts = [f"{k}={cookies[k]}" for k in needed if k in cookies]
print(f"{email}|{'; '.join(parts)}")
```

Priority 1, click "Add All Keys". The 6 accounts on this VPS produce 6 lines.

## Expiry and refresh

- The `token` JWT has `exp` ~2 days out (check the JWT payload's `exp` claim).
- qwen-gate auto-refreshes cookies on disk whenever a session expires (Playwright re-login via the stored email/password `Crazy8809!`).
- If OmniRoute's imported cookies stop working, re-run the extraction — qwen-gate will have written fresh cookies to the same `Cookies` SQLite file.

## Alternative: skip "Qwen Web (Free)" entirely

Adding qwen-gate as a custom OpenAI-compatible node is strictly better for this VPS:
- Base URL: `http://localhost:26405/v1`
- API key: (blank — qwen-gate doesn't check)
- Prefix: `qg`
- Gives all 6 accounts with auto-rotation, auto-refresh, and WAF/baxia bypass already solved.

Use the manual cookie extraction only when the user specifically wants the cookies in OmniRoute's native "Qwen Web (Free)" provider (e.g. for a head-to-head comparison of the two providers' behavior).
