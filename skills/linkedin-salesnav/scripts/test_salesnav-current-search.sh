#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

mkdir -p "$TMP_ROOT/dist/src"
printf 'console.log("stub")\n' > "$TMP_ROOT/dist/src/main.js"

OUTPUT="$(OPENCLI_ROOT="$TMP_ROOT" "$SCRIPT_DIR/salesnav-current-search.sh" --limit 100 --delay-ms 0 --out /tmp/leads.json --print-command)"

python3 - "$OUTPUT" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
cmd = data["cmd"]
assert cmd[:3] == ["node", cmd[1], "linkedin"], cmd
assert cmd[1].endswith("/dist/src/main.js"), cmd
assert "salesnav-current-search" in cmd, cmd
assert "--limit" in cmd and cmd[cmd.index("--limit") + 1] == "100", cmd
assert "--delay-ms" in cmd and cmd[cmd.index("--delay-ms") + 1] == "0", cmd
assert "--details" in cmd and cmd[cmd.index("--details") + 1] == "true", cmd
assert data["out"] == "/tmp/leads.json", data
PY

SLIM="$(OPENCLI_ROOT="$TMP_ROOT" "$SCRIPT_DIR/salesnav-current-search.sh" --slim --print-command)"
python3 - "$SLIM" <<'PY'
import json, sys
cmd = json.loads(sys.argv[1])["cmd"]
assert "--details" in cmd and cmd[cmd.index("--details") + 1] == "false", cmd
PY
