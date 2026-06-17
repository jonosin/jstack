#!/usr/bin/env python3
"""StayFrame prospect-table maintenance.

Keeps one canonical CSV:
~/ventures/stayframe/leads/list/prospects-s6-100-apify-social.csv
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path


SF_ROOT = Path(os.path.expanduser("~/ventures/stayframe"))
LEADS_DIR = SF_ROOT / "leads" / "list"
CANONICAL = LEADS_DIR / "prospects-s6-100-apify-social.csv"
APIFY_DIR = LEADS_DIR / "apify"
SCORING_DIR = SF_ROOT / "leads" / "scoring"
RANKED = SCORING_DIR / "prospects-s7-ranked.csv"

STALE_CSVS = {
    "prospects-s6-100.csv",
    "prospects-s6-100-social-pass1.csv",
    "prospects-s6-100-social-pass2.csv",
}

UNKNOWN = {"", "unknown", "none confirmed", "n/a", "na", "null", "none"}


def is_real(value: str | None) -> bool:
    return (value or "").strip().lower() not in UNKNOWN


def clean(value: str | None) -> str:
    value = (value or "").strip()
    return "" if value.lower() in UNKNOWN else value


def slugish(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")


def domain(url: str | None) -> str:
    url = clean(url)
    if not url:
        return ""
    if not re.match(r"https?://", url):
        url = "https://" + url
    host = urllib.parse.urlparse(url).netloc.lower()
    host = host.removeprefix("www.")
    return host


def load_rows(path: Path = CANONICAL) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise SystemExit(f"missing canonical CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [dict(r) for r in reader]
        return list(reader.fieldnames or []), rows


def write_rows(headers: list[str], rows: list[dict[str, str]], path: Path = CANONICAL) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({h: r.get(h, "") for h in headers})
    tmp.replace(path)


def dedupe_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        slugish(row.get("property_name")),
        slugish(row.get("country")),
        domain(row.get("official_site") or row.get("apify_original_start_url")),
    )


def score_row(row: dict[str, str]) -> tuple[int, list[str]]:
    reasons: list[str] = []
    score = 0

    if row.get("verification_status") == "verified":
        score += 3
        reasons.append("verified")
    elif row.get("verification_status") == "needs_verify":
        score += 1
        reasons.append("needs verify")

    if row.get("icp_status") == "in_icp":
        score += 4
        reasons.append("in ICP")
    elif row.get("icp_status") == "maybe_icp":
        score += 1
        reasons.append("maybe ICP")
    elif row.get("icp_status") == "out_of_icp":
        score -= 5
        reasons.append("out of ICP")

    if row.get("segment") == "active_meta_advertiser":
        score += 2
        reasons.append("active advertiser seed")
    elif row.get("segment") == "au_layer":
        score += 1
        reasons.append("AU expansion")

    contacts = [
        clean(row.get("apify_emails")),
        clean(row.get("apify_phones")),
        clean(row.get("apify_instagram") or row.get("instagram")),
        clean(row.get("apify_facebook") or row.get("facebook")),
    ]
    contact_count = sum(bool(c) for c in contacts)
    if contact_count >= 3:
        score += 2
        reasons.append("multi-channel contact")
    elif contact_count:
        score += 1
        reasons.append("contact found")

    if row.get("outreach_angle") == "videographer_replacement":
        score += 1
        reasons.append("visual upside")
    elif row.get("outreach_angle") == "do_not_prioritize":
        score -= 5
        reasons.append("do not prioritize")

    fb_ad = (row.get("apify_facebook_ad_status") or "").lower()
    if "currently running ads" in fb_ad and "isn't" not in fb_ad:
        score += 1
        reasons.append("current FB ads")

    return score, reasons


def tier(score: int, row: dict[str, str]) -> str:
    if row.get("icp_status") == "out_of_icp" or row.get("outreach_angle") == "do_not_prioritize":
        return "bench"
    if score >= 10:
        return "T1"
    if score >= 7:
        return "T2"
    if row.get("verification_status") == "needs_verify":
        return "verify"
    return "T3"


def channel(row: dict[str, str]) -> str:
    if clean(row.get("apify_emails")):
        return "email"
    if clean(row.get("apify_instagram") or row.get("instagram")):
        return "instagram_dm"
    if clean(row.get("apify_facebook") or row.get("facebook")):
        return "facebook_dm"
    if clean(row.get("apify_phones")):
        return "phone_owner_discovery"
    return "needs_contact"


def frame(row: dict[str, str]) -> str:
    angle = row.get("outreach_angle")
    if angle == "commission_led":
        return "commission-led"
    if angle == "occupancy_led":
        return "occupancy-led"
    if angle == "videographer_replacement":
        return "visual-multiplication"
    if angle == "commission_or_occupancy":
        return "ab-test"
    return "do-not-prioritize"


def cmd_summary(_: argparse.Namespace) -> None:
    headers, rows = load_rows()
    print(f"canonical: {CANONICAL}")
    print(f"rows={len(rows)} cols={len(headers)}")
    for col in ["market", "segment", "verification_status", "icp_status", "outreach_angle", "apify_social_status"]:
        print(f"\n{col}")
        for value, n in Counter((r.get(col) or "<blank>") for r in rows).most_common():
            print(f"  {value}: {n}")
    print("\ncoverage")
    for col in ["official_site", "apify_instagram", "apify_facebook", "apify_tiktok", "apify_emails", "apify_phones"]:
        print(f"  {col}: {sum(is_real(r.get(col)) for r in rows)}/{len(rows)}")


def cmd_validate(_: argparse.Namespace) -> None:
    headers, rows = load_rows()
    errors: list[str] = []
    for name in STALE_CSVS:
        if (LEADS_DIR / name).exists():
            errors.append(f"stale CSV still present: {LEADS_DIR / name}")
    if len(rows) != len({r.get("id") for r in rows}):
        errors.append("duplicate ids")
    if "property_name" not in headers:
        errors.append("missing property_name header")
    dups = [key for key, count in Counter(dedupe_key(r) for r in rows if dedupe_key(r)[0]).items() if count > 1]
    if dups:
        errors.append(f"possible duplicate properties: {dups[:10]}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print("ok")


def cmd_append(args: argparse.Namespace) -> None:
    headers, rows = load_rows()
    existing = {dedupe_key(r) for r in rows}
    max_id = max(int(r.get("id") or 0) for r in rows)
    added: list[dict[str, str]] = []

    with Path(args.input).open(newline="", encoding="utf-8") as f:
        for incoming in csv.DictReader(f):
            row = {h: "" for h in headers}
            for h in headers:
                if h in incoming:
                    row[h] = clean(incoming[h])
            if not clean(row.get("property_name")):
                continue
            key = dedupe_key(row)
            if key in existing:
                continue
            max_id += 1
            row["id"] = str(max_id)
            if not row.get("verification_status"):
                row["verification_status"] = "needs_verify"
            if not row.get("icp_status"):
                row["icp_status"] = "maybe_icp"
            if not row.get("segment"):
                row["segment"] = "ota_dependent"
            if not row.get("source_seed"):
                row["source_seed"] = args.source_seed or "manual_append"
            rows.append(row)
            existing.add(key)
            added.append(row)

    if not args.dry_run:
        write_rows(headers, rows)
    print(f"added={len(added)} dry_run={args.dry_run}")


def cmd_rank(args: argparse.Namespace) -> None:
    _, rows = load_rows()
    ranked: list[dict[str, str]] = []
    for r in rows:
        score, reasons = score_row(r)
        ranked.append({
            "id": r.get("id", ""),
            "property_name": r.get("property_name", ""),
            "market": r.get("market", ""),
            "segment": r.get("segment", ""),
            "verification_status": r.get("verification_status", ""),
            "icp_status": r.get("icp_status", ""),
            "sf_score": str(score),
            "tier": tier(score, r),
            "recommended_channel": channel(r),
            "message_frame": frame(r),
            "next_action": "draft_first_touch" if tier(score, r) in {"T1", "T2"} else "verify_or_hold",
            "reason": "; ".join(reasons),
            "official_site": r.get("official_site", ""),
            "instagram": r.get("apify_instagram") or r.get("instagram", ""),
            "facebook": r.get("apify_facebook") or r.get("facebook", ""),
            "email": r.get("apify_emails", ""),
            "phone": r.get("apify_phones", ""),
        })
    ranked.sort(key=lambda r: (-int(r["sf_score"]), r["tier"], r["market"], r["property_name"]))
    SCORING_DIR.mkdir(parents=True, exist_ok=True)
    with RANKED.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(ranked[0].keys()) if ranked else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ranked)
    print(f"wrote {RANKED}")
    if args.top:
        for r in ranked[: args.top]:
            print(f"{r['tier']} {r['sf_score']:>2} | {r['property_name']} | {r['recommended_channel']} | {r['message_frame']}")


def rows_for_apify(rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    selected = []
    for r in rows:
        if not is_real(r.get("official_site")):
            continue
        status = (r.get("apify_social_status") or "").strip()
        if status in {"found"} and (is_real(r.get("apify_instagram")) or is_real(r.get("apify_emails"))):
            continue
        selected.append(r)
        if limit and len(selected) >= limit:
            break
    return selected


def cmd_apify_input(args: argparse.Namespace) -> None:
    _, rows = load_rows()
    selected = rows_for_apify(rows, args.limit)
    payload = {"startUrls": [{"url": r["official_site"]} for r in selected]}
    output = Path(args.output)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {output} urls={len(selected)}")


def run_apify(payload: dict, timeout: int) -> list[dict]:
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise SystemExit("APIFY_TOKEN is required")
    url = (
        "https://api.apify.com/v2/acts/apify~social-media-leads-analyzer/"
        f"run-sync-get-dataset-items?token={urllib.parse.quote(token)}&timeout={timeout}"
    )
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout + 60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def cmd_apify_run(args: argparse.Namespace) -> None:
    _, rows = load_rows()
    selected = rows_for_apify(rows, args.limit)
    if not selected:
        print("no rows need Apify enrichment")
        return
    payload = {"startUrls": [{"url": r["official_site"]} for r in selected]}
    items = run_apify(payload, args.timeout)
    APIFY_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    output = APIFY_DIR / f"social-media-leads-run-{stamp}.json"
    output.write_text(json.dumps(items, indent=2), encoding="utf-8")
    print(f"wrote {output} items={len(items)}")
    merge_apify_files([output])


def first_url(items: list[dict], key: str) -> str:
    if not items:
        return ""
    first = items[0]
    if isinstance(first, dict):
        return first.get("url") or first.get("profileUrl") or first.get("profileURL") or ""
    return str(first)


def merge_item(row: dict[str, str], item: dict) -> None:
    row["apify_source_domain"] = item.get("domain", row.get("apify_source_domain", ""))
    row["apify_original_start_url"] = item.get("originalStartUrl", row.get("apify_original_start_url", ""))
    if item.get("emails"):
        row["apify_emails"] = ";".join(item["emails"])
    phones = item.get("phones") or item.get("phonesUncertain") or []
    if phones:
        row["apify_phones"] = ";".join(phones)
    if item.get("instagrams"):
        row["apify_instagram"] = first_url(item["instagrams"], "instagrams")
        followers = item["instagrams"][0].get("followersCount") if isinstance(item["instagrams"][0], dict) else ""
        if followers:
            row["apify_instagram_followers"] = str(followers)
    if item.get("facebooks"):
        row["apify_facebook"] = first_url(item["facebooks"], "facebooks")
        fb = item["facebooks"][0]
        if isinstance(fb, dict):
            if fb.get("followersCount"):
                row["apify_facebook_followers"] = str(fb["followersCount"])
            if fb.get("adStatus"):
                row["apify_facebook_ad_status"] = str(fb["adStatus"])
    if item.get("tiktoks"):
        row["apify_tiktok"] = first_url(item["tiktoks"], "tiktoks")
    found = any(is_real(row.get(c)) for c in ["apify_instagram", "apify_facebook", "apify_tiktok", "apify_emails", "apify_phones"])
    row["apify_social_status"] = "found" if found else "no_social_found"


def merge_apify_files(files: list[Path]) -> None:
    headers, rows = load_rows()
    by_domain = {domain(r.get("official_site")): r for r in rows if domain(r.get("official_site"))}
    merged = 0
    run_ids = []
    for file in files:
        run_ids.append(file.stem.removeprefix("social-media-leads-run-"))
        data = json.loads(file.read_text(encoding="utf-8"))
        for item in data if isinstance(data, list) else []:
            key = domain(item.get("originalStartUrl")) or (item.get("domain") or "").removeprefix("www.")
            row = by_domain.get(key)
            if not row:
                continue
            merge_item(row, item)
            existing = set(filter(None, (row.get("apify_run_ids") or "").split(";")))
            existing.update(run_ids)
            row["apify_run_ids"] = ";".join(sorted(existing))
            merged += 1
    write_rows(headers, rows)
    print(f"merged={merged}")


def cmd_merge_apify(args: argparse.Namespace) -> None:
    merge_apify_files([Path(p) for p in args.files])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("summary")
    p.set_defaults(func=cmd_summary)

    p = sub.add_parser("validate")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("append")
    p.add_argument("--input", required=True)
    p.add_argument("--source-seed", default="")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_append)

    p = sub.add_parser("rank")
    p.add_argument("--top", type=int, default=20)
    p.set_defaults(func=cmd_rank)

    p = sub.add_parser("apify-input")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--output", default="/tmp/stayframe-apify-input.json")
    p.set_defaults(func=cmd_apify_input)

    p = sub.add_parser("apify-run")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--timeout", type=int, default=600)
    p.set_defaults(func=cmd_apify_run)

    p = sub.add_parser("merge-apify")
    p.add_argument("files", nargs="+")
    p.set_defaults(func=cmd_merge_apify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
