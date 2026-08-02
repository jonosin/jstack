#!/usr/bin/env python3
"""Contract checks for the deterministic GCP discovery preparation/normalization path."""
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "gcp_discovery.py"
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    markets = root / "markets.json"
    markets.write_text(json.dumps([{"market": "Sedona, Arizona"}, {"market": "Asheville, North Carolina"}, {"market": "Sonoma, California"}]))
    plan = root / "input.json"
    subprocess.run([sys.executable, str(SCRIPT), "prepare", "--markets", str(markets), "--output", str(plan)], check=True, capture_output=True, text=True)
    assert len(json.loads(plan.read_text())["queries"]) == 15
    raw = root / "raw.json"
    raw.write_text(json.dumps([
        {"query_id":"q001","market":"Sedona, Arizona","query":"hotel in Sedona, Arizona, USA","place":{"id":"abc","displayName":{"text":"Independent Lodge"},"websiteUri":"https://example.test","googleMapsUri":"https://maps.google.test/a","primaryType":"lodging","types":["lodging"],"businessStatus":"OPERATIONAL","userRatingCount":21}},
        {"query_id":"q002","market":"Sedona, Arizona","query":"resort in Sedona, Arizona, USA","place":{"id":"abc","displayName":{"text":"Independent Lodge"},"websiteUri":"https://example.test","googleMapsUri":"https://maps.google.test/a","primaryType":"lodging","types":["lodging"],"businessStatus":"OPERATIONAL","userRatingCount":21}},
        {"query_id":"q003","market":"Sedona, Arizona","query":"hotel in Sedona, Arizona, USA","place":{"id":"closed","displayName":{"text":"Closed Hotel"},"websiteUri":"https://closed.test","businessStatus":"CLOSED_PERMANENTLY"}}
    ]))
    out = root / "normalized"
    subprocess.run([sys.executable, str(SCRIPT), "normalize", "--input", str(raw), "--output-dir", str(out)], check=True, capture_output=True, text=True)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["raw_records"] == 3 and summary["deduped_records"] == 2
    assert summary["outcomes"]["retain_for_manual_qualification"] == 1
    assert summary["outcomes"]["excluded_closed"] == 1
print("PASS: GCP plan, source-preserving dedupe, and exclusion behavior verified")
