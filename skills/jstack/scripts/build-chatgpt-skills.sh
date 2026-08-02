#!/usr/bin/env bash
# Build portable Agent Skills for ChatGPT upload.
#
# Produces four individually uploadable ZIPs plus a convenience bundle:
#   jstack-grilling.zip, jstack-focus.zip, jstack-voice.zip, jstack-handoff.zip
#
# Usage: build-chatgpt-skills.sh [--out DIR]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
OUT="$REPO_ROOT/dist/chatgpt-skills"

if [ "${1:-}" = "--out" ]; then
  [ $# -eq 2 ] || { echo "usage: $0 [--out DIR]" >&2; exit 64; }
  OUT="$2"
elif [ $# -ne 0 ]; then
  echo "usage: $0 [--out DIR]" >&2; exit 64
fi

command -v python3 >/dev/null || { echo "ERROR: python3 required" >&2; exit 1; }
command -v zip >/dev/null || { echo "ERROR: zip required" >&2; exit 1; }

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE" "$OUT"

copy_skill() {
  local source="$1" target="$2"
  cp -R "$REPO_ROOT/skills/$source" "$STAGE/$target"
  find "$STAGE/$target" -name '.DS_Store' -delete
}

copy_skill jstack-grilling jstack-grilling
copy_skill jstack-focus jstack-focus
copy_skill jstack-handoff jstack-handoff
copy_skill jstack-myvoice jstack-voice

# The canonical implementation is jstack-myvoice; publish the requested portable alias.
python3 - "$STAGE/jstack-voice/SKILL.md" <<'PY'
from pathlib import Path
p = Path(__import__('sys').argv[1])
t = p.read_text()
t = t.replace('name: jstack-myvoice', 'name: jstack-voice', 1)
t = t.replace('# jstack-myvoice: voice router', '# jstack-voice: voice router', 1)
p.write_text(t)
PY

cat > "$STAGE/README.md" <<'EOF'
# JStack skills for ChatGPT

Each ZIP in this folder is one portable Agent Skill. In ChatGPT, open **Plugins** → **Skills** →
**Create** → **Upload**, then upload the skill ZIP you want. Install all four for the complete set.

`jstack-voice` is the portable ChatGPT name for the canonical `jstack-myvoice` skill.
`jstack-handoff` returns a copy-ready Markdown handoff when ChatGPT cannot create local files.
EOF

for skill in jstack-grilling jstack-focus jstack-voice jstack-handoff; do
  rm -f "$OUT/$skill.zip"
  (cd "$STAGE" && find "$skill" -type f | LC_ALL=C sort | zip -qX "$OUT/$skill.zip" -@)
done

rm -f "$OUT/jstack-chatgpt-skills.zip"
(cd "$OUT" && find README.md jstack-grilling.zip jstack-focus.zip jstack-voice.zip jstack-handoff.zip -type f 2>/dev/null | LC_ALL=C sort | zip -qX jstack-chatgpt-skills.zip -@) || true
cp "$STAGE/README.md" "$OUT/README.md"
# Rebuild the bundle after README exists.
rm -f "$OUT/jstack-chatgpt-skills.zip"
(cd "$OUT" && printf '%s\n' README.md jstack-grilling.zip jstack-focus.zip jstack-voice.zip jstack-handoff.zip | zip -qX jstack-chatgpt-skills.zip -@)

echo "Built ChatGPT upload artifacts in: $OUT"
