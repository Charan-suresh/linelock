#!/usr/bin/env bash
# Point the Vercel console at a gateway URL that is not the one-hour Pinggy link.
# Run from linelock/console after `vercel link`.
set -euo pipefail

if [[ $# -ne 1 || -z "$1" ]]; then
  echo "usage: point-vercel-gateway.sh <gateway-url>" >&2
  exit 1
fi

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root/console"
vercel env add GATEWAY_URL production --value "$1" --yes --force --no-sensitive
vercel deploy --prod --yes
echo "Production console: https://linelock-amber.vercel.app/health"
