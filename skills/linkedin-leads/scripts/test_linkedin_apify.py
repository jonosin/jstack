#!/usr/bin/env python3
"""Offline test for linkedin_apify.py — NO paid scrape is ever made.

Verifies, against frozen real sample outputs:
  1. the sync request URL/payload is built correctly for BOTH actors,
  2. dry-run curl preview never leaks the real token,
  3. the profile + post normalizers extract the expected key fields.

Run: python3 scripts/test_linkedin_apify.py   (also works under pytest)
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = HERE.parent / "references"
sys.path.insert(0, str(HERE))

# Set a dummy token so build_request/curl_preview don't exit; never a real token.
os.environ["APIFY_API_TOKEN"] = "TEST_DUMMY_TOKEN_do_not_use"

import linkedin_apify as la  # noqa: E402


def test_build_request_search():
    url, headers, payload = la.build_request("search", {"searchQuery": "Founder", "takePages": 1})
    assert "harvestapi~linkedin-profile-search/run-sync-get-dataset-items" in url
    assert headers["Content-Type"] == "application/json"
    assert json.loads(payload) == {"searchQuery": "Founder", "takePages": 1}


def test_build_request_posts_and_maxcharge():
    url, _, payload = la.build_request(
        "posts", {"targetUrls": ["https://www.linkedin.com/in/satyanadella/"], "maxPosts": 5}, max_charge=1.5
    )
    assert "harvestapi~linkedin-profile-posts/run-sync-get-dataset-items" in url
    assert "maxTotalChargeUsd=1.5" in url
    assert json.loads(payload)["maxPosts"] == 5


def test_curl_preview_does_not_leak_token():
    preview = la.curl_preview("search", {"searchQuery": "x"})
    assert "$APIFY_API_TOKEN" in preview
    assert "TEST_DUMMY_TOKEN_do_not_use" not in preview  # real token never printed


def test_normalize_profiles_on_real_sample():
    items = [json.load(open(REF / "sample_profile.json"))]
    rows = la.normalize_profiles(items)
    assert len(rows) == 1
    r = rows[0]
    assert r["name"] == "Towhid Rahman, PharmD"
    assert r["publicIdentifier"] == "towhid-rahman"
    assert r["linkedinUrl"].startswith("https://www.linkedin.com/in/")
    assert r["currentCompany"] == "CVS Health"
    assert "Los Angeles" in r["location"]
    assert isinstance(r["connectionsCount"], int)


def test_normalize_posts_on_real_sample():
    items = [json.load(open(REF / "sample_post.json"))]
    rows = la.normalize_posts(items)
    assert len(rows) == 1
    r = rows[0]
    assert r["authorName"] == "Bill Gates"
    assert r["content"].startswith("The leading causes of childhood death")
    assert r["postedDate"] == "2025-05-16T18:11:59.821Z"
    assert r["likes"] == 2916
    assert r["postUrl"].startswith("https://www.linkedin.com/posts/")


def _main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
        passed += 1
    print(f"\n{passed}/{len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
