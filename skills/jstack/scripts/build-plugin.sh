#!/usr/bin/env bash
# jstack build-plugin — deterministically package the jstack skills into a .plugin.
#
# Usage:
#   build-plugin.sh [--out PATH] [--bump patch|minor|major] [--version X.Y.Z] [--print-only]
#
#   --out PATH       Output file (default: <repo>/dist/<plugin-name>.plugin)
#   --bump LEVEL     Bump manifest version (patch|minor|major) and write it back
#   --version X.Y.Z  Set manifest version explicitly and write it back
#   --print-only     Discover + validate + report, write nothing
#
# It auto-discovers every skills/<name>/ that has a SKILL.md (so new and updated
# skills are picked up with no edits here), validates each skill's frontmatter
# against the Cowork .plugin rules, scrubs non-shippable junk, and zips a plugin
# with stable file ordering. Manifest is read from <repo>/.claude-plugin/plugin.json.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"   # scripts -> jstack -> skills -> repo
MANIFEST="$REPO_ROOT/.claude-plugin/plugin.json"
SKILLS_SRC="$REPO_ROOT/skills"

OUT=""; BUMP=""; SETVER=""; PRINT_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --bump) BUMP="$2"; shift 2 ;;
    --version) SETVER="$2"; shift 2 ;;
    --print-only) PRINT_ONLY=1; shift ;;
    -h|--help) sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 64 ;;
  esac
done

[ -f "$MANIFEST" ] || { echo "ERROR: manifest not found at $MANIFEST" >&2; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 required" >&2; exit 1; }
command -v zip     >/dev/null || { echo "ERROR: zip required" >&2; exit 1; }

# --- resolve name + version (optionally bump, writing manifest back) ---------
read -r PNAME PVER < <(python3 - "$MANIFEST" "$BUMP" "$SETVER" <<'PY'
import json, re, sys
mp, bump, setver = sys.argv[1], sys.argv[2], sys.argv[3]
m = json.load(open(mp))
name = m["name"]; ver = m.get("version", "0.1.0")
if setver:
    if not re.fullmatch(r"\d+\.\d+\.\d+", setver): sys.exit("bad --version (want X.Y.Z)")
    ver = setver
elif bump:
    a, b, c = (int(x) for x in ver.split("."))
    if   bump == "patch": c += 1
    elif bump == "minor": b += 1; c = 0
    elif bump == "major": a += 1; b = c = 0
    else: sys.exit("bad --bump (want patch|minor|major)")
    ver = f"{a}.{b}.{c}"
if setver or bump:
    m["version"] = ver
    with open(mp, "w") as f:
        json.dump(m, f, indent=2); f.write("\n")
print(name, ver)
PY
)

echo "jstack build-plugin"
echo "----------------------------------------"
echo "repo:      $REPO_ROOT"
echo "plugin:    $PNAME v$PVER"

# --- stage ------------------------------------------------------------------
STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/.claude-plugin" "$STAGE/skills"
# write the (possibly bumped) manifest fresh so the zip matches the repo
python3 - "$MANIFEST" "$STAGE/.claude-plugin/plugin.json" <<'PY'
import json, sys
json.dump(json.load(open(sys.argv[1])), open(sys.argv[2], "w"), indent=2)
open(sys.argv[2], "a").write("\n")
PY

bundled=0; skipped=""
for d in "$SKILLS_SRC"/*/; do
  name="$(basename "$d")"
  if [ -f "$d/SKILL.md" ]; then
    cp -R "$d" "$STAGE/skills/$name"
    bundled=$((bundled + 1))
  else
    skipped="$skipped $name"
  fi
done

# --- scrub non-shippable junk (deterministic) -------------------------------
find "$STAGE" -type d \( -name '.git' -o -name '.venv' -o -name 'node_modules' -o -name '__pycache__' \) -prune -exec rm -rf {} + 2>/dev/null || true
find "$STAGE" \( -name '.DS_Store' -o -name '*.pyc' -o -name '*.orig' -o -name '*.bak' \) -delete 2>/dev/null || true
find "$STAGE" -type l -delete 2>/dev/null || true   # drop dangling symlinks

echo "skills:    $bundled bundled; skipped (no SKILL.md):${skipped:- none}"

# --- validate every skill's frontmatter against the .plugin rules -----------
python3 - "$STAGE/skills" <<'PY'
import os, re, sys
root = sys.argv[1]; reserved = ("claude", "anthropic"); errs = []
for name in sorted(os.listdir(root)):
    p = os.path.join(root, name, "SKILL.md")
    if not os.path.isfile(p): errs.append(f"{name}: missing SKILL.md"); continue
    t = open(p, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---", t, re.S)
    if not m: errs.append(f"{name}: no YAML frontmatter"); continue
    fm = m.group(1)
    nm = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
    nmv = nm.group(1) if nm else ""
    # description block: from 'description:' to next top-level key (or end)
    dm = re.search(r"^description:[ \t]*(.*?)(?=\n[A-Za-z0-9_-]+:|\Z)", fm, re.S | re.M)
    dv = dm.group(1) if dm else ""
    dv = re.sub(r"^[|>][+-]?\s*", "", dv).strip().strip('"').strip("'")  # strip scalar indicator/quotes
    if nmv != name: errs.append(f"{name}: name '{nmv}' != dir name")
    if not re.fullmatch(r"[a-z0-9-]+", nmv or ""): errs.append(f"{name}: name not kebab-case")
    if len(nmv) > 64: errs.append(f"{name}: name >64 chars")
    if any(w in nmv for w in reserved): errs.append(f"{name}: reserved word in name")
    if not dv: errs.append(f"{name}: empty description")
    if len(dv) > 1024: errs.append(f"{name}: description {len(dv)} >1024 chars")
    if "<" in dv or ">" in dv: errs.append(f"{name}: angle bracket in description")
if errs:
    print("FRONTMATTER ERRORS:", *("  " + e for e in errs), sep="\n"); sys.exit(1)
print("frontmatter: all valid")
PY

# --- output path ------------------------------------------------------------
[ -n "$OUT" ] || OUT="$REPO_ROOT/dist/$PNAME.plugin"

if [ "$PRINT_ONLY" = 1 ]; then
  echo "would write: $OUT"; exit 0
fi

mkdir -p "$(dirname "$OUT")"
# --- zip with stable file ordering (deterministic layout) -------------------
TMPZIP="$(mktemp -u).plugin"
( cd "$STAGE" && find . -type f | LC_ALL=C sort | sed 's#^\./##' | zip -qX "$TMPZIP" -@ )
mv -f "$TMPZIP" "$OUT" 2>/dev/null || { cp -f "$TMPZIP" "$OUT"; rm -f "$TMPZIP" 2>/dev/null || true; }

echo "----------------------------------------"
echo "built: $OUT ($(du -h "$OUT" | cut -f1), $bundled skills)"
