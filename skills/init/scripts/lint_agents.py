#!/usr/bin/env python3
"""lint_agents.py — type-aware size-cap lint for AGENTS.md router files.

Mirrors the brain's `hot.md <= 50` gate idea: a router file is a pointer, not a home
for content. Ventures cap at 120 lines, builds at 200 (builds carry coding guidelines).
Over-cap means content should move to the brain or a skill.

Usage:
  lint_agents.py                                  # scan ~/ventures/*/AGENTS.md + ~/builds/*/AGENTS.md
  lint_agents.py --cap-venture 120 --cap-build 200
  lint_agents.py ~/builds/foo/AGENTS.md           # lint exactly these files
  lint_agents.py --ventures-base /tmp/v --builds-base /tmp/b   # override glob roots (testing)

Exit 0 if all within cap; exit 1 if any over cap.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def info(msg: str) -> None:
    print(msg)


def count_lines(path: Path) -> int:
    return len(path.read_text().splitlines())


def cap_for(path: Path, cap_venture: int, cap_build: int) -> int:
    s = str(path)
    if "/builds/" in s:
        return cap_build
    if "/ventures/" in s:
        return cap_venture
    return cap_venture  # default


def main() -> int:
    ap = argparse.ArgumentParser(description="Size-cap lint for AGENTS.md router files.")
    ap.add_argument("paths", nargs="*", help="explicit AGENTS.md files to lint (default: scan the roots)")
    ap.add_argument("--cap-venture", type=int, default=120, help="line cap for venture routers")
    ap.add_argument("--cap-build", type=int, default=200, help="line cap for build routers")
    ap.add_argument("--ventures-base", default=str(Path.home() / "ventures"),
                    help="override ventures glob root (testing)")
    ap.add_argument("--builds-base", default=str(Path.home() / "builds"),
                    help="override builds glob root (testing)")
    args = ap.parse_args()

    if args.paths:
        files = [Path(p).expanduser() for p in args.paths]
    else:
        ventures_base = Path(args.ventures_base).expanduser()
        builds_base = Path(args.builds_base).expanduser()
        files = sorted(ventures_base.glob("*/AGENTS.md")) + sorted(builds_base.glob("*/AGENTS.md"))

    if not files:
        info("no AGENTS.md files found to lint")
        return 0

    over = 0
    for f in files:
        if not f.is_file():
            info(f"MISSING {f} — not a file")
            over += 1
            continue
        n = count_lines(f)
        cap = cap_for(f, args.cap_venture, args.cap_build)
        if n <= cap:
            info(f"OK {f} ({n}/{cap})")
        else:
            info(f"OVER {f} ({n}/{cap}) — move content to the brain or a skill")
            over += 1

    info(f"\n{len(files)} file(s) checked, {over} over cap")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
