#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; SCRIPT = ROOT / "scripts" / "gcp_qualify.py"
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp); retained=root/"retained.json"; excluded=root/"excluded.json"
    retained.write_text(json.dumps([{"property":"A","website":"https://a.test"}]))
    excluded.write_text(json.dumps([{"property":"B","prefilter_rule":"chain_name_or_domain"}]))
    out=root/"out"
    subprocess.run([sys.executable, str(SCRIPT), "--retained", str(retained), "--excluded", str(excluded), "--output-dir", str(out)], check=True, capture_output=True, text=True)
    summary=json.loads((out/"summary.json").read_text())
    assert summary["qualified"] == 0 and summary["needs_review"] == 1 and summary["rejected"] == 1
print("PASS: GCP-only evidence is conservatively held for review")
