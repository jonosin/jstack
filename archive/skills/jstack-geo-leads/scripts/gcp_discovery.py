#!/usr/bin/env python3
"""Run a lineage-preserving Google Places Text Search discovery batch.

The runner deliberately uses only the Places Text Search response fields needed
for discovery.  It never fetches property pages or attempts contact enrichment.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

API = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = "places.id,places.displayName,places.formattedAddress,places.googleMapsUri,places.websiteUri,places.primaryType,places.types,places.businessStatus"
FAMILIES = ("hotel", "boutique hotel", "resort", "lodge", "retreat")
CHAIN = re.compile(r"\b(accor|best western|choice hotels|courtyard|four seasons|hampton inn|hilton|holiday inn|hyatt|ihg|marriott|motel 6|omni|radisson|ritz carlton|sheraton|westin|wyndham)\b", re.I)
SINGLE = re.compile(r"\b(cottage|holiday home|tiny house|tiny home|vacation rental|villa)\b", re.I)
IRRELEVANT_TYPES = {"real_estate_agency", "travel_agency", "restaurant", "bar", "spa", "campground"}


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def domain(url: str) -> str:
    return urlparse(url if "://" in url else f"https://{url}").netloc.lower().removeprefix("www.")


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def dedupe_key(row: dict) -> str:
    if row.get("place_id"):
        return f"place_id:{row['place_id']}"
    if row.get("website_domain"):
        return f"domain:{row['website_domain']}"
    return f"name_locality:{norm(row['property'])}|{norm(row['locality'])}"


def classify(row: dict) -> tuple[str, str]:
    title, site = row["property"], row["website"]
    types = set(row.get("types") or [])
    if row.get("business_status") == "CLOSED_PERMANENTLY":
        return "excluded_closed", "business_status_closed_permanently"
    if not site:
        return "excluded_missing_website", "website_blank"
    if CHAIN.search(title) or any(part in site.lower() for part in ("hilton.com", "marriott.com", "hyatt.com", "ihg.com", "wyndhamhotels.com")):
        return "excluded_chain_or_franchise", "chain_name_or_domain"
    if types & IRRELEVANT_TYPES:
        return "excluded_irrelevant", "primary_type_or_types"
    if SINGLE.search(title):
        return "excluded_obvious_single_unit_stay", "single_unit_name"
    return "retain_for_manual_qualification", "no_discovery_level_exclusion"


def prepare(args: argparse.Namespace) -> None:
    markets = json.loads(args.markets.read_text())
    if not isinstance(markets, list) or not 3 <= len(markets) <= 5:
        raise SystemExit("markets must be a JSON list of 3 to 5 US micro-markets")
    rows = []
    for market in markets:
        name = market.get("market", "").strip()
        if not name:
            raise SystemExit("every market needs market")
        for family in FAMILIES:
            rows.append({"query_id": f"q{len(rows)+1:03d}", "market": name, "family": family, "textQuery": f"{family} in {name}, USA"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"country": "US", "created_at": timestamp(), "field_mask": FIELD_MASK, "queries": rows}, indent=2) + "\n")
    print(json.dumps({"query_count": len(rows), "field_mask": FIELD_MASK}, indent=2))


def token() -> str:
    return subprocess.check_output(["gcloud", "auth", "application-default", "print-access-token"], text=True).strip()


def run(args: argparse.Namespace) -> None:
    plan = json.loads(args.input.read_text())
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    unexpected = [path.name for path in out.iterdir() if path.name not in {"input.json", "source-ledger.json"}]
    if unexpected:
        raise SystemExit(f"refusing to overwrite existing run artifacts: {', '.join(sorted(unexpected))}")
    (out / "input.json").write_text(json.dumps(plan, indent=2) + "\n")
    access_token = token()
    quota_project = subprocess.check_output(["gcloud", "config", "get-value", "project"], text=True).strip()
    all_places, query_log = [], []
    for query in plan["queries"]:
        page_token = None
        raw_files, returned = [], 0
        for page_number in range(1, args.max_pages + 1):
            payload = {"textQuery": query["textQuery"], "pageSize": args.page_size}
            if page_token:
                payload["pageToken"] = page_token
            body = json.dumps(payload).encode()
            request = Request(API, data=body, headers={"Content-Type": "application/json", "X-Goog-FieldMask": FIELD_MASK, "X-Goog-User-Project": quota_project, "Authorization": f"Bearer {access_token}"}, method="POST")
            try:
                with urlopen(request, timeout=60) as response:
                    raw = json.loads(response.read())
            except HTTPError as exc:
                message = exc.read().decode(errors="replace")
                failure = {"provider": "gcp_places_text_search", "api": API, "field_mask": FIELD_MASK, "status": "blocked", "blocked_at_query": query["query_id"], "blocked_at_page": page_number, "error_code": exc.code, "error": message[:1000], "resolution": "Set a quota project on the local application-default credentials, then rerun this same batch directory."}
                (out / "source-ledger.json").write_text(json.dumps(failure, indent=2) + "\n")
                raise SystemExit(f"Places request {query['query_id']} page {page_number} failed ({exc.code}): {message[:500]}")
            (out / "raw").mkdir(exist_ok=True)
            raw_file = f"raw/{query['query_id']}-page-{page_number:02d}.json"
            (out / raw_file).write_text(json.dumps(raw, indent=2) + "\n")
            raw_files.append(raw_file)
            places = raw.get("places", [])
            returned += len(places)
            for place in places:
                all_places.append({"query_id": query["query_id"], "market": query["market"], "query": query["textQuery"], "page": page_number, "place": place})
            page_token = raw.get("nextPageToken")
            if not page_token:
                break
        query_log.append({**query, "returned_places": returned, "page_count": len(raw_files), "raw_files": raw_files})
    (out / "raw-index.json").write_text(json.dumps(query_log, indent=2) + "\n")
    (out / "raw-combined.json").write_text(json.dumps(all_places, indent=2) + "\n")
    ledger = {"provider": "gcp_places_text_search", "api": API, "field_mask": FIELD_MASK, "credential": "application-default credentials (not stored)", "quota_project_header": True, "status": "completed", "started_at": plan["created_at"], "completed_at": datetime.now(timezone.utc).isoformat(), "query_count": len(query_log), "raw_response_count": len(all_places), "cost_note": "Google Cloud billing/usage is account-managed; this run does not infer a dollar charge.", "project": quota_project}
    (out / "source-ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
    print(json.dumps(ledger, indent=2))


def normalize(args: argparse.Namespace) -> None:
    raw = json.loads(args.input.read_text())
    groups: dict[str, list[dict]] = {}
    for index, item in enumerate(raw):
        place = item["place"]
        display = place.get("displayName", {}).get("text", "")
        website = place.get("websiteUri", "")
        row = {"property": display, "country": "US", "region": item["market"], "locality": item["market"], "website": website, "website_domain": domain(website), "place_id": place.get("id", ""), "google_maps_url": place.get("googleMapsUri", ""), "formatted_address": place.get("formattedAddress", ""), "primary_type": place.get("primaryType", ""), "types": place.get("types", []), "business_status": place.get("businessStatus", ""), "source_query": item["query"], "source_query_id": item["query_id"], "source_index": index}
        groups.setdefault(dedupe_key(row), []).append(row)
    rows = []
    for key, records in groups.items():
        row = records[0].copy()
        row["dedupe_key"] = key
        row["raw_record_count"] = len(records)
        row["source_query_ids"] = [record["source_query_id"] for record in records]
        row["source_queries"] = list(dict.fromkeys(record["source_query"] for record in records))
        row["prefilter_outcome"], row["prefilter_rule"] = classify(row)
        rows.append(row)
    rows.sort(key=lambda row: row["source_index"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, subset in (("normalized-records.json", rows), ("retained-plausible.json", [r for r in rows if r["prefilter_outcome"] == "retain_for_manual_qualification"]), ("excluded.json", [r for r in rows if r["prefilter_outcome"] != "retain_for_manual_qualification"])):
        (args.output_dir / name).write_text(json.dumps(subset, indent=2) + "\n")
    fields = sorted({field for row in rows for field in row if field not in {"types", "source_query_ids", "source_queries"}})
    with (args.output_dir / "normalized-records.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(({k: (json.dumps(v) if isinstance(v, list) else v) for k, v in row.items() if k in fields} for row in rows))
    summary = {"raw_records": len(raw), "deduped_records": len(rows), "duplicates_collapsed": len(raw) - len(rows), "outcomes": dict(Counter(row["prefilter_outcome"] for row in rows))}
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare"); p.add_argument("--markets", type=Path, required=True); p.add_argument("--output", type=Path, required=True); p.set_defaults(func=prepare)
    r = sub.add_parser("run"); r.add_argument("--input", type=Path, required=True); r.add_argument("--output-dir", type=Path, required=True); r.add_argument("--page-size", type=int, default=20); r.add_argument("--max-pages", type=int, default=3); r.set_defaults(func=run)
    n = sub.add_parser("normalize"); n.add_argument("--input", type=Path, required=True); n.add_argument("--output-dir", type=Path, required=True); n.set_defaults(func=normalize)
    args = parser.parse_args(); args.func(args)


if __name__ == "__main__":
    main()
