#!/usr/bin/env python3
"""Campaign workflow helpers for HarvestAPI LinkedIn lead sourcing.

The low-level linkedin_apify.py script runs one actor call at a time. This
script codifies the multi-step campaign path a reusable multi-step campaign path:

  build-search-input      -> write a HarvestAPI profile-search JSON input
  paginated-search        -> loop startPage, call linkedin-profile-search, dedupe
  enrich-public-ids       -> enrich a list of publicIdentifiers through profile-scraper
  dedupe                  -> remove candidates already present in prior raw/CSV sends
  split-qualification     -> split net-new leads into review batches

Paid network calls are dry-run by default. Pass --execute when you mean to spend.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = "https://api.apify.com/v2"
PROFILE_SEARCH = "harvestapi~linkedin-profile-search"
PROFILE_SCRAPER = "harvestapi~linkedin-profile-scraper"

OWNER_OPERATOR_FILTERS = {
    "profileScraperMode": "Full",
    "currentJobTitles": [
        "Founder",
        "Co-Founder",
        "Owner",
        "CEO",
        "Chief Executive Officer",
        "Managing Director",
        "President",
    ],
    "seniorityLevelIds": ["320", "310"],
    "companyHeadcount": ["C", "D"],
    "locations": [
        "United States",
        "United Kingdom",
        "Canada",
        "Australia",
        "Ireland",
        "New Zealand",
        "Singapore",
    ],
    "profileLanguages": ["English"],
    "recentlyPostedOnLinkedIn": True,
    "yearsAtCurrentCompanyIds": ["3", "4", "5"],
}


def load_json(path: str | Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def token() -> str:
    tok = os.environ.get("APIFY_API_TOKEN", "").strip()
    if not tok:
        sys.exit("APIFY_API_TOKEN is not set. Load env first, or run without --execute for dry-run.")
    return tok


def actor_url(actor_slug: str, timeout: int, max_charge: float | None = None, printable: bool = False) -> str:
    tok = "$APIFY_API_TOKEN" if printable else token()
    url = f"{API_BASE}/acts/{actor_slug}/run-sync-get-dataset-items?token={tok}&timeout={timeout}&format=json"
    if max_charge is not None:
        url += f"&maxTotalChargeUsd={max_charge}"
    return url


def post_actor(actor_slug: str, payload: dict, timeout: int, max_charge: float | None):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        actor_url(actor_slug, timeout, max_charge),
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout + 60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"Apify HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:800]}")
    if isinstance(data, dict) and data.get("error"):
        sys.exit(f"Apify error: {json.dumps(data['error'])[:800]}")
    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict) and data[0].get("error"):
        sys.exit(f"Apify error: {data[0]['error']}")
    if not isinstance(data, list):
        sys.exit(f"Unexpected non-list actor response: {str(data)[:800]}")
    return data


def norm_url(url: str | None) -> str:
    url = (url or "").strip().lower().rstrip("/")
    return re.sub(r"\?.*$", "", url)


def sales_nav_id(url: str | None) -> str:
    url = url or ""
    if "/sales/people/" not in url:
        return ""
    return url.rsplit("/sales/people/", 1)[1].split("?", 1)[0].strip()


def lead_key(profile: dict) -> str:
    return (
        norm_url(profile.get("linkedinUrl"))
        or profile.get("id")
        or profile.get("publicIdentifier")
        or json.dumps(profile, sort_keys=True)[:200]
    )


def cmd_build_search_input(args) -> int:
    if args.filters:
        payload = load_json(args.filters)
    elif args.preset == "owner-operator":
        payload = dict(OWNER_OPERATOR_FILTERS)
    else:
        sys.exit("No filters provided. Ask the user for titles, seniority, headcount, locations, industries, and activity filters.")

    if args.industry_ids:
        payload["industryIds"] = load_json(args.industry_ids)
    if args.start_page is not None:
        payload["startPage"] = args.start_page
    if args.max_items is not None:
        payload["maxItems"] = args.max_items
    write_json(args.out, payload)
    print(f"wrote search input -> {args.out}")
    return 0


def cmd_paginated_search(args) -> int:
    base = load_json(args.input_file)
    all_items, seen, dry_pages = [], set(), 0
    for page in range(args.start_page, args.start_page + args.max_pages):
        payload = dict(base, startPage=page, maxItems=args.per_page)
        if not args.execute:
            print(f"# DRY-RUN page {page}; would POST to:")
            print(actor_url(PROFILE_SEARCH, args.timeout, args.max_charge, printable=True))
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            continue
        page_items = post_actor(PROFILE_SEARCH, payload, args.timeout, args.max_charge)
        new = 0
        for profile in page_items:
            key = lead_key(profile)
            if key in seen:
                continue
            seen.add(key)
            all_items.append(profile)
            new += 1
        print(f"page {page}: got={len(page_items)} new={new} unique_total={len(all_items)}")
        if len(all_items) >= args.target:
            all_items = all_items[: args.target]
            break
        if not page_items or new == 0:
            dry_pages += 1
            if dry_pages >= 2:
                print(f"stopping: {dry_pages} consecutive dry pages")
                break
        else:
            dry_pages = 0
        time.sleep(args.sleep)
    if args.execute:
        write_json(args.out, all_items)
        print(f"wrote {len(all_items)} unique profiles -> {args.out}")
    return 0


def cmd_enrich_public_ids(args) -> int:
    candidates = load_json(args.candidates)
    public_ids = []
    for item in candidates[: args.limit if args.limit else None]:
        if isinstance(item, str):
            public_id = item
        else:
            public_id = item.get("publicIdentifier") or item.get("public_identifier")
        if public_id and public_id not in public_ids:
            public_ids.append(public_id)
    if not public_ids:
        sys.exit("No publicIdentifier values found.")

    all_items = []
    for start in range(0, len(public_ids), args.chunk_size):
        chunk = public_ids[start : start + args.chunk_size]
        payload = {
            "profileScraperMode": args.mode,
            "publicIdentifiers": chunk,
        }
        if not args.execute:
            print(f"# DRY-RUN chunk {start // args.chunk_size + 1}; would POST to:")
            print(actor_url(PROFILE_SCRAPER, args.timeout, args.max_charge, printable=True))
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            continue
        data = post_actor(PROFILE_SCRAPER, payload, args.timeout, args.max_charge)
        all_items.extend(data)
        write_json(args.out, all_items)
        print(f"chunk {start // args.chunk_size + 1}: requested={len(chunk)} enriched={len(data)} total={len(all_items)}")
        time.sleep(args.sleep)
    if args.execute:
        write_json(args.out, all_items)
        print(f"wrote {len(all_items)} enriched profiles -> {args.out}")
    return 0


def collect_existing(existing_raw_paths: list[str], existing_csv_paths: list[str]):
    urls, ids = set(), set()
    for path in existing_raw_paths:
        if not path:
            continue
        for profile in load_json(path):
            url = norm_url(profile.get("linkedinUrl"))
            if url:
                urls.add(url)
            if profile.get("id"):
                ids.add(profile["id"])
    for path in existing_csv_paths:
        if not path:
            continue
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                url = norm_url(row.get("OpenProfile"))
                if url:
                    urls.add(url)
                mid = sales_nav_id(row.get("OpenInSalesNav"))
                if mid:
                    ids.add(mid)
    return urls, ids


def cmd_dedupe(args) -> int:
    existing_urls, existing_ids = collect_existing(args.existing_raw, args.existing_csv)
    raw = load_json(args.raw)
    net_new, dupes = [], []
    seen_urls, seen_ids = set(), set()
    for profile in raw:
        url = norm_url(profile.get("linkedinUrl"))
        mid = profile.get("id") or ""
        duplicate = (
            (url and url in existing_urls)
            or (mid and mid in existing_ids)
            or (url and url in seen_urls)
            or (mid and mid in seen_ids)
        )
        if duplicate:
            dupes.append(profile)
            continue
        if url:
            seen_urls.add(url)
        if mid:
            seen_ids.add(mid)
        profile["_expandIndex"] = len(net_new)
        net_new.append(profile)
    write_json(args.out_net_new, net_new)
    write_json(args.out_dupes, dupes)
    print(f"raw={len(raw)} net_new={len(net_new)} duplicates={len(dupes)}")
    return 0


def cmd_split_qualification(args) -> int:
    leads = load_json(args.leads)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob(f"{args.prefix}_*.json"):
        old.unlink()
    count = 0
    for start in range(0, len(leads), args.batch_size):
        chunk = leads[start : start + args.batch_size]
        write_json(out_dir / f"{args.prefix}_{count}.json", chunk)
        count += 1
    print(f"wrote {count} batches of up to {args.batch_size} leads -> {out_dir}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build-search-input")
    p.add_argument("--filters", help="JSON file containing HarvestAPI profile-search filters")
    p.add_argument("--preset", choices=["owner-operator"], help="Use a built-in filter preset")
    p.add_argument("--industry-ids", help="JSON list of LinkedIn industry ids to add")
    p.add_argument("--start-page", type=int)
    p.add_argument("--max-items", type=int)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_build_search_input)

    p = sub.add_parser("paginated-search")
    p.add_argument("--input-file", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--target", type=int, default=200)
    p.add_argument("--start-page", type=int, default=1)
    p.add_argument("--max-pages", type=int, default=20)
    p.add_argument("--per-page", type=int, default=50)
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--max-charge", type=float)
    p.add_argument("--sleep", type=float, default=1.0)
    p.add_argument("--execute", action="store_true")
    p.set_defaults(func=cmd_paginated_search)

    p = sub.add_parser("enrich-public-ids")
    p.add_argument("--candidates", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--limit", type=int)
    p.add_argument("--chunk-size", type=int, default=10)
    p.add_argument("--mode", default="Profile details no email ($4 per 1k)")
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--max-charge", type=float)
    p.add_argument("--sleep", type=float, default=1.0)
    p.add_argument("--execute", action="store_true")
    p.set_defaults(func=cmd_enrich_public_ids)

    p = sub.add_parser("dedupe")
    p.add_argument("--raw", required=True)
    p.add_argument("--existing-raw", action="append", default=[])
    p.add_argument("--existing-csv", action="append", default=[])
    p.add_argument("--out-net-new", required=True)
    p.add_argument("--out-dupes", required=True)
    p.set_defaults(func=cmd_dedupe)

    p = sub.add_parser("split-qualification")
    p.add_argument("--leads", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--batch-size", type=int, default=20)
    p.add_argument("--prefix", default="batch")
    p.set_defaults(func=cmd_split_qualification)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
