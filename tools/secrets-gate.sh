#!/usr/bin/env bash
# secrets-gate.sh — scan the jstack repo for personal identity, machine paths,
# GCP project ids, and credential patterns before pushing. Exits non-zero on a
# hit. Run it before every `git push` (the repo is shareable).
#
#   tools/secrets-gate.sh
#
# Resolves the repo from its own location, so it runs from anywhere. Scans
# tracked + untracked (non-ignored) files, so a brand-new skill is checked even
# before it is staged. config.env / local.md are gitignored and skipped.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Patterns that must never appear in a shareable jstack repo.
patterns=(
  'project-a4713060'                 # GCP project id
  '/Users/thanadolsinthubodee'       # machine home path
  '\bJono\b'                         # persona name
  'Thanadol'                         # legal name
  'xxgaming'                         # personal handle / email local-part
  '\bFacet\b'                        # company
  'PeptIQ'                           # brand
  '[Ee]stell'                        # project codename
  '[Dd]onna'                         # project codename
  '\bsk-[A-Za-z0-9]{12}'             # anthropic-style API key
  'ghp_[A-Za-z0-9]{10}'              # github personal access token
  'gho_[A-Za-z0-9]{10}'              # github oauth token
  'AIza[A-Za-z0-9]{10}'              # google api key
  'tvly-[A-Za-z0-9]'                 # tavily key
)

args=()
for p in "${patterns[@]}"; do args+=(-e "$p"); done

# -n line numbers, -I skip binary, -E extended regex. Exclude this gate file
# (it necessarily contains the patterns it searches for).
hits="$(git -C "$REPO_ROOT" grep -nIE --untracked "${args[@]}" -- . ':!tools/secrets-gate.sh' 2>/dev/null || true)"

if [ -n "$hits" ]; then
  echo "SECRETS GATE: FAIL — forbidden content found:" >&2
  echo "$hits" >&2
  echo >&2
  echo "Move personal values into ~/.jstack/config.env (gitignored) and genericize the file." >&2
  exit 1
fi

echo "SECRETS GATE: clean ($REPO_ROOT)"
