#!/usr/bin/env python3
"""Safely rebuild send_queue.json from prospects.csv WITHOUT losing send state.

Run this AFTER editing copy (subject/message) in your prospects.csv.
The authoritative record of what was already sent lives in the EXISTING
send_queue.json `sent` field. This script:
  1. reads the existing send_queue.json -> sent-state by Row (preserves '... sent (credit/free)'
     and 'skip:...' markers so we never re-send or re-skip),
  2. reads the freshly-built prospects.csv -> new copy (subject/message) for every row,
  3. writes send_queue.json with NEW copy but PRESERVED sent-state,
  4. re-syncs prospects.csv Sent column from the merged queue (so the display sheet is correct).

Idempotent. Safe to run repeatedly.

Usage: python3 rebuild_send_queue.py [DIR]
       DIR defaults to $LINKEDIN_SEND_DIR or cwd.
       LINKEDIN_SEND_TIERS=A,B restricts to those tiers (default: all rows).
"""
import csv, json, re, os, sys

DIR = os.environ.get("LINKEDIN_SEND_DIR") or (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else os.getcwd())
CSV = os.path.join(DIR, "prospects.csv")
QUEUE = os.path.join(DIR, "send_queue.json")

# 1) preserve sent-state from existing queue (by Row)
sent_by_row = {}
if os.path.exists(QUEUE):
    for x in json.load(open(QUEUE)):
        if x.get("sent"):
            sent_by_row[str(x["row"])] = x["sent"]

# 2) fresh rows from prospects.csv, optionally filtered by tier
rows = list(csv.DictReader(open(CSV)))
fields = list(rows[0].keys())
tiers = os.environ.get("LINKEDIN_SEND_TIERS")
tiers = [t.strip() for t in tiers.split(",")] if tiers else None
A = [r for r in rows if (tiers is None or r.get("Tier","") in tiers)]
q = []
for r in A:
    m = re.search(r"/sales/people/([A-Za-z0-9_-]+)", r["OpenInSalesNav"])
    q.append({
        "row": r["Row"], "leadId": m.group(1) if m else "", "name": r["Name"],
        "firstName": r["FirstName"], "business": r["Business"], "variant": r["Variant"],
        "salesNav": r["OpenInSalesNav"], "openProfile_url": r["OpenProfile"],
        "subject": r["Subject"], "message": r["Message"],
        "sent": sent_by_row.get(r["Row"], ""),   # PRESERVED
    })
json.dump(q, open(QUEUE, "w"), indent=2, ensure_ascii=False)

# 3) re-sync prospects.csv Sent column from merged queue
qsent = {x["row"]: x["sent"] for x in q if x["sent"]}
for r in rows:
    if r["Row"] in qsent:
        r["Sent"] = qsent[r["Row"]]
w = csv.DictWriter(open(CSV, "w", newline=""), fieldnames=fields)
w.writeheader(); w.writerows(rows)

done = [x for x in q if x["sent"] and x["sent"][:2] == "20"]
skip = [x for x in q if x["sent"] and x["sent"].startswith("skip")]
unsent = [x for x in q if not x["sent"]]
print(f"rebuilt send_queue.json: {len(q)} rows | already-sent {len(done)} | skipped {len(skip)} | unsent {len(unsent)}")
if unsent:
    print(f"  next unsent: row {unsent[0]['row']} ({unsent[0]['name']}) .. row {unsent[-1]['row']}")
