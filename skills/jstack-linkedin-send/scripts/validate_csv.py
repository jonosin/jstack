#!/usr/bin/env python3
"""Pre-send gate: validate prospects.csv before building the send queue.

Usage: python3 validate_csv.py [--dir DIR]
DIR defaults to $LINKEDIN_SEND_DIR or cwd.
Exits nonzero if any FAIL checks are found.
"""
import csv, os, sys, re, argparse, collections

REQUIRED_COLS = ["Row", "Variant", "Name", "OpenInSalesNav", "Subject", "Message"]
SALESNAV_PAT = re.compile(r"/sales/(people|search)/")


def main():
    parser = argparse.ArgumentParser(description="Validate prospects.csv before sending")
    parser.add_argument("--dir", default="", help="Working dir (overrides LINKEDIN_SEND_DIR)")
    args = parser.parse_args()

    d = args.dir or os.environ.get("LINKEDIN_SEND_DIR") or os.getcwd()
    csv_path = os.path.join(d, "prospects.csv")

    if not os.path.exists(csv_path):
        print(f"FAIL: {csv_path} not found")
        sys.exit(1)

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    problems = []
    warnings = []

    # 1) required columns
    missing_cols = [c for c in REQUIRED_COLS if c not in fields]
    if missing_cols:
        problems.append(f"missing required columns: {missing_cols}")

    # 2) row count
    print(f"rows: {len(rows)}")

    # 3) per-row checks (only if required cols present)
    if not missing_cols:
        seen_rows = {}
        variant_counts = collections.Counter()

        for i, r in enumerate(rows, 1):
            row_id = r.get("Row", "").strip()
            variant = r.get("Variant", "").strip()
            name = r.get("Name", "").strip()
            nav = r.get("OpenInSalesNav", "").strip()
            subject = r.get("Subject", "").strip()
            message = r.get("Message", "").strip()

            # Row unique + non-empty
            if not row_id:
                problems.append(f"line {i}: Row is empty")
            elif row_id in seen_rows:
                problems.append(f"duplicate Row={row_id!r} (lines {seen_rows[row_id]} and {i})")
            else:
                seen_rows[row_id] = i

            # OpenInSalesNav pattern
            if not nav:
                problems.append(f"row {row_id}: OpenInSalesNav is empty")
            elif not SALESNAV_PAT.search(nav):
                warnings.append(f"row {row_id}: OpenInSalesNav does not contain /sales/people/ or /sales/search/: {nav!r}")

            # Subject non-empty
            if not subject:
                problems.append(f"row {row_id}: Subject is empty")

            # Message >= 50 chars
            if len(message) < 50:
                problems.append(f"row {row_id}: Message too short ({len(message)} chars, need >= 50)")

            # Variant non-empty
            if not variant:
                problems.append(f"row {row_id}: Variant is empty")
            else:
                variant_counts[variant] += 1

        # variant distribution
        if variant_counts:
            dist = ", ".join(f"{v}={c}" for v, c in sorted(variant_counts.items()))
            print(f"variants: {dist}")

    # report
    for w in warnings:
        print(f"WARN: {w}")
    for p in problems:
        print(f"FAIL: {p}")

    if problems:
        print(f"FAIL ({len(problems)} problem(s) found)")
        sys.exit(1)
    else:
        print("PASS")


if __name__ == "__main__":
    main()
