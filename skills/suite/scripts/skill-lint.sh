#!/bin/bash
# skill-lint.sh [--strict] <skill-dir> — deterministic hygiene gate for jstack skills.
# Checks are structural only; behavior/quality is the eval gate's job.
# --strict promotes the Gotchas-section warning to a failure (use on new skills).
set -euo pipefail

# --- flag parsing (kept minimal so it never breaks existing positional usage) ---
STRICT=0
args=()
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    -h|--help)
      echo "usage: skill-lint.sh [--strict] <skill-dir>"
      exit 0
      ;;
    *) args+=("$arg") ;;
  esac
done
set -- "${args[@]+"${args[@]}"}"

d="${1:?usage: skill-lint.sh [--strict] <skill-dir>}"
f="$d/SKILL.md"
fails=()
warns=()
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
# 6. Gotchas section (warn by default — most skills don't have one yet;
# --strict promotes this to a failure for use on newly authored skills).
grep -qE '^#+[[:space:]]*.*[Gg]otcha' "$f" || {
  if [ "$STRICT" -eq 1 ]; then
    fails+=("missing a Gotchas section (--strict)")
  else
    warns+=("missing a Gotchas section (add '## Gotchas' — warn-level, not required yet)")
  fi
}
# 7. Trigger-word collision: two different skills whose frontmatter description
# quotes the SAME trigger phrase route ambiguously — that's a real routing bug,
# so this is fail-level regardless of --strict. Compares this skill's quoted
# trigger phrases (text inside "...") against every sibling skill under the
# same skills/ root. Case-insensitive, exact-phrase match only, ignores
# trivial/empty quotes (<3 chars).
extract_desc() {
  awk '
    /^---$/ { n++; next }
    n==1 {
      if ($0 ~ /^description:/) { grab=1 }
      else if (grab && $0 ~ /^[A-Za-z_-]+:/) { grab=0 }
      if (grab) print
    }
  ' "$1"
}
extract_quotes() {
  grep -oE '"[^"]{3,}"' <<<"$1" | sed -E 's/^"//; s/"$//; s/^[[:space:]]+//; s/[[:space:]]+$//' | tr '[:upper:]' '[:lower:]' | sort -u
}
own_quotes="$(extract_quotes "$desc")" || true
if [ -n "$own_quotes" ]; then
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  skills_root="$(cd "$script_dir/../.." && pwd)"
  self_name="$(basename "$(cd "$d" && pwd)")"
  for sib in "$skills_root"/*/; do
    sib_name="$(basename "$sib")"
    [ "$sib_name" = "$self_name" ] && continue
    sib_f="$sib/SKILL.md"
    [ -f "$sib_f" ] || continue
    sib_quotes="$(extract_quotes "$(extract_desc "$sib_f")")" || true
    [ -z "$sib_quotes" ] && continue
    while IFS= read -r oq; do
      [ -z "$oq" ] && continue
      while IFS= read -r sq; do
        [ -z "$sq" ] && continue
        if [ "$oq" = "$sq" ]; then
          fails+=("trigger-phrase collision with $sib_name: \"$oq\"")
        fi
      done <<<"$sib_quotes"
    done <<<"$own_quotes"
  done
fi
if [ "${#warns[@]}" -gt 0 ]; then
  printf 'LINT-WARN %s\n' "$(basename "$d")"; printf ' - %s\n' "${warns[@]}"
fi
if [ "${#fails[@]}" -gt 0 ]; then
  printf 'LINT-FAIL %s\n' "$(basename "$d")"; printf ' - %s\n' "${fails[@]}"; exit 1
fi
echo "LINT-PASS $(basename "$d")"
