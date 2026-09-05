#!/usr/bin/env bash
# Idiot-proof OmniRoute update while living behind zo-reverse-proxy.
# ANY model can run this. Do not improvise.
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/local/bin:$PATH

OMNI_DIR="/home/workspace/Projects/omniroute"
PROXY_TS="/home/workspace/Projects/zo-reverse-proxy/proxy.ts"
SUPER_CONF="/etc/zo/supervisord-user.conf"
SUPER="supervisorctl -s http://127.0.0.1:29011"
STAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/workspace/Backups/omniroute-update-${STAMP}"
VERIFY="/home/workspace/Skills/omniroute-maintain/scripts/verify.sh"

echo "=== OmniRoute update-via-proxy ==="
echo "Backup dir: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# 0) Backup critical bits
cp -a "$OMNI_DIR/.env" "$BACKUP_DIR/omniroute.env"
cp -a "$PROXY_TS" "$BACKUP_DIR/proxy.ts"
cp -a "$SUPER_CONF" "$BACKUP_DIR/supervisord-user.conf"
sqlite3 /root/.omniroute/storage.sqlite "PRAGMA wal_checkpoint(TRUNCATE);" >/dev/null 2>&1 || true
cp -a /root/.omniroute/storage.sqlite "$BACKUP_DIR/storage.sqlite"
cp -a /root/.hermes/config.yaml "$BACKUP_DIR/hermes-config.yaml" 2>/dev/null || true

# 1) HARD PINS — never skip (function so we can re-pin after git ops)
apply_pins() {
python3 - <<'PY'
from pathlib import Path
import re

PUBLIC_BASE = "https://zo-reverse-proxy-sillyhippy.zocomputer.io/omniroute"

env = Path("/home/workspace/Projects/omniroute/.env")
text = env.read_text()

def pin_env(key: str, value: str) -> None:
    global text
    pat = rf"(?m)^{re.escape(key)}=.*$"
    if re.search(pat, text):
        text = re.sub(pat, f"{key}={value}", text)
    else:
        text += f"\n{key}={value}\n"

pin_env("OMNIROUTE_BASE_PATH", "/omniroute")
pin_env("NEXT_PUBLIC_BASE_URL", PUBLIC_BASE)
pin_env("AUTH_COOKIE_SECURE", "true")
pin_env("OMNIROUTE_MEMORY_MB", "4096")
env.write_text(text)
print(f"pinned .env OMNIROUTE_BASE_PATH=/omniroute")
print(f"pinned .env NEXT_PUBLIC_BASE_URL={PUBLIC_BASE}")
print("pinned .env AUTH_COOKIE_SECURE=true")

# Swarm admission pins — MUST survive /omni update (applied 2026-08-21).
# Factory defaults MAX_HEAVY=1 + tools>=64=heavy 503 every Hermes swarm.
ADMISSION = {
    "OMNIROUTE_CHAT_MAX_HEAVY_IN_FLIGHT": "24",
    "OMNIROUTE_CHAT_HEAVY_TOOL_COUNT": "256",
    "OMNIROUTE_CHAT_HEAVY_MESSAGE_COUNT": "400",
    "OMNIROUTE_CHAT_HEAVY_ESTIMATED_TOKENS": "131072",
    "OMNIROUTE_CHAT_LARGE_BODY_BYTES": "1048576",
    "RATE_LIMIT_MAX_WAIT_MS": "60000",
    "OMNIROUTE_MEMORY_MB": "4096",
}
server_env = Path("/root/.omniroute/server.env")
if server_env.exists():
    se = server_env.read_text().splitlines()
    seen = set()
    out = []
    for line in se:
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            out.append(line)
            continue
        k = line.split("=", 1)[0].strip()
        if k in ADMISSION:
            out.append(f"{k}={ADMISSION[k]}")
            seen.add(k)
        else:
            out.append(line)
    missing = [k for k in ADMISSION if k not in seen]
    if missing:
        if out and out[-1] != "":
            out.append("")
        out.append("# swarm admission pins — do not drop")
        for k in missing:
            out.append(f"{k}={ADMISSION[k]}")
    server_env.write_text("\n".join(out) + "\n")
    print("pinned server.env swarm admission")

conf = Path("/etc/zo/supervisord-user.conf")
t = conf.read_text()
def repl(m):
    block = m.group(0)
    # PRODUCTION ONLY behind reverse proxy. npm run dev + HMR websocket = stuck Login "Loading...".
    # run-standalone.mjs applies OMNIROUTE_MEMORY_MB → --max-old-space-size.
    # Bare server.js ignores the 4096 pin and the model catalog OOMs / 503s.
    block = re.sub(
        r"^command=.*$",
        "command=bash -c 'cd /home/workspace/Projects/omniroute/.build/next/standalone && exec node ../../../scripts/dev/run-standalone.mjs'",
        block,
        count=1,
        flags=re.M,
    )
    block = re.sub(
        r"^directory=.*$",
        "directory=/home/workspace/Projects/omniroute",
        block,
        count=1,
        flags=re.M,
    )
    block = re.sub(
        r"^environment=.*$",
        'environment=PORT="20128",HOST="0.0.0.0",HOSTNAME="0.0.0.0",OMNIROUTE_BASE_PATH="/omniroute",NODE_ENV="production",AUTH_COOKIE_SECURE="true",NEXT_PUBLIC_BASE_URL="https://zo-reverse-proxy-sillyhippy.zocomputer.io/omniroute",OMNIROUTE_CHAT_MAX_HEAVY_IN_FLIGHT="24",OMNIROUTE_CHAT_HEAVY_TOOL_COUNT="256",OMNIROUTE_CHAT_HEAVY_MESSAGE_COUNT="400",OMNIROUTE_CHAT_HEAVY_ESTIMATED_TOKENS="131072",OMNIROUTE_CHAT_LARGE_BODY_BYTES="1048576",RATE_LIMIT_MAX_WAIT_MS="60000",OMNIROUTE_MEMORY_MB="4096"',
        block,
        count=1,
        flags=re.M,
    )
    return block
nt, n = re.subn(r"\[program:omniroute\]\n(?:(?!\[program:).*\n)+", repl, t, count=1)
if n != 1:
    raise SystemExit(f"Could not pin supervisor omniroute env (n={n})")
conf.write_text(nt)
print("pinned supervisor: production + BASE_PATH + swarm admission MAX_HEAVY=12")

proxy = Path("/home/workspace/Projects/zo-reverse-proxy/proxy.ts")
pt = proxy.read_text()
if 'prefix: "/omniroute"' not in pt:
    raise SystemExit("proxy.ts missing /omniroute route — STOP and restore from skill")
if "preservePrefix: true" not in pt:
    raise SystemExit("proxy.ts missing preservePrefix — STOP")
# HTML rewrite breaks nothing critical now, but omniroute must stay excluded (has real basePath).
if 'route.prefix !== "/omniroute"' not in pt:
    print("WARN: proxy.ts should exclude /omniroute from HTML path rewrite")
print("proxy.ts route OK")
PY
}

apply_pins

# 2) Git upgrade — ENABLED BY DEFAULT (OMNIROUTE_GIT_PULL=1 unless explicitly 0).
#    Moves the deploy checkout to the LATEST upstream release branch (release/vX.Y.Z)
#    and preserves local uncommitted subpath patches: stash → pull → pop (re-pin).
git_upgrade() {
  cd "$OMNI_DIR"
  if [ "${OMNIROUTE_GIT_PULL:-1}" != "1" ]; then
    echo "git upgrade skipped (OMNIROUTE_GIT_PULL != 1)"
    return 0
  fi

  echo "=== git: fetching upstream (tags + release branches) ==="
  git fetch origin --tags --prune

  # Fast-forward to $1 (upstream ref); if the local branch diverged, reset to it
  # (old commits stay in reflog — nothing is destroyed silently).
  ff_or_reset() {
    if ! git merge --ff-only "$1"; then
      echo "WARN: fast-forward not possible (local branch diverged) — resetting to $1 (reflog preserves old commits)"
      git reset --hard "$1"
    fi
  }

  # Latest upstream release = highest-semver release/vX.Y.Z branch
  LATEST_RELEASE_BRANCH=$(git ls-remote --heads origin 'refs/heads/release/v*' \
    | grep -oE 'release/v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1 || true)
  if [ -z "$LATEST_RELEASE_BRANCH" ]; then
    CURRENT=$(git branch --show-current || true)
    if [ -n "$CURRENT" ] && git rev-parse --verify -q "origin/$CURRENT" >/dev/null; then
      echo "WARN: no upstream release/v* branch — fast-forwarding $CURRENT to origin/$CURRENT"
      ff_or_reset "origin/$CURRENT"
    else
      echo "WARN: no upstream release/v* branch — plain fast-forward pull on current branch"
      git pull --ff-only
    fi
    return 0
  fi
  echo "Latest upstream release branch: $LATEST_RELEASE_BRANCH"

  # Save + stash local uncommitted subpath patches (tracked + untracked)
  STASHED=0
  if [ -n "$(git status --porcelain)" ]; then
    STASHED=1
    echo "=== git: local uncommitted changes found — backing up patch + stashing ==="
    git diff > "$BACKUP_DIR/local-patches.diff" || true
    git stash push -u -m "omniroute-update-${STAMP}"
    echo "stashed (refs/stash) — patch backup: $BACKUP_DIR/local-patches.diff"
  fi

  CURRENT_BRANCH=$(git branch --show-current || true)
  if [ "$CURRENT_BRANCH" != "$LATEST_RELEASE_BRANCH" ]; then
    echo "=== git: upgrading ${CURRENT_BRANCH:-<detached>} → $LATEST_RELEASE_BRANCH ==="
    # -B: (re)create the release branch exactly at the upstream head (old commits stay in reflog)
    git checkout -B "$LATEST_RELEASE_BRANCH" "origin/$LATEST_RELEASE_BRANCH"
  else
    echo "=== git: already on $LATEST_RELEASE_BRANCH — fast-forwarding ==="
    ff_or_reset "origin/$LATEST_RELEASE_BRANCH"
  fi
  git branch --set-upstream-to="origin/$LATEST_RELEASE_BRANCH" "$LATEST_RELEASE_BRANCH" >/dev/null 2>&1 || true

  # Re-apply local patches (re-pin). On conflict keep the LOCAL patched version
  # (required for this proxy deployment) and leave the stash for manual merge.
  if [ "$STASHED" = "1" ]; then
    echo "=== git: re-applying stashed local patches ==="
    if git stash pop; then
      echo "local patches re-applied cleanly"
    else
      echo "WARN: stash pop did not apply cleanly — restoring LOCAL patched versions"
      # Merge conflicts (UU): take the local patched version, keep stash for manual merge
      CONFLICTED=$(git diff --name-only --diff-filter=U || true)
      if [ -n "$CONFLICTED" ]; then
        echo "      conflicted files (kept local version):"
        echo "$CONFLICTED" | sed 's/^/        /'
        git checkout --theirs -- . || true
      fi
      # Untracked files that upstream now tracks live in the stash's untracked commit (^3)
      git checkout "stash@{0}^3" -- . 2>/dev/null || true
      git add -A || true
      echo "WARN: stash kept as refs/stash (stash@{0}) — resolve manually later if needed"
    fi
  fi

  echo "=== git: now on $(git branch --show-current) @ $(git rev-parse --short HEAD) ==="
  git log --oneline -3 | sed 's/^/    /'
}

git_upgrade

# 2b) Re-pin after git ops (pull/checkout can change tracked files — pins must survive)
apply_pins

# 3) Install if package files changed (safe)
cd "$OMNI_DIR"
if [ "${OMNIROUTE_NPM_INSTALL:-0}" = "1" ]; then
  npm install
fi

# 4) Production rebuild — keep OmniRoute RUNNING until build succeeds (stopping first
#    left the site down when build failed or was interrupted mid-way).
build_in_flight() {
  pgrep -f 'build-next-isolated.mjs' >/dev/null 2>&1 \
    || pgrep -f 'next build --turbopack' >/dev/null 2>&1 \
    || pgrep -f 'next build --webpack' >/dev/null 2>&1 \
    || pgrep -f '[n]ext build' >/dev/null 2>&1
}

wait_for_build_lock() {
  local i=0
  while build_in_flight; do
    i=$((i + 1))
    echo "waiting for in-flight production build (${i}) — will NOT start a second one"
    sleep 30
    if [ "$i" -ge 40 ]; then
      echo "FATAL: another build still running after 20m — stop it or wait, then retry"
      exit 1
    fi
  done
}

ram_abort_watch() {
  local target_pid="$1"
  while kill -0 "$target_pid" 2>/dev/null; do
    local avail
    avail=$(awk '/MemAvailable:/{print int($2/1024)}' /proc/meminfo)
    if [ -n "$avail" ] && [ "$avail" -lt 1500 ]; then
      echo "FATAL: available RAM ${avail}MB < 1500 — killing build pid $target_pid to protect the VPS"
      kill -TERM "$target_pid" 2>/dev/null || true
      sleep 2
      kill -KILL "$target_pid" 2>/dev/null || true
      exit 1
    fi
    sleep 15
  done
}

run_production_build() {
  export OMNIROUTE_BASE_PATH=/omniroute
  export NEXT_PUBLIC_BASE_URL=https://zo-reverse-proxy-sillyhippy.zocomputer.io/omniroute
  export AUTH_COOKIE_SECURE=true
  export PORT=20128
  export HOST=0.0.0.0
  # Turbopack native RAM hit 14GB here (2026-08-30) and never finished.
  # Webpack + 10GB V8 heap is the production path on this 32GB box.
  export OMNIROUTE_USE_TURBOPACK=0
  export OMNIROUTE_BUILD_MEMORY_MB=10240
  export NODE_OPTIONS="--max-old-space-size=10240"
  wait_for_build_lock
  rm -f "$OMNI_DIR/.build/next/lock" 2>/dev/null || true
  npm run build &
  local build_pid=$!
  ram_abort_watch "$build_pid" &
  local watch_pid=$!
  wait "$build_pid"
  local rc=$?
  kill "$watch_pid" 2>/dev/null || true
  wait "$watch_pid" 2>/dev/null || true
  return "$rc"
}

echo "=== production webpack build (OMNIROUTE_USE_TURBOPACK=0, heap 10GB) ==="
# Runtime stays OMNIROUTE_MEMORY_MB=4096. Do not stop OmniRoute until BUILD_ID exists.
export NODE_OPTIONS="--max-old-space-size=10240"
free_mb=$(free -m | awk '/^Mem:/{print $7}')
if [ "$free_mb" -lt 4000 ]; then
  echo "FATAL: Available RAM ($free_mb MB) < 4000 — not starting a production build"
  exit 1
fi

if ! run_production_build; then
  echo "WARN: first build failed — retrying once after 10s..."
  sleep 10
  run_production_build
fi
if [ ! -f "$OMNI_DIR/.build/next/BUILD_ID" ] \
   || [ ! -f "$OMNI_DIR/.build/next/standalone/server.js" ]; then
  echo "FATAL: build finished but standalone missing — OmniRoute left on previous build if still running"
  echo "Backup at $BACKUP_DIR"
  exit 1
fi
echo "build OK"

# 5) Restart app then proxy (order matters) — brief downtime only after good build
$SUPER reread || true
$SUPER update || true
$SUPER restart omniroute
sleep 8
$SUPER restart zo-reverse-proxy
sleep 5

# 6) Wait for API
ok=0
for i in $(seq 1 40); do
  code=$(curl -s -o /dev/null -m 10 -w "%{http_code}" http://127.0.0.1:20128/omniroute/v1/models || echo 000)
  echo "boot try $i → $code"
  if [ "$code" = "200" ] || [ "$code" = "401" ]; then ok=1; break; fi
  sleep 3
done
if [ "$ok" != "1" ]; then
  echo "FATAL: OmniRoute API never came up under /omniroute/v1"
  echo "Backup at $BACKUP_DIR"
  exit 1
fi

# 7) Verify (includes browser login hydrate check)
bash "$VERIFY"
rc=$?

# 7) Hermes URL sanity (do not rewrite whole config here)
if ! grep -q 'http://127.0.0.1:20128/omniroute/v1' /root/.hermes/config.yaml; then
  echo "WARN: Hermes still missing localhost+basePath URL — fix providers.omniroute / venice"
  rc=$((rc+1))
fi

echo "Backup: $BACKUP_DIR"
exit $rc
