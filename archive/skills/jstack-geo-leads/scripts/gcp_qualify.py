#!/usr/bin/env python3
"""Conservatively project GCP discovery records into qualification artifacts.

Places proves only discovery-level facts.  It must never manufacture active
site, direct-booking, operating-scale, independence, or contact evidence.
"""
from __future__ import annotations

import argparse, csv, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retained", type=Path, required=True)
    parser.add_argument("--excluded", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    retained = json.loads(args.retained.read_text())
    excluded = json.loads(args.excluded.read_text())
    checked = datetime.now(timezone.utc).isoformat()
    review = []
    for row in retained:
        review.append({**row, "checked_at": checked, "outcome": "needs_review", "business_qualification_status": "needs_review", "official_site_capture_status": "needs_review", "active_operation_status": "needs_review", "direct_booking_or_enquiry_status": "needs_review", "observable_scale_status": "needs_review", "independence_status": "needs_review", "public_contact_status": "needs_review", "disposition_reason": "GCP discovery confirms a website but contains no official-site capture; active operation, direct booking/enquiry, operating scale, independence, and reachable contact remain unverified."})
    rejected = [{**row, "checked_at": checked, "outcome": "rejected", "business_qualification_status": "rejected", "disposition_reason": f"Discovery prefilter exclusion: {row['prefilter_rule']}"} for row in excluded]
    qualified: list[dict] = []
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in (("qualified", qualified), ("needs-review", review), ("rejected", rejected)):
        (args.output_dir / f"{name}.json").write_text(json.dumps(rows, indent=2) + "\n")
        write_csv(args.output_dir / f"{name}.csv", rows)
    summary = {"provider": "gcp_places_text_search", "checked_at": checked, "qualified": 0, "needs_review": len(review), "rejected": len(rejected), "reason_qualified_is_zero": "No official-site evidence has yet been captured; GCP discovery data alone cannot satisfy the downstream business-fit gates."}
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
