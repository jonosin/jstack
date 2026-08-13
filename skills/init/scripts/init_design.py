#!/usr/bin/env python3
"""init_design.py — deterministically initialize a DESIGN.md design system in a repo.

This is the baked-in mechanizable core of the deprecated ggdesign-init skill.
It copies the starter DESIGN.md template into a repo, wires the repo's AGENTS.md to
read it, and (optionally) lints + exports tokens via @google/design.md.

Network steps soft-fail: scaffold determinism must NOT depend on npx/network.

Usage:
  init_design.py --repo ~/builds/my-app
  init_design.py --repo ~/builds/my-app --force            # overwrite existing DESIGN.md
  init_design.py --repo ~/builds/my-app --no-lint
  init_design.py --repo ~/builds/my-app --tailwind v4      # also export tokens
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# templates / constants
# ---------------------------------------------------------------------------

STARTER = Path(__file__).parent / ".." / "references" / "design" / "starter.md"

DESIGN_SECTION_HDR = "## Design system"

DESIGN_SECTION = """
## Design system

Read `DESIGN.md` at the repo root before producing any UI/frontend output. Apply all tokens — colors,
typography, spacing, components — and follow the prose rationale for taste and do's/don'ts.
"""


# ---------------------------------------------------------------------------
# helpers (copied from new_venture.py to keep this script self-contained)
# ---------------------------------------------------------------------------

def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def info(msg: str) -> None:
    print(msg)


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


# ---------------------------------------------------------------------------
# steps
# ---------------------------------------------------------------------------

def copy_starter(repo: Path, force: bool) -> None:
    starter = STARTER.resolve()
    if not starter.is_file():
        die(f"starter template not found: {starter}")
    dest = repo / "DESIGN.md"
    if dest.exists() and not force:
        info(f"skip: DESIGN.md already exists (use --force to overwrite): {dest}")
        return
    dest.write_text(starter.read_text())
    info(f"ok: wrote DESIGN.md ({'overwrote' if force else 'created'}): {dest}")


def wire_agents(repo: Path) -> None:
    agents = repo / "AGENTS.md"
    if agents.is_file():
        text = agents.read_text()
        if DESIGN_SECTION_HDR in text:
            info(f"skip: AGENTS.md already has a '{DESIGN_SECTION_HDR}' section")
            return
        if not text.endswith("\n"):
            text += "\n"
        agents.write_text(text + DESIGN_SECTION)
        info(f"ok: appended '{DESIGN_SECTION_HDR}' section to AGENTS.md")
    else:
        agents.write_text(DESIGN_SECTION.lstrip("\n"))
        info(f"ok: created AGENTS.md with '{DESIGN_SECTION_HDR}' section")


def lint(repo: Path) -> None:
    try:
        r = run(["npx", "-y", "@google/design.md", "lint", "DESIGN.md"], cwd=repo)
    except (FileNotFoundError, OSError) as e:
        info(f"warn: lint skipped (npx unavailable): {e}")
        return
    out = (r.stdout.strip() + "\n" + r.stderr.strip()).strip()
    if r.returncode == 0:
        info("ok: design.md lint passed")
    else:
        info(f"warn: design.md lint reported issues (exit {r.returncode}) — review DESIGN.md")
    if out:
        info(out)


def export_tailwind(repo: Path, flavor: str) -> None:
    fmt = "tailwind" if flavor == "v3" else "css-tailwind"
    try:
        r = run(["npx", "-y", "@google/design.md", "export", "DESIGN.md", "--format", fmt], cwd=repo)
    except (FileNotFoundError, OSError) as e:
        info(f"warn: tailwind export skipped (npx unavailable): {e}")
        return
    if r.returncode == 0:
        info(f"ok: exported tokens (--format {fmt}) — stdout below; redirect to a file to persist")
        if r.stdout.strip():
            info(r.stdout.strip())
    else:
        info(f"warn: tailwind export failed (exit {r.returncode})")
        if r.stderr.strip():
            info(r.stderr.strip())


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Initialize a DESIGN.md design system in a repo.")
    ap.add_argument("--repo", required=True, help="path to the repo root")
    ap.add_argument("--force", action="store_true", help="overwrite an existing DESIGN.md")
    ap.add_argument("--no-lint", action="store_true", help="skip the npx design.md lint")
    ap.add_argument("--tailwind", choices=["none", "v3", "v4"], default="none",
                    help="export tokens to Tailwind (v3=theme json, v4=css custom props)")
    args = ap.parse_args()

    repo = Path(args.repo).expanduser()
    if not repo.is_dir():
        die(f"--repo is not a directory: {repo}")

    copy_starter(repo, args.force)
    wire_agents(repo)
    if args.no_lint:
        info("skip: lint (--no-lint)")
    else:
        lint(repo)
    if args.tailwind != "none":
        export_tailwind(repo, args.tailwind)

    print()
    print("DONE — design system initialized")
    print(f"  DESIGN.md: {repo / 'DESIGN.md'}")
    print("Next (human/agent judgment — NOT deterministic):")
    print("  - Fill in the starter placeholders: brand name, colors, fonts, voice/feel.")
    print("  - Replace the MyBrand defaults with the real palette + typography, then re-lint.")


if __name__ == "__main__":
    main()
