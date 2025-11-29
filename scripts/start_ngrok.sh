#!/usr/bin/env bash
# Simple helper to start ngrok for local development and update .env BASE_URL
set -euo pipefail

# Usage: start_ngrok.sh [--yes]
# If --yes is passed, the script will automatically update .env without prompting.
AUTO_YES=0
if [ "${1-}" = "--yes" ] || [ "${1-}" = "-y" ]; then
  AUTO_YES=1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
NGROK_BIN="$(command -v ngrok || true)"

if [ -z "$NGROK_BIN" ]; then
  echo "ngrok binary not found in PATH." >&2
  echo "Download from https://ngrok.com/download and put it in your PATH." >&2
  exit 2
fi

if [ ! -f "$ENV_FILE" ]; then
  echo ".env file not found at $ENV_FILE" >&2
  exit 3
fi

if [ -n "${NGROK_AUTH_TOKEN-}" ]; then
  echo "Setting ngrok authtoken from NGROK_AUTH_TOKEN env var"
  "$NGROK_BIN" authtoken "$NGROK_AUTH_TOKEN" >/dev/null 2>&1 || true
fi

echo "Starting ngrok (http -> 8020)..."
"$NGROK_BIN" http 8020 --log=stdout >/tmp/ngrok.log 2>&1 &
NGROK_PID=$!

echo "ngrok PID: $NGROK_PID"
echo "Waiting for tunnel to become available..."

for i in {1..30}; do
  sleep 1
  if curl --silent --fail http://127.0.0.1:4040/api/tunnels >/dev/null 2>&1; then
    break
  fi
done

TUNNELS_JSON=$(curl --silent http://127.0.0.1:4040/api/tunnels)
PUBLIC_HTTPS=$(printf '%s' "$TUNNELS_JSON" | python3 - <<'PY'
import sys, json
data = json.load(sys.stdin)
for t in data.get('tunnels', []):
    if t.get('proto') == 'https' or t.get('public_url','').startswith('https'):
        print(t.get('public_url'))
        sys.exit(0)
sys.exit(1)
PY
)

if [ -z "$PUBLIC_HTTPS" ]; then
  echo "Failed to find public https URL from ngrok. See /tmp/ngrok.log" >&2
  exit 4
fi

echo "Public HTTPS URL: $PUBLIC_HTTPS"

if [ "$AUTO_YES" -eq 1 ]; then
  yn='y'
else
  read -p "Update BASE_URL in $ENV_FILE to '$PUBLIC_HTTPS' now? [y/N]: " yn
fi
case "$yn" in
  [Yy]*)
    cp "$ENV_FILE" "$ENV_FILE.bak"
    if grep -q '^BASE_URL=' "$ENV_FILE"; then
      sed -i "s|^BASE_URL=.*|BASE_URL=$PUBLIC_HTTPS|" "$ENV_FILE"
    else
      echo "BASE_URL=$PUBLIC_HTTPS" >> "$ENV_FILE"
    fi
    echo "Updated $ENV_FILE (backup at $ENV_FILE.bak)"
    ;;
  *)
    echo "Skipping .env update. Remember to set BASE_URL=$PUBLIC_HTTPS"
    ;;
esac

echo "Done. ngrok running. To stop: kill $NGROK_PID" 
echo "ngrok logs: /tmp/ngrok.log"

exit 0
