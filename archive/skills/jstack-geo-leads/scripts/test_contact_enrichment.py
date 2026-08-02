#!/usr/bin/env python3
"""Behavior checks for parameterized contact enrichment preparation and merge gates."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "contact_enrichment.py"
REF = ROOT / "references" / "contact-fixtures"
SCHEMA = ROOT / "references" / "contact-result-schema.json"


def run(*args: str, succeeds: bool = True) -> subprocess.CompletedProcess:
    completed = subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True)
    if succeeds and completed.returncode:
        raise AssertionError(completed.stderr)
    if not succeeds and not completed.returncode:
        raise AssertionError("expected command failure")
    return completed


with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    inputs = root / "inputs"
    run("prepare", "--input", str(REF / "prospects.json"), "--output-dir", str(inputs), "--shard-count", "3")
    prepared = json.loads((inputs / "prepare-summary.json").read_text())
    assert prepared == {
        "input": str(REF / "prospects.json"), "prospect_count": 5,
        "requested_shard_count": 3, "actual_shard_count": 3,
        "shard_sizes": [2, 2, 1], "coverage_complete": True,
    }
    assert [path.name for path in sorted(inputs.glob("shard-*-input.json"))] == ["shard-01-input.json", "shard-02-input.json", "shard-03-input.json"]

    results = root / "results"
    results.mkdir()
    rows = json.loads((REF / "results-good.json").read_text())
    for index, row in enumerate((rows[:2], rows[2:4], rows[4:]), start=1):
        (results / f"shard-{index:02}-results.json").write_text(json.dumps(row))
    merged = root / "merged"
    run("merge", "--input-dir", str(inputs), "--results-dir", str(results), "--schema", str(SCHEMA), "--output-dir", str(merged))
    summary = json.loads((merged / "summary.json").read_text())
    assert summary["input_count"] == summary["output_count"] == 5
    assert summary["draft_eligible"] == 1 and summary["draft_blocked_no_ready_email"] == 4
    assert summary["coverage_complete"] is True

    overridden = root / "overridden"
    run("merge", "--input-dir", str(inputs), "--results-dir", str(results), "--schema", str(SCHEMA), "--output-dir", str(overridden), "--overrides", str(REF / "overrides.json"))
    override_summary = json.loads((overridden / "summary.json").read_text())
    assert override_summary["draft_eligible"] == 2
    final_rows = json.loads((overridden / "contact-results.json").read_text())
    coastal = next(row for row in final_rows if row["property"] == "Coastal House")
    assert coastal["status"] == "contact_ready" and coastal["email"] == "reservations@coastal.example.au"

    invalid_results = root / "invalid-results"
    invalid_results.mkdir()
    (invalid_results / "shard-01-results.json").write_text((REF / "results-invalid-source.json").read_text())
    failed = run("merge", "--input-dir", str(inputs), "--results-dir", str(invalid_results), "--schema", str(SCHEMA), "--output-dir", str(root / "invalid-merged"), succeeds=False)
    assert "published contact needs email and public source URL" in failed.stderr

print("PASS: parameterized preparation, exact coverage, source/status gates, overrides, and draft gating verified")
