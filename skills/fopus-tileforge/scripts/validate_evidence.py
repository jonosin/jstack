"""Reject corrupt visual evidence and unreviewed/failed visual-review verdicts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image


def _is_placeholder(value: str) -> bool:
    return re.search(r"<[^<>]*>", value) is not None


def validate(evidence_dir: Path, review_path: Path | None = None) -> dict:
    images = sorted(evidence_dir.glob("*.png"))
    assert images, "no PNG evidence found"
    records = []
    for path in images:
        with Image.open(path) as image:
            assert image.format == "PNG", f"{path.name} is not a PNG"
            size = list(image.size)
            image.verify()
        records.append({
            "file": path.name,
            "size": size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    review_path = review_path or evidence_dir / "visual-review.json"
    review = json.loads(review_path.read_text())
    assert review.get("independent") is True, "visual review must be independent"
    assert isinstance(review.get("reviewer"), str) and review["reviewer"].strip(), "visual review must identify its reviewer"
    assert not _is_placeholder(review["reviewer"]), "visual review has unresolved reviewer placeholder"
    counts = review.get("counts", review)
    critical = counts.get("Critical", counts.get("critical", -1))
    important = counts.get("Important", counts.get("important", -1))
    minor = counts.get("Minor", counts.get("minor", -1))
    assert all(isinstance(value, int) and value >= 0 for value in (critical, important, minor)), "visual review counts are invalid"
    assert critical == 0, "visual review has critical findings"
    assert important == 0, "visual review has important findings"
    for check in review.get("semantic_checks", []):
        if check.get("kind") != "contextual-orientation":
            continue
        assert isinstance(check.get("asset_id"), str) and check["asset_id"].strip(), (
            "contextual orientation requires asset ID"
        )
        assert not _is_placeholder(check["asset_id"]), "contextual orientation has unresolved asset ID placeholder"
        assert isinstance(check.get("accepted_calibration_map"), str) and check["accepted_calibration_map"].strip(), (
            "contextual orientation requires accepted calibration map"
        )
        assert isinstance(check.get("station_relationship"), str) and check["station_relationship"].strip(), (
            "contextual orientation requires station relationship"
        )
        assert check.get("user_accepted") is True, "contextual orientation requires user acceptance"
        assert check.get("isolated_after_acceptance") is True, (
            "contextual orientation requires isolation after acceptance"
        )
        assert isinstance(check.get("recreated_relationship"), str) and check["recreated_relationship"].strip(), (
            "contextual orientation requires recreated relationship"
        )
        assert not any(
            _is_placeholder(check[field])
            for field in ("accepted_calibration_map", "station_relationship", "recreated_relationship")
        ), "contextual orientation has unresolved template placeholder"
        assert check.get("verdict") == "accepted", "contextual orientation requires accepted verdict"
    result = {
        "format": "tileforge-evidence-validation-v1",
        "status": "PASS",
        "reviewer": review["reviewer"],
        "review_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
        "images": records,
    }
    (evidence_dir / "evidence-validation-report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--evidence-dir", type=Path, required=True); parser.add_argument("--review", type=Path)
    args = parser.parse_args(); print(json.dumps(validate(args.evidence_dir, args.review)))


if __name__ == "__main__": main()
