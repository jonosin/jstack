#!/usr/bin/env python3
"""linkedin_apify.py — deterministic runner for HarvestAPI's LinkedIn Apify actors.

Two actors, one tool:
  search  -> harvestapi~linkedin-profile-search   find / enrich LinkedIn profiles by filters
  posts   -> harvestapi~linkedin-profile-posts     pull a profile's or company's recent posts

Both actors are PAY-PER-RESULT. To prevent an accidental paid scrape, every run
command DEFAULTS to --dry-run: it prints the exact curl + JSON it *would* send and
exits without calling Apify. Pass --execute to actually run the synchronous call.

Auth: reads APIFY_API_TOKEN from the environment (load it first, see SKILL.md).
The token is NEVER printed — dry-run previews use the literal "$APIFY_API_TOKEN".

Usage:
  linkedin_apify.py auth
  linkedin_apify.py search  --input '{"searchQuery":"Founder","profileScraperMode":"Short","takePages":1}'
  linkedin_apify.py posts   --input '{"targetUrls":["https://www.linkedin.com/in/satyanadella/"],"maxPosts":5}'
  linkedin_apify.py search  --input-file in.json --execute --max-charge 1.00 --out items.json
  linkedin_apify.py normalize-profiles items.json
  linkedin_apify.py normalize-posts    items.json
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

API_BASE = "https://api.apify.com/v2"

# Actor id -> path slug (tilde form used in API URLs)
ACTORS = {
    "search": "harvestapi~linkedin-profile-search",
    "posts": "harvestapi~linkedin-profile-posts",
}


def _token():
    tok = os.environ.get("APIFY_API_TOKEN", "").strip()
    if not tok:
        sys.exit("APIFY_API_TOKEN is not set. Load env first (see SKILL.md), then retry.")
    return tok


def run_sync_url(actor_slug, token):
    return f"{API_BASE}/acts/{actor_slug}/run-sync-get-dataset-items?token={token}"


def build_request(actor, input_obj, max_charge=None):
    """Return (url_with_real_token, headers, payload_bytes) for the sync call.

    actor: 'search' | 'posts'. Raises KeyError on unknown actor.
    max_charge: optional float; sent as the run query param maxTotalChargeUsd (hard cost cap).
    """
    slug = ACTORS[actor]
    url = run_sync_url(slug, _token())
    if max_charge is not None:
        url += f"&maxTotalChargeUsd={max_charge}"
    payload = json.dumps(input_obj).encode("utf-8")
    return url, {"Content-Type": "application/json"}, payload


def curl_preview(actor, input_obj, max_charge=None):
    """Copy-pasteable curl with the token kept as the literal $APIFY_API_TOKEN (no leak)."""
    slug = ACTORS[actor]
    url = f'{API_BASE}/acts/{slug}/run-sync-get-dataset-items?token=$APIFY_API_TOKEN'
    if max_charge is not None:
        url += f"&maxTotalChargeUsd={max_charge}"
    body = json.dumps(input_obj, indent=2)
    return (
        f'curl -sS "{url}" \\\n'
        f"  -H \"Content-Type: application/json\" \\\n"
        f"  -d '{body}'"
    )


def execute_run(actor, input_obj, max_charge=None, timeout=600):
    url, headers, payload = build_request(actor, input_obj, max_charge)
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"Apify HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:500]}")


def auth_check():
    url = f"{API_BASE}/users/me?token={_token()}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8")).get("data", {})
        print(f"OK — Apify auth verified. username={data.get('username')} plan={(data.get('plan') or {}).get('id')}")
        return 0
    except urllib.error.HTTPError as e:
        print(f"AUTH FAILED — HTTP {e.code}", file=sys.stderr)
        return 1


# ---------- normalizers: dataset item -> flat prospecting row ----------

def normalize_profiles(items):
    out = []
    for p in items:
        loc = (p.get("location") or {}).get("linkedinText")
        cur = (p.get("currentPosition") or [{}])
        cur0 = cur[0] if cur else {}
        out.append({
            "name": " ".join(x for x in [p.get("firstName"), p.get("lastName")] if x).strip() or None,
            "headline": p.get("headline"),
            "linkedinUrl": p.get("linkedinUrl"),
            "publicIdentifier": p.get("publicIdentifier"),
            "location": loc,
            "currentCompany": cur0.get("companyName"),
            "currentCompanyUrl": cur0.get("companyLinkedinUrl"),
            "topSkills": p.get("topSkills"),
            "connectionsCount": p.get("connectionsCount"),
            "followerCount": p.get("followerCount"),
            "openToWork": p.get("openToWork"),
            "email": p.get("email"),  # present only in "Full + email search" mode
        })
    return out


def normalize_posts(items):
    out = []
    for post in items:
        author = post.get("author") or {}
        posted = post.get("postedAt") or {}
        eng = post.get("engagement") or {}
        out.append({
            "postUrl": post.get("linkedinUrl"),
            "type": post.get("type"),
            "authorName": author.get("name"),
            "authorUrl": author.get("linkedinUrl"),
            "authorPublicIdentifier": author.get("publicIdentifier"),
            "content": post.get("content"),
            "postedDate": posted.get("date"),
            "likes": eng.get("likes"),
            "comments": eng.get("comments"),
            "shares": eng.get("shares"),
        })
    return out


# ---------- CLI ----------

def _load_input(args):
    if args.input_file:
        with open(args.input_file) as f:
            return json.load(f)
    if args.input:
        return json.loads(args.input)
    sys.exit("Provide --input '<json>' or --input-file <path>.")


def _run_cmd(actor, args):
    input_obj = _load_input(args)
    if not args.execute:
        print(f"# DRY-RUN ({actor}) — pay-per-result; nothing was sent. Add --execute to run.\n")
        print(curl_preview(actor, input_obj, args.max_charge))
        return 0
    items = execute_run(actor, input_obj, args.max_charge)
    text = json.dumps(items, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"Wrote {len(items)} items -> {args.out}")
    else:
        print(text)
    return 0


def _normalize_cmd(kind, path):
    with open(path) as f:
        items = json.load(f)
    if not isinstance(items, list):
        items = [items]
    rows = normalize_profiles(items) if kind == "profiles" else normalize_posts(items)
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth", help="Verify APIFY_API_TOKEN (free GET /users/me)")

    for name in ("search", "posts"):
        sp = sub.add_parser(name, help=f"Run the {name} actor (dry-run by default)")
        sp.add_argument("--input", help="JSON input string")
        sp.add_argument("--input-file", help="Path to JSON input file")
        sp.add_argument("--execute", action="store_true", help="Actually send the PAID sync call")
        sp.add_argument("--max-charge", type=float, default=None,
                        help="Hard cost cap in USD (maxTotalChargeUsd)")
        sp.add_argument("--out", help="Write returned dataset items to this file")

    np_ = sub.add_parser("normalize-profiles", help="Flatten profile dataset items to prospecting rows")
    np_.add_argument("path", help="JSON file of dataset items")
    nq = sub.add_parser("normalize-posts", help="Flatten post dataset items to prospecting rows")
    nq.add_argument("path", help="JSON file of dataset items")

    args = ap.parse_args(argv)
    if args.cmd == "auth":
        return auth_check()
    if args.cmd in ("search", "posts"):
        return _run_cmd(args.cmd, args)
    if args.cmd == "normalize-profiles":
        return _normalize_cmd("profiles", args.path)
    if args.cmd == "normalize-posts":
        return _normalize_cmd("posts", args.path)
    return 1


if __name__ == "__main__":
    sys.exit(main())
