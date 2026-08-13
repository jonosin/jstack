#!/bin/bash
# git-guardrails-hook.sh — Claude Code PreToolUse hook (matcher: Bash).
# Reads the tool call JSON on stdin; blocks destructive git commands.
# Adapted from mattpocock/skills git-guardrails. Exit 2 = block with message.
set -euo pipefail
cmd=$(jq -r '.tool_input.command // empty' 2>/dev/null || true)
[ -z "$cmd" ] && exit 0
block() { echo "git-guardrails: blocked destructive command ($1). Run it manually if truly intended." >&2; exit 2; }
echo "$cmd" | grep -qE 'git (push --force|push -f)( |$)'        && block "force push"
echo "$cmd" | grep -qE 'git reset --hard'                        && block "reset --hard"
echo "$cmd" | grep -qE 'git clean -[a-z]*f'                      && block "clean -f"
echo "$cmd" | grep -qE 'git branch -D'                           && block "branch -D"
echo "$cmd" | grep -qE 'git (checkout|restore) \.'               && block "checkout/restore ."
exit 0
