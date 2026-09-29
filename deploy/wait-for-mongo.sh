#!/usr/bin/env bash
# supervisord's default autorestart gives a program 3 fast failures before
# giving up (FATAL state, no more retries) — mongod (started by the same
# supervisord, same moment) takes a few seconds to accept connections, and
# ensure_indexes() (app/main.py, runs at import time) would fail instantly
# on every one of those first few attempts. Polling here first, then
# exec'ing uvicorn only once mongo actually answers, means uvicorn's own
# startup never races mongod at all — supervisord's retry counter never
# even enters the picture.
set -euo pipefail

for _ in $(seq 1 60); do
  if mongosh --quiet --eval "db.adminCommand('ping')" "mongodb://127.0.0.1:27017/sakshya" >/dev/null 2>&1; then
    exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
  fi
  sleep 1
done

echo "mongod did not become ready within 60s" >&2
exit 1
