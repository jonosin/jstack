#!/usr/bin/env python3
"""stalk_fetch.py — deterministic LinkedIn enrichment fetch for one SBA prospect.

Resolves a prospect (slug / lead ID / profile URL) against the venture registry, then runs
the OpenCLI CDP ladder against Jono's logged-in Brave (port 9222):

  1. salesnav-profile  — richest read (About, positions, education, industry) via the URN
                         built from the lead ID: urn:li:fs_salesProfile:(<leadId>,NAME_SEARCH,blank)
  2. profile-read      — public-profile read; also resolves /in/<leadId> -> canonical vanity URL
  3. posts             — top-N visible posts from the canonical profile activity page

Each rung is independent: a failure is recorded in meta.failures and the ladder continues.
Output: one normalized JSON bundle (default clients/<slug>/stalk-raw.json when --slug given).

Exit codes: 0 ok (>=1 rung succeeded) · 66 nothing retrievable · 69 CDP preflight failed ·
2 bad arguments / prospect not found.
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

OPENCLI = Path.home() / ".claude/skills/jstack-opencli/scripts/opencli-cdp.sh"
CDP_PROBE = "http://localhost:9222/json/version"
LEAD_ID_RE = re.compile(r"/sales/(?:people|lead)/([A-Za-z0-9_\-]+)")
IN_URL_RE = re.compile(r"linkedin\.com/in/([^/?#,]+)")


def venture_root() -> Path:
    v = os.environ.get("SBA_VENTURE")
    if not v:
        cfg = Path.home() / ".jstack/config.env"
        if cfg.exists():
            for line in cfg.read_text().splitlines():
                m = re.match(r"\s*(?:export\s+)?SBA_VENTURE=(.+)", line)
                if m:
                    v = m.group(1).strip().strip("'\"")
    return Path(os.path.expanduser(v)) if v else Path.home() / "ventures/second-brain-agency"


def cdp_preflight() -> bool:
    try:
        subprocess.run(
            ["curl", "-fsS", "--max-time", "5", CDP_PROBE],
            check=True, capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def parse_json_out(raw: str):
    """opencli prints a JSON array, sometimes followed by an update banner — slice it out."""
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON array in output")
    return json.loads(raw[start : end + 1])


def opencli(args: list[str], timeout: int = 150):
    """Run one opencli linkedin command. Returns (rows, error_string)."""
    cmd = [str(OPENCLI), "linkedin", *args, "-f", "json"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, f"timeout after {timeout}s"
    out = p.stdout or ""
    if p.returncode != 0:
        blob = (out + "\n" + (p.stderr or "")).strip()
        m = re.search(r"message: ?'?([^'\n]+)'?", blob)
        return None, m.group(1) if m else blob[:300]
    try:
        return parse_json_out(out), None
    except ValueError as e:
        return None, f"{e}: {out[:200]}"


def resolve_from_registry(root: Path, slug=None, lead=None, url=None, row=None):
    """Find the prospect row in prospects/prospects.csv. Returns dict or None."""
    reg = root / "prospects/prospects.csv"
    if not reg.exists():
        return None
    slug_tokens = set(slug.lower().replace("-", " ").split()) if slug else None
    with reg.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if row and r.get("Row") == str(row):
                return r
            if slug and r.get("ClientFolder", "").strip().lower() == f"clients/{slug.lower()}":
                return r
            if lead and lead in r.get("OpenInSalesNav", ""):
                return r
            if url:
                m = IN_URL_RE.search(url)
                if m and m.group(1).lower() in r.get("OpenProfile", "").lower():
                    return r
            if slug_tokens:
                biz = set(re.sub(r"[^a-z0-9 ]", " ", r.get("Business", "").lower()).split())
                if slug_tokens and slug_tokens <= biz:
                    return r
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", help="client folder slug (clients/<slug>) — preferred input")
    ap.add_argument("--lead", help="Sales Navigator lead ID (ACwAA…/ACoAA…) or sales/people URL")
    ap.add_argument("--url", help="public linkedin.com/in/<handle> profile URL")
    ap.add_argument("--row", help="prospects.csv Row number")
    ap.add_argument("--posts", type=int, default=3, help="max posts to pull (default 3)")
    ap.add_argument("--skip-salesnav", action="store_true", help="skip the salesnav-profile rung")
    ap.add_argument("--skip-posts", action="store_true", help="skip the posts rung")
    ap.add_argument("--out", help="output path (default clients/<slug>/stalk-raw.json, else stdout)")
    a = ap.parse_args()

    if not (a.slug or a.lead or a.url or a.row):
        ap.error("need one of --slug / --lead / --url / --row")

    root = venture_root()
    reg_row = resolve_from_registry(root, slug=a.slug, lead=a.lead, url=a.url, row=a.row)
    if not reg_row and not (a.lead or a.url):
        print(f"prospect not found in {root}/prospects/prospects.csv", file=sys.stderr)
        sys.exit(2)

    lead_id = None
    public_url = None
    if a.lead:
        m = LEAD_ID_RE.search(a.lead)
        lead_id = m.group(1) if m else a.lead
    if a.url:
        public_url = a.url
    if reg_row:
        if not lead_id:
            m = LEAD_ID_RE.search(reg_row.get("OpenInSalesNav", "") or "")
            lead_id = m.group(1) if m else None
        if not public_url:
            op = (reg_row.get("OpenProfile", "") or "").strip()
            if op.startswith("http") and "/in/" in op:
                public_url = op.rstrip("/") + "/"

    if not cdp_preflight():
        print("CDP preflight failed: Brave is not exposing :9222 — run the brave-cdp skill "
              "(brave-cdp-relaunch) and retry.", file=sys.stderr)
        sys.exit(69)

    bundle = {
        "resolved": {
            "slug": a.slug,
            "lead_id": lead_id,
            "public_url": public_url,
            "registry_row": {k: reg_row.get(k) for k in
                             ("Row", "Name", "Business", "Country", "Tier", "Variant",
                              "Round", "ClientFolder", "Reply", "Notes")} if reg_row else None,
        },
        "salesnav_profile": None,
        "profile": None,
        "posts": None,
        "meta": {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S %z"), "failures": {}},
    }

    # Rung 1 — salesnav-profile (needs an active Sales Navigator subscription)
    if lead_id and not a.skip_salesnav:
        urn = f"urn:li:fs_salesProfile:({lead_id},NAME_SEARCH,blank)"
        rows, err = opencli(["salesnav-profile", urn])
        if rows:
            bundle["salesnav_profile"] = rows[0]
        else:
            bundle["meta"]["failures"]["salesnav_profile"] = err

    # Rung 2 — profile-read; /in/<leadId> 301s to the canonical vanity URL when logged in
    probe_url = public_url or (f"https://www.linkedin.com/in/{lead_id}/" if lead_id else None)
    if probe_url:
        rows, err = opencli(["profile-read", "--profile-url", probe_url])
        if rows:
            bundle["profile"] = rows[0]
            canon = rows[0].get("profile_url")
            if canon and "/in/" in canon:
                bundle["resolved"]["canonical_url"] = canon
        else:
            bundle["meta"]["failures"]["profile_read"] = err

    # Rung 3 — posts from the canonical activity page
    posts_url = bundle["resolved"].get("canonical_url") or probe_url
    if posts_url and not a.skip_posts:
        rows, err = opencli(["posts", "--profile-url", posts_url, "--limit", str(a.posts)],
                            timeout=200)
        if rows is not None:
            bundle["posts"] = rows
        else:
            bundle["meta"]["failures"]["posts"] = err  # EMPTY_RESULT = no visible posts (common)

    got = [k for k in ("salesnav_profile", "profile", "posts") if bundle.get(k)]
    out_path = a.out
    if not out_path and a.slug:
        out_path = str(root / "clients" / a.slug / "stalk-raw.json")
    payload = json.dumps(bundle, indent=1, ensure_ascii=False)
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(payload + "\n", encoding="utf-8")
        print(f"wrote {out_path}", file=sys.stderr)
    else:
        print(payload)

    name = (bundle.get("salesnav_profile") or {}).get("name") or (bundle.get("profile") or {}).get("name")
    n_posts = len(bundle["posts"]) if bundle.get("posts") else 0
    print(f"got: {', '.join(got) or 'nothing'} | name: {name} | posts: {n_posts}"
          f"{' | failures: ' + ', '.join(bundle['meta']['failures']) if bundle['meta']['failures'] else ''}",
          file=sys.stderr)
    sys.exit(0 if got else 66)


if __name__ == "__main__":
    main()
