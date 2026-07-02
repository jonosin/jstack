#!/usr/bin/env python3
"""Track InMail replies and conversion events against prospects.csv.

Subcommands:
  log   --lead <SEL> --outcome <O> [--text "..."] [--dir DIR]
  stats [--dir DIR]

DIR defaults to $LINKEDIN_SEND_DIR, then sys.argv positional, then cwd.
"""
import csv, json, os, sys, datetime, argparse

OUTCOMES = {"replied", "positive", "negative", "demo_sent", "call_booked", "deposit", "closed_lost"}
STATUS_COLS = ["Sent", "Reply", "DemoSent", "Call", "Deposit", "Notes"]


def resolve_dir(args_dir):
    return (args_dir
            or os.environ.get("LINKEDIN_SEND_DIR")
            or os.getcwd())


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    # ensure status cols exist (add missing ones at end)
    for col in STATUS_COLS:
        if col not in fields:
            fields.append(col)
            for r in rows:
                r.setdefault(col, "")
    return fields, rows


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def append_notes(existing, addition):
    existing = (existing or "").strip()
    addition = addition.strip()
    if not addition:
        return existing
    if existing:
        return existing + "; " + addition
    return addition


def cmd_log(args):
    d = resolve_dir(args.dir)
    csv_path = os.path.join(d, "prospects.csv")
    fields, rows = load_csv(csv_path)
    sel = args.lead.strip()

    # resolve lead: exact Row -> leadId substring -> Name substring (case-insensitive)
    matches = [r for r in rows if r.get("Row", "") == sel]
    if not matches:
        matches = [r for r in rows if sel.lower() in r.get("OpenInSalesNav", "").lower()]
    if not matches:
        matches = [r for r in rows if sel.lower() in r.get("Name", "").lower()]

    if len(matches) == 0:
        print(f"no match for lead selector: {sel!r}", file=sys.stderr)
        sys.exit(1)
    if len(matches) > 1:
        print(f"ambiguous selector {sel!r} matched {len(matches)} rows:", file=sys.stderr)
        for r in matches:
            print(f"  row {r['Row']} | {r['Name']} | {r.get('OpenInSalesNav','')}", file=sys.stderr)
        sys.exit(1)

    lead = matches[0]
    outcome = args.outcome
    text = (args.text or "").strip()[:200]

    # update status columns
    if outcome in ("replied", "positive", "negative", "closed_lost"):
        lead["Reply"] = "yes"
    if outcome == "positive":
        lead["Notes"] = append_notes(lead.get("Notes", ""), "[positive]")
    if outcome in ("negative", "closed_lost"):
        lead["Notes"] = append_notes(lead.get("Notes", ""), "[negative]")
    if outcome == "demo_sent":
        lead["DemoSent"] = "yes"
    if outcome == "call_booked":
        lead["Call"] = "yes"
    if outcome == "deposit":
        lead["Deposit"] = "yes"
    if text:
        lead["Notes"] = append_notes(lead.get("Notes", ""), text)

    write_csv(csv_path, fields, rows)

    # append to replies.jsonl
    jsonl_path = os.path.join(d, "replies.jsonl")
    event = {
        "t": datetime.datetime.now().isoformat(timespec="seconds"),
        "row": lead.get("Row", ""),
        "name": lead.get("Name", ""),
        "variant": lead.get("Variant", ""),
        "outcome": outcome,
        "text": text,
    }
    with open(jsonl_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(f"logged: row {lead['Row']} {lead['Name']} variant {lead.get('Variant','')} -> {outcome}")


def cmd_stats(args):
    d = resolve_dir(args.dir)
    csv_path = os.path.join(d, "prospects.csv")
    queue_path = os.path.join(d, "send_queue.json")
    fields, rows = load_csv(csv_path)

    # denominator: sent per variant
    sent_counts = {}
    if os.path.exists(queue_path):
        queue = json.load(open(queue_path, encoding="utf-8"))
        for entry in queue:
            if str(entry.get("sent", "")).startswith("20"):
                v = entry.get("variant", "")
                sent_counts[v] = sent_counts.get(v, 0) + 1
    else:
        for r in rows:
            if r.get("Sent", "").strip():
                v = r.get("Variant", "")
                sent_counts[v] = sent_counts.get(v, 0) + 1

    # collect all variants (from CSV rows)
    variants = []
    seen = set()
    for r in rows:
        v = r.get("Variant", "")
        if v and v not in seen:
            variants.append(v)
            seen.add(v)
    variants.sort()

    # numerators per variant from CSV status columns
    def counts_for(variant):
        subset = [r for r in rows if r.get("Variant", "") == variant]
        replies = sum(1 for r in subset if r.get("Reply", "").strip().lower() == "yes")
        positive = sum(1 for r in subset if "[positive]" in r.get("Notes", ""))
        demos = sum(1 for r in subset if r.get("DemoSent", "").strip().lower() == "yes")
        calls = sum(1 for r in subset if r.get("Call", "").strip().lower() == "yes")
        deposits = sum(1 for r in subset if r.get("Deposit", "").strip().lower() == "yes")
        return replies, positive, demos, calls, deposits

    header = f"{'Variant':<10} {'Sent':>6} {'Replies':>10} {'Positive':>10} {'Demos':>6} {'Calls':>6} {'Deposits':>9}"
    print(header)
    print("-" * len(header))

    totals = [0, 0, 0, 0, 0, 0]
    for v in variants:
        s = sent_counts.get(v, 0)
        r, pos, demos, calls, deps = counts_for(v)
        rate = f"{100*r/s:.1f}%" if s > 0 else "0.0%"
        print(f"{v:<10} {s:>6} {str(r)+' ('+rate+')':>10} {pos:>10} {demos:>6} {calls:>6} {deps:>9}")
        for i, val in enumerate([s, r, pos, demos, calls, deps]):
            totals[i] += val

    ts, tr, tpos, tdemos, tcalls, tdeps = totals
    trate = f"{100*tr/ts:.1f}%" if ts > 0 else "0.0%"
    print("-" * len(header))
    print(f"{'TOTAL':<10} {ts:>6} {str(tr)+' ('+trate+')':>10} {tpos:>10} {tdemos:>6} {tcalls:>6} {tdeps:>9}")


def main():
    parser = argparse.ArgumentParser(description="Track InMail replies")
    sub = parser.add_subparsers(dest="cmd")

    p_log = sub.add_parser("log", help="Log a reply/outcome event")
    p_log.add_argument("--lead", required=True, help="Row, leadId substring, or Name substring")
    p_log.add_argument("--outcome", required=True, choices=sorted(OUTCOMES))
    p_log.add_argument("--text", default="", help="Optional note (truncated to 200 chars)")
    p_log.add_argument("--dir", default="", help="Working dir (overrides LINKEDIN_SEND_DIR)")

    p_stats = sub.add_parser("stats", help="Print per-variant conversion stats")
    p_stats.add_argument("--dir", default="", help="Working dir (overrides LINKEDIN_SEND_DIR)")

    args = parser.parse_args()
    if args.cmd == "log":
        cmd_log(args)
    elif args.cmd == "stats":
        cmd_stats(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
