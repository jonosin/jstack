#!/usr/bin/env bash
set -euo pipefail

OPENCLI_ROOT="${OPENCLI_ROOT:-$HOME/builds/OpenCLI}"
LIMIT="100"
OUT=""
DELAY_MS="250"
DETAILS="true"
PRINT_COMMAND="false"

usage() {
  cat <<'USAGE'
Usage:
  salesnav-current-search.sh [--limit N] [--out FILE] [--delay-ms N] [--slim] [--print-command]

Runs the local OpenCLI Sales Navigator current-tab extractor:
  node ~/builds/OpenCLI/dist/src/main.js linkedin salesnav-current-search --limit N --delay-ms N -f json

Options:
  --limit N        Number of leads to extract. Default: 100.
  --out FILE       Write JSON to FILE. Default: stdout.
  --delay-ms N     Delay between profile enrichment calls. Default: 250.
  --slim           Skip per-profile enrichment.
  --print-command  Print the command as JSON without running it.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit)
      LIMIT="${2:?--limit requires a value}"
      shift 2
      ;;
    --out)
      OUT="${2:?--out requires a value}"
      shift 2
      ;;
    --delay-ms)
      DELAY_MS="${2:?--delay-ms requires a value}"
      shift 2
      ;;
    --slim)
      DETAILS="false"
      shift
      ;;
    --print-command)
      PRINT_COMMAND="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

OPENCLI_BIN="$OPENCLI_ROOT/dist/src/main.js"
if [[ ! -f "$OPENCLI_BIN" ]]; then
  echo "OpenCLI build not found at $OPENCLI_BIN. Run npm run build in $OPENCLI_ROOT." >&2
  exit 1
fi

export OPENCLI_CDP_ENDPOINT="${OPENCLI_CDP_ENDPOINT:-http://localhost:9222}"
export OPENCLI_CDP_TARGET="${OPENCLI_CDP_TARGET:-sales/search}"

if ! curl -sf "$OPENCLI_CDP_ENDPOINT/json/version" >/dev/null; then
  echo "OpenCLI CDP endpoint is not reachable at $OPENCLI_CDP_ENDPOINT." >&2
  echo "Run brave-cdp-relaunch, then retry. Browser Bridge is not required for this workflow." >&2
  exit 69
fi

CMD=(node "$OPENCLI_BIN" linkedin salesnav-current-search --limit "$LIMIT" --delay-ms "$DELAY_MS" --details "$DETAILS" -f json)

if [[ "$PRINT_COMMAND" == "true" ]]; then
  python3 - "$OUT" "${CMD[@]}" <<'PY'
import json, sys
out = sys.argv[1]
cmd = sys.argv[2:]
print(json.dumps({"cmd": cmd, "out": out or None}, indent=2))
PY
  exit 0
fi

if [[ -n "$OUT" ]]; then
  mkdir -p "$(dirname "$OUT")"
  "${CMD[@]}" > "$OUT"
  echo "$OUT"
else
  "${CMD[@]}"
fi
