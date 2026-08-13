#!/usr/bin/env bash
#
# opencli-cdp.sh — run OpenCLI against a logged-in Brave session over CDP (no extension).
#
# This is the ENFORCED default for opencli: it sets OPENCLI_CDP_ENDPOINT so OpenCLI's
# getBrowserFactory() (src/runtime.ts) selects the CDPBridge instead of the Browser Bridge
# extension, then runs the command verbatim. Every arg after the script name is passed straight
# through to opencli.
#
# Usage:
#   opencli-cdp.sh <site> <command> [args...] [-f json]
#   opencli-cdp.sh linkedin salesnav-inbox --filter inmail-accepted --limit 5 -f json
#   opencli-cdp.sh list -f json                      # discover all registered commands
#
# Env overrides:
#   OPENCLI_CDP_ENDPOINT   CDP endpoint (default: http://localhost:9222)
#   OPENCLI_CDP_TARGET     optional: pin a specific tab by title/url substring
#   OPENCLI_DIR            OpenCLI repo root (default: $HOME/builds/OpenCLI)
#   OPENCLI_CDP_DRYRUN=1   print the resolved endpoint + command and exit 0 (no preflight, no run)
#
# Exit codes: 1 = opencli not found · 69 = no CDP browser on the port · else = opencli's own code.

set -euo pipefail

OPENCLI_DIR="${OPENCLI_DIR:-$HOME/builds/OpenCLI}"
CDP_ENDPOINT="${OPENCLI_CDP_ENDPOINT:-http://localhost:9222}"

# Derive the TCP port from the endpoint for the preflight check (default 9222).
CDP_PORT="$(printf '%s' "$CDP_ENDPOINT" | sed -E 's#^[a-zA-Z]+://[^:/]+:([0-9]+).*#\1#')"
case "$CDP_PORT" in
  ''|*[!0-9]*) CDP_PORT=9222 ;;
esac

# Resolve the opencli entrypoint: prefer the source build, fall back to the global bin.
if [ -f "$OPENCLI_DIR/dist/src/main.js" ]; then
  OPENCLI_CMD=(node "$OPENCLI_DIR/dist/src/main.js")
elif command -v opencli >/dev/null 2>&1; then
  OPENCLI_CMD=(opencli)
else
  echo "opencli not found. Build it (cd $OPENCLI_DIR && npm run build) or 'npm i -g @jackwener/opencli'." >&2
  exit 1
fi

if [ "${OPENCLI_CDP_DRYRUN:-}" = "1" ]; then
  echo "OPENCLI_CDP_ENDPOINT=$CDP_ENDPOINT"
  echo "CDP_PORT=$CDP_PORT"
  echo "CMD=${OPENCLI_CMD[*]} $*"
  exit 0
fi

# Preflight: confirm a CDP-enabled Chromium (Brave) is actually listening. opencli doctor only
# checks the extension path, so curl /json/version is the reliable CDP check.
if ! curl -fsS "http://localhost:${CDP_PORT}/json/version" >/dev/null 2>&1; then
  echo "No CDP browser on port ${CDP_PORT}. Launch Brave with:" >&2
  echo "  --remote-debugging-port=${CDP_PORT} --remote-allow-origins=\"*\"" >&2
  echo "(jono harness: use the brave-cdp skill / brave-cdp-relaunch.)" >&2
  exit 69
fi

export OPENCLI_CDP_ENDPOINT="$CDP_ENDPOINT"
exec "${OPENCLI_CMD[@]}" "$@"
