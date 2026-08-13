#!/usr/bin/env bash
#
# Test for opencli-cdp.sh — verifies the wrapper enforces the CDP bypass (sets
# OPENCLI_CDP_ENDPOINT) and forwards args verbatim, without needing a live Brave session.
# Uses OPENCLI_CDP_DRYRUN=1 so no network preflight and no opencli execution occur.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
WRAP="$HERE/opencli-cdp.sh"
FIXTURE="$HERE/../references/dryrun-fixture.txt"

# A fake OPENCLI_DIR with a dist entrypoint so command resolution is deterministic
# (independent of whether a global opencli is installed on the host).
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/dist/src"
: > "$TMP/dist/src/main.js"

pass=0 fail=0
check() { # check <name> <expected-substring> <actual>
  if printf '%s' "$3" | grep -qF -- "$2"; then
    echo "ok   - $1"; pass=$((pass+1))
  else
    echo "FAIL - $1"; echo "       expected to contain: $2"; echo "       got: $3"; fail=$((fail+1))
  fi
}

# 1. Default endpoint is localhost:9222 and args forward verbatim.
out1="$(OPENCLI_DIR="$TMP" OPENCLI_CDP_DRYRUN=1 bash "$WRAP" linkedin salesnav-inbox --filter inmail-accepted --limit 5 -f json)"
check "default endpoint is localhost:9222"        "OPENCLI_CDP_ENDPOINT=http://localhost:9222" "$out1"
check "derived port is 9222"                      "CDP_PORT=9222"                               "$out1"
check "command uses the dist entrypoint"          "node $TMP/dist/src/main.js"                  "$out1"
check "args are forwarded verbatim"               "linkedin salesnav-inbox --filter inmail-accepted --limit 5 -f json" "$out1"

# 2. A custom endpoint is respected and its port is derived correctly.
out2="$(OPENCLI_DIR="$TMP" OPENCLI_CDP_ENDPOINT="http://localhost:9333" OPENCLI_CDP_DRYRUN=1 bash "$WRAP" list -f json)"
check "custom endpoint respected"                 "OPENCLI_CDP_ENDPOINT=http://localhost:9333" "$out2"
check "custom port derived"                        "CDP_PORT=9333"                              "$out2"

# 3. The default dry-run matches the committed fixture (behavior snapshot).
if [ -f "$FIXTURE" ]; then
  expected="$(sed "s#__OPENCLI_DIR__#$TMP#g" "$FIXTURE")"
  if [ "$out1" = "$expected" ]; then
    echo "ok   - dry-run output matches fixture"; pass=$((pass+1))
  else
    echo "FAIL - dry-run output matches fixture"; diff <(printf '%s\n' "$expected") <(printf '%s\n' "$out1") || true; fail=$((fail+1))
  fi
fi

# 4. Missing opencli (empty OPENCLI_DIR, PATH without a global opencli) exits 1 with guidance.
out4="$(OPENCLI_DIR="$TMP/nope" OPENCLI_CDP_DRYRUN=1 PATH="/usr/bin:/bin" bash "$WRAP" list 2>&1)" && rc4=0 || rc4=$?
check "missing opencli mentions build guidance"   "opencli not found"                          "$out4"
[ "${rc4:-0}" -eq 1 ] && { echo "ok   - missing opencli exits 1"; pass=$((pass+1)); } || { echo "FAIL - missing opencli exits 1 (got ${rc4:-0})"; fail=$((fail+1)); }

echo "-----"
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
