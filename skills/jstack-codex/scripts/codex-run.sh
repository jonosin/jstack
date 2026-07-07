#!/usr/bin/env bash
# codex-run.sh: canonical deterministic entrypoint for running GPT-5.5 via the
# OpenAI Codex CLI from any Claude session. Generalizes jstack-challenge's
# codex-advisor.sh to all lanes (advisor, review, implement, investigate).
#
# Subcommands:
#   probe                     CODEX_OK (exit 0) if codex installed AND authed,
#                             else CODEX_UNAVAILABLE (exit 1).
#   run <prompt_file> [opts]  run `codex exec` on the prompt, parse the JSONL
#                             stream, print ONLY the final agent message to
#                             stdout. Diagnostics -> stderr.
# Options for run:
#   --write           workspace-write sandbox (default: read-only)
#   --effort E        low|medium|high|xhigh   (default: medium)
#   --search          enable web search (-c tools.web_search=true)
#   --schema F        validate final answer against JSON schema F
#   --isolated        run in an empty temp dir (advisor mode: nothing to read,
#                     must reason from the briefing alone)
#   --timeout S       seconds (default: 900)
#   --out F           also write the final message to file F
#
# Exit codes: 0 ok | 2 usage | 3 codex unavailable | 124 timeout | other: codex failed.

set -uo pipefail

_authed() {
  local home="${CODEX_HOME:-$HOME/.codex}"
  local k1 k2
  k1=$(printf '%s' "${CODEX_API_KEY:-}" | tr -d '[:space:]')
  k2=$(printf '%s' "${OPENAI_API_KEY:-}" | tr -d '[:space:]')
  [ -n "$k1" ] || [ -n "$k2" ] || [ -f "$home/auth.json" ]
}
_available() { command -v codex >/dev/null 2>&1 && _authed; }
_with_timeout() {
  local secs="$1"; shift
  local to
  to=$(command -v gtimeout 2>/dev/null || command -v timeout 2>/dev/null || echo "")
  if [ -n "$to" ]; then "$to" "$secs" "$@"; else "$@"; fi
}

case "${1:-}" in
  probe)
    if _available; then echo CODEX_OK; exit 0; fi
    echo CODEX_UNAVAILABLE; exit 1
    ;;
  run)
    shift
    promptfile="${1:-}"; shift || true
    if [ -z "$promptfile" ] || [ ! -f "$promptfile" ]; then
      echo "usage: codex-run.sh run <prompt_file> [--write] [--effort E] [--search] [--schema F] [--isolated] [--timeout S] [--out F]" >&2
      exit 2
    fi
    sandbox="read-only"; effort="medium"; search=""; schema=""; isolated=""
    timeout_s=900; outfile=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --write)    sandbox="workspace-write" ;;
        --effort)   effort="$2"; shift ;;
        --search)   search="1" ;;
        --schema)   schema="$2"; shift ;;
        --isolated) isolated="1" ;;
        --timeout)  timeout_s="$2"; shift ;;
        --out)      outfile="$2"; shift ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
      esac
      shift
    done
    if ! _available; then echo "__CODEX_UNAVAILABLE__" >&2; exit 3; fi

    prompt=$(cat "$promptfile")
    tmperr=$(mktemp "${TMPDIR:-/tmp}/codex-run-err-XXXXXX")
    workdir=""
    args=( -s "$sandbox" -m gpt-5.5 --json --skip-git-repo-check
           -c "model_reasoning_effort=\"$effort\"" -c 'mcp_servers={}' )
    if [ -n "$isolated" ]; then
      workdir=$(mktemp -d "${TMPDIR:-/tmp}/codex-run-XXXXXX")
      args+=( -C "$workdir" )
    fi
    [ -n "$search" ] && args+=( -c 'tools.web_search=true' )
    [ -n "$schema" ] && args+=( --output-schema "$schema" )
    [ -n "$outfile" ] && args+=( --output-last-message "$outfile" )

    _with_timeout "$timeout_s" codex exec "$prompt" "${args[@]}" \
      < /dev/null 2>"$tmperr" \
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
    [ -n "$workdir" ] && rmdir "$workdir" 2>/dev/null || true
    if [ "$code" = "124" ]; then
      echo "[codex-run timed out after ${timeout_s}s]" >&2
    elif [ "$code" != "0" ] && grep -qiE "auth|login|unauthorized|forbidden" "$tmperr" 2>/dev/null; then
      echo "[codex-run auth error] $(head -1 "$tmperr")" >&2
    elif [ "$code" != "0" ]; then
      echo "[codex-run failed (exit $code)]" >&2
      head -3 "$tmperr" >&2 2>/dev/null || true
    fi
    rm -f "$tmperr" 2>/dev/null || true
    exit "$code"
    ;;
  *)
    echo "usage: codex-run.sh {probe | run <prompt_file> [options]}" >&2
    exit 2
    ;;
esac
