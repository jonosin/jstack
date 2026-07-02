#!/usr/bin/env python3
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "fast_html.py"
EXAMPLE = ROOT / "references" / "example-doc.json"


def test_html_generation():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "doc.html"
        p = subprocess.run(["python3", str(SCRIPT), str(EXAMPLE), "--out", str(out)], capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        s = out.read_text()
        assert "Athar Follow-Up Close Package" in s
        assert "--accent:#9a7b4f" in s
        assert "<table>" in s
        assert "<article class='card third'>" in s


def test_default_slug_output():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "input.json"
        data = json.loads(EXAMPLE.read_text())
        data["title"] = "Fast HTML: Demo!"
        src.write_text(json.dumps(data))
        p = subprocess.run(["python3", str(SCRIPT), str(src)], cwd=td, capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        assert (Path(td) / "fast-html-demo.html").exists()

if __name__ == "__main__":
    test_html_generation(); test_default_slug_output(); print("ok")
