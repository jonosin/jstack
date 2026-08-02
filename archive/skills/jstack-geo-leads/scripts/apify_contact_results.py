#!/usr/bin/env python3
"""Convert source-linked Apify email output into conservative contact statuses."""
from __future__ import annotations

import argparse, json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def domain(value: str) -> str:
    return urlparse(value if "://" in value else f"https://{value}").netloc.lower().removeprefix("www.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", type=Path, required=True, help="Apify input.json")
    parser.add_argument("--raw", type=Path, required=True, help="raw-output.json")
    parser.add_argument("--run", type=Path, required=True, help="run-current.json")
    parser.add_argument("--properties", type=Path, required=True, help="GCP retained-plausible.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    cohort = json.loads(args.cohort.read_text())["urls"]
    raw = json.loads(args.raw.read_text())
    run = json.loads(args.run.read_text())["data"]
    properties = json.loads(args.properties.read_text())
    by_domain = {domain(row["website"]): row for row in properties}
    emails = defaultdict(list)
    for row in raw:
        if row.get("email") and row.get("seedUrl") and row.get("url"):
            emails[domain(row["seedUrl"])].append(row)
    results = []
    observed = datetime.now(timezone.utc).isoformat()
    for entry in cohort:
        seed = entry["url"]
        seed_domain = domain(seed)
        property_row = by_domain.get(seed_domain, {})
        matches = emails[seed_domain]
        published = []
        held = []
        for item in matches:
            email = item["email"].lower()
            email_domain = email.rsplit("@", 1)[-1]
            target = {seed_domain, seed_domain.removeprefix("www.")}
            (published if email_domain in target else held).append({"email": email, "source_url": item["url"]})
        if published:
            status = "published_unverified"; chosen = published
            note = "Published on an official-site crawl, but mail-domain verification has not been performed."
        elif held:
            status = "contact_held"; chosen = held
            note = "Published email uses a third-party domain; property relationship needs review."
        else:
            status = "contact_missing"; chosen = []
            note = "No public email returned by the bounded official-site crawl."
        results.append({"property": property_row.get("property"), "website": seed, "status": status, "emails": chosen, "observed_at": observed, "notes": note, "actor": "maximedupre/website-emails-scraper", "run_id": run["id"]})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "contact-results.json").write_text(json.dumps(results, indent=2) + "\n")
    summary = {"actor": "maximedupre/website-emails-scraper", "run_id": run["id"], "dataset_id": run["defaultDatasetId"], "status": run["status"], "actual_cost_usd": run.get("usageTotalUsd"), "cohort_count": len(cohort), "raw_email_rows": len(raw), "outcomes": dict(Counter(row["status"] for row in results)), "draft_eligible": 0, "decision": "Apify yields source-linked public emails, but this first pilot has no mail-domain confirmation; retain all records outside outreach and use agent review only for third-party or ambiguous sources."}
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
