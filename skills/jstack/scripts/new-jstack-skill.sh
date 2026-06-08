#!/usr/bin/env bash
# new-jstack-skill.sh — create a jstack skill canonically in the jstack repo
# (skills/<name>) and symlink it into every harness installed on this machine:
# .agents (the hub), .claude, .codex, and the .hermes jstack/ package.
#
# The canonical location is the repo this script ships in, resolved from the
# script's own path — so it works wherever you cloned jstack.
#
# Usage:
#   new-jstack-skill.sh <skill-name> [--desc "one-line description"]
#   new-jstack-skill.sh jstack-foo --desc "Does the foo thing"
#
# Idempotent: re-running for an existing skill repairs missing symlinks without
# clobbering the canonical SKILL.md.

set -euo pipefail

# Resolve the repo root from this script's location:
# skills/jstack/scripts/new-jstack-skill.sh -> up 3 -> repo root.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SKILLS="$REPO_ROOT/skills"

AGENTS="$HOME/.agents/skills"
CLAUDE="$HOME/.claude/skills"
CODEX="$HOME/.codex/skills"
HERMES_PKG="$HOME/.hermes/skills/jstack"

name="${1:-}"
shift || true
desc=""
while [ $# -gt 0 ]; do
  case "$1" in
    --desc) desc="${2:-}"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$name" ]; then
  echo "usage: new-jstack-skill.sh <skill-name> [--desc \"...\"]" >&2
  exit 2
fi
case "$name" in
  jstack|jstack-*) : ;;
  *) echo "error: skill name must be 'jstack' or start with 'jstack-' (got: $name)" >&2; exit 2 ;;
esac

canon="$SKILLS/$name"

# 1. Canonical skill dir in the repo
if [ -e "$canon" ] && [ ! -d "$canon" ]; then
  echo "error: $canon exists and is not a directory" >&2
  exit 1
fi
mkdir -p "$canon"
if [ ! -f "$canon/SKILL.md" ]; then
  [ -z "$desc" ] && desc="TODO: one-line description with trigger phrases"
  cat > "$canon/SKILL.md" <<EOF
---
name: $name
description: "$desc"
---

# $name

TODO: write the skill body.
EOF
  echo "created canonical skill: $canon/SKILL.md"
else
  echo "canonical skill already exists: $canon/SKILL.md (leaving as-is)"
fi

# 2. Symlink into each harness that exists. Args: <skills-dir> <link-target-path>
link_into() {
  local dir="$1" target="$2" link="$1/$name"
  [ -d "$dir" ] || { echo "skip (no dir): $dir"; return 0; }
  if [ -L "$link" ]; then
    rm "$link"
  elif [ -e "$link" ]; then
    echo "warn: $link exists and is not a symlink, leaving untouched" >&2
    return 0
  fi
  ln -s "$target" "$link"
  echo "linked: $link -> $target"
}

# .agents is the hub: it points straight at the repo. The other harnesses point
# at .agents (transitive) when it exists, else straight at the repo so a machine
# without .agents still gets working links.
if [ -d "$AGENTS" ]; then
  link_into "$AGENTS" "$canon"
  link_into "$CLAUDE" "../../.agents/skills/$name"   # repo-relative, via the hub
  link_into "$CODEX"  "$AGENTS/$name"
  link_into "$HERMES_PKG" "$AGENTS/$name"
else
  link_into "$CLAUDE" "$canon"
  link_into "$CODEX"  "$canon"
  link_into "$HERMES_PKG" "$canon"
fi

echo "done: $name is canonical in the jstack repo and symlinked across harnesses."
