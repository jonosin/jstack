#!/usr/bin/env bash
# secrets-gate.sh — scan the jstack repo for credential patterns, generic
# machine paths, and (if configured) personal-identity patterns before
# pushing. Exits non-zero on a hit. Run it before every `git push` (the repo
# is shareable).
#
#   tools/secrets-gate.sh
#
# Resolves the repo from its own location, so it runs from anywhere. Scans
# tracked + untracked (non-ignored) files, so a brand-new skill is checked even
# before it is staged. config.env / local.md are gitignored and skipped.
#
# Personal patterns (names, handles, companies, brands, codenames, project
# ids) are NOT hardcoded here — this file is committed and shareable. They
# resolve env var -> ~/.jstack/config.env -> empty default, via
# SECRETS_GATE_PERSONAL_PATTERNS: multiple regexes joined by the delimiter
# `|||` (chosen because it can't appear inside a grep -E pattern by accident).
# See .env.example for the format.
#
# KNOWN LIMITATION (pre-existing, not introduced here): on at least one tested
# git build, `git grep -E` silently ignores `\b` word-boundary anchors (a
# non-error, zero-match no-op), while `-P` honors them correctly. This script
# keeps -E for parity with the prior committed version's behavior. Any \b-
# anchored pattern you add (personal or generic) may not fire under -E on
# your platform — verify with a spot test (inject a hit, confirm FAIL) before
# relying on it. Switching to -P would fix this but was left out of scope
# here: on this repo's current tree it flips several already-committed,
# non-secret \b-anchored personal-name mentions in skill docs to FAIL, which
# is a separate cleanup, not this task.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Generic patterns that must never appear in a shareable jstack repo. No
# personal identity here by design — see header.
patterns=(
  '\bsk-[A-Za-z0-9]{12}'              # anthropic-style API key
  'ghp_[A-Za-z0-9]{10}'               # github personal access token
  'gho_[A-Za-z0-9]{10}'               # github oauth token
  'AIza[A-Za-z0-9]{10}'               # google api key
  'tvly-[A-Za-z0-9]'                  # tavily key
  '/Users/[A-Za-z0-9][A-Za-z0-9_.-]*' # any macOS absolute home path (first char
                                       # after /Users/ must be alnum, so illustrative
                                       # "/Users/..." in prose doesn't false-positive)
)

# Resolve personal patterns: env var (even if explicitly empty) wins outright;
# otherwise fall back to ~/.jstack/config.env; otherwise empty (not configured).
if [ "${SECRETS_GATE_PERSONAL_PATTERNS+is_set}" = "is_set" ]; then
  personal_patterns="$SECRETS_GATE_PERSONAL_PATTERNS"
else
  personal_patterns=""
  config_file="$HOME/.jstack/config.env"
  if [ -f "$config_file" ]; then
    personal_patterns="$(sed -n 's/^SECRETS_GATE_PERSONAL_PATTERNS=//p' "$config_file" | tail -n1)"
  fi
fi

if [ -z "$personal_patterns" ]; then
  echo "SECRETS GATE: notice — SECRETS_GATE_PERSONAL_PATTERNS not configured; running generic checks only." >&2
else
  # Split on the ||| delimiter (bash substring ops; not a single-char IFS split).
  remaining="$personal_patterns"
  while [ -n "$remaining" ]; do
    if [[ "$remaining" == *'|||'* ]]; then
      chunk="${remaining%%'|||'*}"
      remaining="${remaining#*'|||'}"
    else
      chunk="$remaining"
      remaining=""
    fi
    [ -n "$chunk" ] && patterns+=("$chunk")
  done
fi

args=()
for p in "${patterns[@]}"; do args+=(-e "$p"); done

# -n line numbers, -I skip binary, -E extended regex (matches the original
# script's engine flag — see the KNOWN LIMITATION note below re: \b).
# Exclude this gate file: the generic /Users/ pattern above appears in this
# file as a regex literal and would otherwise self-match.
hits="$(git -C "$REPO_ROOT" grep -nIE --untracked "${args[@]}" -- . ':!tools/secrets-gate.sh' 2>/dev/null || true)"

if [ -n "$hits" ]; then
  echo "SECRETS GATE: FAIL — forbidden content found:" >&2
  echo "$hits" >&2
  echo >&2
  echo "Move personal values into ~/.jstack/config.env (gitignored) and genericize the file." >&2
  exit 1
fi

echo "SECRETS GATE: clean ($REPO_ROOT)"
