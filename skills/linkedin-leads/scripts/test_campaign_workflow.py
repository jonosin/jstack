#!/usr/bin/env python3
"""Offline tests for campaign_workflow.py. No paid Apify calls."""
import csv
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["APIFY_API_TOKEN"] = "TEST_DUMMY_TOKEN_do_not_use"

import campaign_workflow as cw  # noqa: E402


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def test_build_search_input_preset():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "search.json"
        rc = cw.main(["build-search-input", "--preset", "owner-operator", "--start-page", "9", "--max-items", "50", "--out", str(out)])
        data = json.load(open(out))
    assert rc == 0
    assert data["profileScraperMode"] == "Full"
    assert data["companyHeadcount"] == ["C", "D"]
    assert data["recentlyPostedOnLinkedIn"] is True
    assert data["startPage"] == 9
    assert data["maxItems"] == 50


def test_dedupe_against_raw_and_csv():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        raw = [
            {"id": "1", "linkedinUrl": "https://www.linkedin.com/in/a"},
            {"id": "2", "linkedinUrl": "https://www.linkedin.com/in/b"},
            {"id": "3", "linkedinUrl": "https://www.linkedin.com/in/c"},
            {"id": "3", "linkedinUrl": "https://www.linkedin.com/in/c"},
        ]
        existing = [{"id": "1", "linkedinUrl": "https://www.linkedin.com/in/a"}]
        write(root / "raw.json", raw)
        write(root / "existing.json", existing)
        with open(root / "existing.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["OpenProfile", "OpenInSalesNav"])
            w.writeheader()
            w.writerow({"OpenProfile": "https://www.linkedin.com/in/b", "OpenInSalesNav": "https://www.linkedin.com/sales/people/2"})
        rc = cw.main([
            "dedupe",
            "--raw", str(root / "raw.json"),
            "--existing-raw", str(root / "existing.json"),
            "--existing-csv", str(root / "existing.csv"),
            "--out-net-new", str(root / "net.json"),
            "--out-dupes", str(root / "dupes.json"),
        ])
        net = json.load(open(root / "net.json"))
        dupes = json.load(open(root / "dupes.json"))
    assert rc == 0
    assert len(net) == 1
    assert net[0]["id"] == "3"
    assert net[0]["_expandIndex"] == 0
    assert len(dupes) == 3


def test_split_qualification_batches():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write(root / "leads.json", [{"id": str(i)} for i in range(5)])
        rc = cw.main(["split-qualification", "--leads", str(root / "leads.json"), "--out-dir", str(root / "batches"), "--batch-size", "2"])
        batches = sorted((root / "batches").glob("batch_*.json"))
        sizes = [len(json.load(open(p))) for p in batches]
    assert rc == 0
    assert sizes == [2, 2, 1]


def test_enrich_public_ids_dry_run_hides_token(capsys=None):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write(root / "candidates.json", [{"publicIdentifier": "a"}, {"publicIdentifier": "b"}])
        rc = cw.main(["enrich-public-ids", "--candidates", str(root / "candidates.json"), "--out", str(root / "out.json"), "--chunk-size", "1"])
    assert rc == 0


def _main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"\n{len(tests)}/{len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
