#!/usr/bin/env python3
"""register_folder.py — add a top-level folder to a venture repo AND keep its
AGENTS.md "## 2. Folder map" table in sync, deterministically.

The lean standard says a new top-level dir needs a real reason and the AGENTS.md
folder map must never be hand-edited. This script is the only sanctioned way to add
one: it creates the dir (with a .gitkeep) and inserts a row into the folder-map table.

Usage:
  register_folder.py --venture geo-optimization --path leads --desc "prospect funnels + outreach log"

  # testing override:
  register_folder.py --venture v --path leads --desc "..." --ventures-base /tmp/v
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SECTION_HDR = "## 2. Folder map"


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Register a top-level folder in a venture repo + sync its AGENTS.md folder map.")
    ap.add_argument("--venture", required=True, help="venture slug (dir under --ventures-base)")
    ap.add_argument("--path", required=True, help="top-level folder name, e.g. 'leads'")
    ap.add_argument("--desc", required=True, help="one-line description for the folder-map row")
    ap.add_argument("--ventures-base", default=str(Path.home() / "ventures"),
                    help="override ventures root (testing)")
    args = ap.parse_args()

    repo = Path(args.ventures_base).expanduser() / args.venture
    if not repo.is_dir():
        die(f"venture repo not found: {repo}")
    agents = repo / "AGENTS.md"
    if not agents.is_file():
        die(f"no AGENTS.md in {repo}")

    # keep it lean + shallow: top-level only
    folder = args.path.strip().strip("/")
    if "/" in folder:
        die(f"'{folder}' is nested — register top-level folders only (lean + shallow rule)")

    # create the dir (idempotent) with a .gitkeep so it tracks empty
    d = repo / folder
    d.mkdir(parents=True, exist_ok=True)
    keep = d / ".gitkeep"
    if not any(d.iterdir()):
        keep.write_text("")

    # update the folder-map table
    lines = agents.read_text().splitlines(keepends=True)
    try:
        start = next(i for i, ln in enumerate(lines) if ln.startswith(SECTION_HDR))
    except StopIteration:
        die(f'could not find "{SECTION_HDR}" in {agents}')
    # section ends at the next "## " header (or EOF)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))

    row_cell = f"`{folder}/`"
    # idempotency: row already present in this section
    if any(row_cell in lines[i] for i in range(start, end)):
        print(f"folder map already lists {row_cell}; dir ensured, table unchanged")
        return

    # find the last table row in the section (lines starting with "| `")
    last_row = max((i for i in range(start, end) if lines[i].lstrip().startswith("| `")),
                   default=None)
    if last_row is None:
        die("could not find the folder-map table rows to append after")
    new_row = f"| {row_cell} | {args.desc} |\n"
    lines.insert(last_row + 1, new_row)
    agents.write_text("".join(lines))
    print(f"created {d} and added folder-map row: {row_cell} — {args.desc}")


if __name__ == "__main__":
    main()
