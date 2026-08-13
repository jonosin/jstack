#!/usr/bin/env bash
# codex-advisor.sh: run the jstack-challenge adversarial advisor as a background
# OpenAI Codex agent. Self-contained: no dependency on any other skill, so it
# travels with the public jstack repo.
#
# Subcommands:
#   probe              prints CODEX_OK (exit 0) when `codex` is installed AND
#                      authed; prints CODEX_UNAVAILABLE (exit 1) otherwise. This
#                      is the auto-pick gate the skill reads to choose an engine.
#   run <prompt_file>  runs `codex exec` read-only and single-shot against the
#                      prompt in <prompt_file>, parses the JSONL event stream,
#                      and prints ONLY the advisor's final message to stdout.
#                      Diagnostics and fallback markers go to stderr.
#
# The advisor is read-only, single-shot, attack-the-position: no writes, no web
# search, no research. It must reason purely from the briefing in the prompt,
# exactly like the Claude `Agent` path it stands in for.
#
# Exit codes for `run`:
#   0    advisor produced output
#   3    codex unavailable at run time (prints __CODEX_UNAVAILABLE__) -> caller
#        should fall back to the Claude path
#   124  codex timed out -> caller should fall back to the Claude path
#   other non-zero: codex failed (e.g. auth error) -> caller should fall back

set -uo pipefail  # no `set -e`: exits are handled explicitly below.

_advisor_authed() {
  # Multi-signal auth: env key (CI / platform users) OR the codex auth file.
  local home="${CODEX_HOME:-$HOME/.codex}"
  local k1 k2
  k1=$(printf '%s' "${CODEX_API_KEY:-}" | tr -d '[:space:]')
  k2=$(printf '%s' "${OPENAI_API_KEY:-}" | tr -d '[:space:]')
  [ -n "$k1" ] || [ -n "$k2" ] || [ -f "$home/auth.json" ]
}

_advisor_available() {
  command -v codex >/dev/null 2>&1 && _advisor_authed
}

_advisor_timeout() {
  # Prefer gtimeout (Homebrew coreutils on macOS), then timeout (Linux),
  # else run unwrapped. $1 = seconds; rest = command. Exit 124 = timed out.
  local secs="$1"; shift
  local to
  to=$(command -v gtimeout 2>/dev/null || command -v timeout 2>/dev/null || echo "")
  if [ -n "$to" ]; then "$to" "$secs" "$@"; else "$@"; fi
}

case "${1:-}" in
  probe)
    if _advisor_available; then echo CODEX_OK; exit 0; fi
    echo CODEX_UNAVAILABLE; exit 1
    ;;

  run)
    promptfile="${2:-}"
    if [ -z "$promptfile" ] || [ ! -f "$promptfile" ]; then
      echo "usage: codex-advisor.sh run <prompt_file>" >&2
      exit 2
    fi
    if ! _advisor_available; then
      echo "__CODEX_UNAVAILABLE__" >&2
      exit 3
    fi

    prompt=$(cat "$promptfile")
    # Isolated empty working dir: read-only sandbox + an empty dir + no web
    # search means the advisor has nothing to read and must attack from the
    # briefing alone. --skip-git-repo-check lets codex run outside a git repo.
    workdir=$(mktemp -d "${TMPDIR:-/tmp}/jstack-advisor-XXXXXX")
    tmperr=$(mktemp "${TMPDIR:-/tmp}/jstack-advisor-err-XXXXXX.txt")

    _advisor_timeout 600 codex exec "$prompt" \
      -C "$workdir" -s read-only --skip-git-repo-check \
      -c 'model_reasoning_effort="high"' --json < /dev/null 2>"$tmperr" \
    | PYTHONUNBUFFERED=1 python3 -u -c '
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        obj = json.loads(line)
    except Exception:
        continue
    if obj.get("type") == "item.completed":
        item = obj.get("item", {})
        if item.get("type") == "agent_message" and item.get("text"):
            print(item["text"], flush=True)
'
    code=${PIPESTATUS[0]}

    rmdir "$workdir" 2>/dev/null || true
    if [ "$code" = "124" ]; then
      echo "[codex advisor timed out after 600s -- fall back to the Claude advisor]" >&2
    elif [ "$code" != "0" ] && grep -qiE "auth|login|unauthorized|forbidden" "$tmperr" 2>/dev/null; then
      echo "[codex advisor auth error -- fall back to the Claude advisor] $(head -1 "$tmperr")" >&2
    elif [ "$code" != "0" ]; then
      echo "[codex advisor failed (exit $code) -- fall back to the Claude advisor]" >&2
      head -3 "$tmperr" >&2 2>/dev/null || true
    fi
    rm -f "$tmperr" 2>/dev/null || true
    exit "$code"
    ;;

  *)
    echo "usage: codex-advisor.sh {probe | run <prompt_file>}" >&2
    exit 2
    ;;
esac
