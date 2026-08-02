#!/usr/bin/env python3
"""Prepare and merge traceable public-email enrichment results."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PUBLISHED = {"contact_ready", "contact_held", "published_unverified"}
NO_EMAIL = {"contact_missing", "blocked"}


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read JSON {path}: {exc}") from exc


def require_text(record: dict, field: str, source: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"{source}: prospect needs non-empty {field!r}")
    return value.strip()


def prepare(args: argparse.Namespace) -> None:
    payload = load_json(args.input)
    prospects = payload.get("prospects") if isinstance(payload, dict) else None
    if not isinstance(prospects, list) or not prospects:
        raise SystemExit("input must be an object with a non-empty prospects array")
    if args.shard_count < 1:
        raise SystemExit("shard-count must be at least 1")

    by_property: dict[str, dict] = {}
    for index, row in enumerate(prospects):
        if not isinstance(row, dict):
            raise SystemExit(f"input prospect {index} must be an object")
        property_name = require_text(row, "property", f"input prospect {index}")
        if property_name in by_property:
            raise SystemExit(f"duplicate property in input: {property_name}")
        website = require_text(row, "website", f"input prospect {index}")
        by_property[property_name] = {
            "property": property_name,
            "region": row.get("region", ""),
            "locality": row.get("locality", ""),
            "website": website,
            "geo_query": row.get("query", ""),
            "geo_conversation_url": row.get("conversation_url", ""),
            "geo_status": row.get("candidate_status", ""),
            "geo_safe_claim": row.get("safe_claim", ""),
        }

    records = sorted(by_property.values(), key=lambda row: (str(row["region"]), row["property"]))
    shard_count = min(args.shard_count, len(records))
    shards = [[] for _ in range(shard_count)]
    for index, row in enumerate(records):
        shards[index % shard_count].append(row)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for index, shard in enumerate(shards, start=1):
        (args.output_dir / f"shard-{index:02}-input.json").write_text(json.dumps(shard, indent=2) + "\n")
    summary = {
        "input": str(args.input),
        "prospect_count": len(records),
        "requested_shard_count": args.shard_count,
        "actual_shard_count": shard_count,
        "shard_sizes": [len(shard) for shard in shards],
        "coverage_complete": sum(map(len, shards)) == len(records),
    }
    (args.output_dir / "prepare-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


def source_url_is_valid(value) -> bool:
    parsed = urlparse(value or "")
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_result(record: dict, required: set[str], statuses: set[str], email_types: set, confidences: set, source: Path) -> None:
    if not isinstance(record, dict):
        raise SystemExit(f"{source}: result must be an object")
    missing = required - record.keys()
    if missing:
        raise SystemExit(f"{source}: {record.get('property')!r} missing {sorted(missing)}")
    property_name = require_text(record, "property", str(source))
    require_text(record, "website", f"{source}: {property_name}")
    status = record["status"]
    if status not in statuses:
        raise SystemExit(f"{source}: invalid status for {property_name}")
    if record["email_type"] not in email_types:
        raise SystemExit(f"{source}: invalid email_type for {property_name}")
    if record["confidence"] not in confidences:
        raise SystemExit(f"{source}: invalid confidence for {property_name}")
    email = record["email"]
    if email is not None and (not isinstance(email, str) or not EMAIL_RE.fullmatch(email)):
        raise SystemExit(f"{source}: invalid email syntax for {property_name}")
    if status in PUBLISHED:
        if not email or not source_url_is_valid(record["email_source_url"]):
            raise SystemExit(f"{source}: published contact needs email and public source URL for {property_name}")
        if status == "contact_ready" and record["mail_domain_status"] not in {"confirmed", "present"}:
            raise SystemExit(f"{source}: contact_ready needs confirmed or present mail-domain status for {property_name}")
    if status in NO_EMAIL and any(record.get(key) is not None for key in ("email", "email_source_url")):
        raise SystemExit(f"{source}: {status} cannot retain email or source URL for {property_name}")


def read_prepared(input_dir: Path) -> dict[str, dict]:
    rows: list[dict] = []
    for path in sorted(input_dir.glob("shard-*-input.json")):
        value = load_json(path)
        if not isinstance(value, list):
            raise SystemExit(f"{path}: input shard must be a JSON array")
        rows.extend(value)
    if not rows:
        raise SystemExit(f"no prepared shards found in {input_dir}")
    expected = {}
    for row in rows:
        property_name = require_text(row, "property", "prepared input")
        if property_name in expected:
            raise SystemExit(f"duplicate property across prepared shards: {property_name}")
        expected[property_name] = row
    return expected


def read_results(results_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(results_dir.glob("shard-*-results.json")):
        value = load_json(path)
        if not isinstance(value, list):
            raise SystemExit(f"{path}: result shard must be a JSON array")
        rows.extend(value)
    if not rows:
        raise SystemExit(f"no result shards found in {results_dir}")
    return rows


def merge(args: argparse.Namespace) -> None:
    schema = load_json(args.schema)
    required = set(schema.get("required", []))
    statuses = set(schema.get("status_values", []))
    email_types = set(schema.get("email_type_values", []))
    confidences = set(schema.get("confidence_values", []))
    if not required or not statuses or not confidences:
        raise SystemExit("schema missing required validation values")
    expected = read_prepared(args.input_dir)
    results = read_results(args.results_dir)
    overrides = load_json(args.overrides) if args.overrides else {}
    if not isinstance(overrides, dict):
        raise SystemExit("overrides must be a JSON object keyed by property")

    seen = set()
    merged = []
    for row in results:
        property_name = row.get("property") if isinstance(row, dict) else None
        if property_name in seen:
            raise SystemExit(f"duplicate property in results: {property_name}")
        if property_name not in expected:
            raise SystemExit(f"unexpected property in results: {property_name}")
        seen.add(property_name)
        reviewed = overrides.get(property_name)
        if reviewed is not None:
            if not isinstance(reviewed, dict):
                raise SystemExit(f"override for {property_name} must be an object")
            row = {**row, **reviewed}
        validate_result(row, required, statuses, email_types, confidences, args.results_dir)
        if row["website"] != expected[property_name]["website"]:
            raise SystemExit(f"website mismatch for {property_name}")
        merged.append(row)
    missing = sorted(set(expected) - seen)
    if missing:
        raise SystemExit(f"coverage mismatch; missing={missing}")

    merged.sort(key=lambda row: (row["status"], row["property"]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "contact-results.json").write_text(json.dumps(merged, indent=2) + "\n")
    fields = sorted({key for row in merged for key in row})
    with (args.output_dir / "contact-results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(merged)
    counts = dict(Counter(row["status"] for row in merged))
    summary = {
        "input_count": len(expected),
        "output_count": len(merged),
        "status_counts": counts,
        "draft_eligible": counts.get("contact_ready", 0),
        "draft_blocked_no_ready_email": len(merged) - counts.get("contact_ready", 0),
        "coverage_complete": len(merged) == len(expected),
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--input", type=Path, required=True)
    prepare_parser.add_argument("--output-dir", type=Path, required=True)
    prepare_parser.add_argument("--shard-count", type=int, default=2)
    merge_parser = commands.add_parser("merge")
    merge_parser.add_argument("--input-dir", type=Path, required=True)
    merge_parser.add_argument("--results-dir", type=Path, required=True)
    merge_parser.add_argument("--schema", type=Path, required=True)
    merge_parser.add_argument("--output-dir", type=Path, required=True)
    merge_parser.add_argument("--overrides", type=Path)
    args = parser.parse_args()
    (prepare if args.command == "prepare" else merge)(args)


if __name__ == "__main__":
    main()
