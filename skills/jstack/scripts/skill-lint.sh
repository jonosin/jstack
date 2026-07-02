#!/bin/bash
# skill-lint.sh <skill-dir> — deterministic hygiene gate for jstack skills.
# Checks are structural only; behavior/quality is the eval gate's job.
set -euo pipefail
d="${1:?usage: skill-lint.sh <skill-dir>}"
f="$d/SKILL.md"
fails=()
[ -f "$f" ] || { echo "LINT-FAIL: no SKILL.md in $d"; exit 1; }
# 1. Frontmatter: opening ---, name:, description:
head -1 "$f" | grep -qx -- '---' || fails+=("missing frontmatter opening ---")
awk '/^---$/{n++} n==1 && /^name:/{found=1} END{exit !found}' "$f" || fails+=("frontmatter missing name:")
awk '/^---$/{n++} n==1 && /^description:/{found=1} END{exit !found}' "$f" || fails+=("frontmatter missing description:")
# 2. Description states WHEN to trigger (must contain a trigger cue)
# description may be a YAML folded/literal block scalar (`description: >` or `|`)
# spanning multiple lines, so gather the full field before checking — not just
# the `description:` line itself, which misses the cue on continuation lines.
desc="$(awk '
  /^---$/ { n++; next }
  n==1 {
    if ($0 ~ /^description:/) { grab=1 }
    else if (grab && $0 ~ /^[A-Za-z_-]+:/) { grab=0 }
    if (grab) print
  }
' "$f")"
echo "$desc" | grep -qiE '(use when|invoke|trigger|when the user|when you)' || fails+=("description lacks a 'use when' trigger cue")
# 3. Next skills table present
grep -q '## Next skills' "$f" || fails+=("missing ## Next skills table")
# 4. No absolute personal paths
grep -qE '/Users/[a-z]' "$f" && fails+=("absolute /Users/ path in SKILL.md")
# 5. SKILL.md size budget (progressive disclosure)
[ "$(wc -l < "$f")" -le 500 ] || fails+=("SKILL.md over 500 lines — push detail into references/")
if [ "${#fails[@]}" -gt 0 ]; then
  printf 'LINT-FAIL %s\n' "$(basename "$d")"; printf ' - %s\n' "${fails[@]}"; exit 1
fi
echo "LINT-PASS $(basename "$d")"
