#!/usr/bin/env bash
# STUB of jstack-challenge/scripts/codex-advisor.sh for skilltune evals.
# Same CLI contract as the real script, but behaviour is forced by $STUB_MODE so
# every scenario (codex ok / unavailable / empty / timeout / auth-error) is
# deterministic. Every invocation is appended to $ACTIONS_LOG as a TSV line so the
# Python grader can verify the probe->run->fallback protocol from ground truth.
#
#   STUB_MODE = ok | unavailable | empty | timeout | autherror | runerror
#   ACTIONS_LOG = path to the append-only action log (required)
set -uo pipefail
log() { printf '%s\t%s\n' "$1" "${2:-}" >> "${ACTIONS_LOG:-/dev/null}"; }

mode="${STUB_MODE:-ok}"
case "${1:-}" in
  probe)
    log "probe" "$mode"
    if [ "$mode" = "unavailable" ]; then echo CODEX_UNAVAILABLE; exit 1; fi
    echo CODEX_OK; exit 0
    ;;
  run)
    pf="${2:-}"
    log "run" "$pf"
    if [ -z "$pf" ] || [ ! -f "$pf" ]; then echo "usage: run <prompt_file>" >&2; exit 2; fi
    case "$mode" in
      unavailable) echo "__CODEX_UNAVAILABLE__" >&2; exit 3 ;;
      empty)       exit 0 ;;                                   # exit 0 but no stdout -> caller must fall back
      timeout)     echo "[codex advisor timed out after 600s -- fall back]" >&2; exit 124 ;;
      autherror)   echo "[codex advisor auth error -- fall back] unauthorized" >&2; exit 1 ;;
      runerror)    echo "[codex advisor failed (exit 9) -- fall back]" >&2; exit 9 ;;
      ok|*)        echo "VERDICT: This doesn't survive contact with a paying customer. The warm-intro moat is a one-shot asset, not a compounding one. [stub advisor output]"; exit 0 ;;
    esac
    ;;
  *) echo "usage: codex-advisor-stub.sh {probe | run <prompt_file>}" >&2; exit 2 ;;
esac
