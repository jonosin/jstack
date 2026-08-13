#!/usr/bin/env bash
set -euo pipefail

skill_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
repo=$(pwd)
[[ -f "$repo/AGENTS.md" ]] || { echo "run verify_repair.sh from the build repository" >&2; exit 1; }
python=/usr/local/bin/python3
[[ -x "$python" ]] || { echo "Pillow-capable Python is required at $python" >&2; exit 1; }

for test in test_tileforge_structure.py test_replay.py test_tileforge_alpha.py test_tileforge_cardinal_seating.py test_tileforge_map.py test_tileforge_seams.py; do
  "$python" "$skill_dir/tests/$test"
done

out="$repo/docs/reference/tileforge-proof/package"
contract="$skill_dir/references/contracts/warm-cardinal-study-hall.json"
"$python" "$skill_dir/scripts/process_sheet.py" --contract "$contract" \
  --source surfaces="$repo/docs/reference/tileforge-proof/raw/surfaces-generated.png" \
  --source furniture="$repo/docs/reference/tileforge-proof/raw/furniture-generated.png" \
  --source objects="$repo/docs/reference/tileforge-proof/raw/objects-generated.png" \
  --outdir "$out" --tolerance 128
"$python" "$skill_dir/scripts/package_assets.py" --contract "$contract" --asset-dir "$out/assets" --outdir "$out"
"$python" "$skill_dir/scripts/validate_output.py" --contract "$contract" --outdir "$out"
node "$repo/experiments/tileforge-proof/export-map-schema.mjs"
"$python" "$skill_dir/scripts/validate_map.py" --asset-manifest "$out/metadata.json" --map "$repo/experiments/tileforge-proof/map.json"
"$python" "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" "$skill_dir"
bash "$HOME/jstack/skills/suite/scripts/skill-lint.sh" "$skill_dir"
"$python" "$HOME/jstack/skills/init/scripts/docs_index.py" lint --repo "$repo" --satellite-kind build
"$python" - "$skill_dir" "$repo" <<'PY'
import os
import sys
from pathlib import Path

canonical, repo = map(Path, sys.argv[1:])
for path in (
    repo / ".agents/skills/fopus-tileforge",
    repo / ".claude/skills/fopus-tileforge",
    Path.home() / ".codex/skills/fopus-tileforge",
    Path.home() / ".hermes/skills/suite/fopus-tileforge",
):
    assert path.is_symlink(), f"missing installed link: {path}"
    assert Path(os.readlink(path)).resolve() == canonical.resolve(), f"wrong installed link: {path}"
PY
echo TILEFORGE-REPAIR-PASS
