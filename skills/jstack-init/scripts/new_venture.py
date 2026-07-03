#!/usr/bin/env python3
"""new_venture.py — deterministically scaffold a lean venture repo AND wire it into
the second brain.

The lean venture standard (reference impl: ~/ventures/geo-optimization) is:

  ~/ventures/<slug>/
    AGENTS.md              # thin brain-routing router: identical MECHANICS + a venture-specific PERSONA
    CLAUDE.md -> AGENTS.md # symlink
    BRAIN.md              # satellite pointer back to the brain
    .gitignore
    docs/
      decisions.md         # append-only operational log (seeded header)
      scratch/.gitkeep
      superpowers/specs/.gitkeep
      superpowers/adr/.gitkeep
    clients/.gitkeep
    assets/.gitkeep

Brain side (this coupling is the whole point — it ALWAYS happens):
  - create wiki/personal/ventures/<slug>.md hub stub (warn-not-overwrite)
  - add a row to wiki/maps/satellites.md
  - run sb.py index, append sb.py log (init-venture), run sb.py check

Determinism: all mechanics live here. The agent supplies judgment (the persona
paragraph). Idempotency: refuses if ~/ventures/<slug>/ already exists.

Usage:
  new_venture.py --name "GEO Optimization" --slug geo-optimization \
      --desc "one-line description" --persona "the persona paragraph"

  # override roots for testing (no clobber of real dirs):
  new_venture.py ... --ventures-base /tmp/v --brain /tmp/brain --no-git
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# templates
# ---------------------------------------------------------------------------

AGENTS_TMPL = """# {name} — venture router (agents)

> Built for agents. Jono does not read this repo. Terse + machine-parseable.
> **Purpose:** a work-product *router* for this venture — not a software build repo (code builds live
> in `~/builds`), not the knowledge base (that is the brain, §1). It carries pointers + operating rules
> only. If you are tempted to write a fact about *what this venture is or does*, it belongs in the
> brain, not this file.

## 0. Persona + the one ritual

{persona}

Ritual (every venture, every session): when a strategic decision reshapes this venture, write a
two-sentence summary of *what this venture has become* and capture it to the brain
(`/jstack-savetobrain` → hub `{slug}.md`). Decide strategy in conversation; it lives in the brain,
never in this file.

## 1. Where venture context lives — read the brain, not this file

This repo holds **work product only**. Anything venture-specific (what we sell, who we sell to,
pricing, the offer, positioning, decisions, the *why*) lives in the **second brain**:

- knowledge_home: `{knowledge_home}`
- Need a venture fact? **Read it there.** Never restate brain knowledge in this repo. Link, don't duplicate.

## 2. Folder map

| Path | What |
|---|---|
| `docs/scratch/` | agent drop zone: brainstorms, working notes, superpower ideas (ephemeral) |
| `docs/superpowers/` | durable plans: `specs/` + `adr/` (global planning-doc convention) |
| `docs/decisions.md` | append-only operational decision log (durable *why* routes to the brain) |
| `clients/<slug>/` | one folder per client/prospect — all work product for that account |
| `assets/` | creatives, exports, downloads tied to the venture |

Adding a top-level folder needs a real reason (keep the tree lean + shallow, avoid nesting). Do it
deterministically so this table stays in sync — **never hand-edit the table**:

    python3 ~/jstack/skills/jstack-init/scripts/register_folder.py --venture {slug} --path <name> --desc "<one line>"

## 3. Operating principles (identical across every venture)

- **brain ⊥ satellite.** Brain = knowledge (decisions, research, the why). This repo = the artifacts
  those decisions produce. Never duplicate one into the other — **link**.
- **Capture:** a durable decision/fact surfaces here → `/jstack-savetobrain` (compiled later by
  `/jstack-brainwork`). **Never write `~/second-brain/wiki/` from inside this repo.**
- **Planning docs** (specs/designs/ADRs) → `docs/superpowers/` (global standard).
- **Lean + shallow:** minimal top-level dirs, avoid nesting. Context belongs in the brain, not new folders.
- **Keep this router current — gated.** When the repo's structure or operating mechanics change, update
  this file in the *same* change (add folders via `register_folder.py`; fix routing/pointers inline).
  Before adding any line ask: *is this a durable operating rule needed every session?* If it's a
  procedure, template, research note, or strategy decision, put it in the brain / a skill / a playbook
  and **link it** instead. Propose structural edits; never absorb strategy.
- **Hard size cap (~120 lines).** If this router grows past ~120 lines, something belongs in the brain
  or a skill — move it out. Check: `python3 ~/jstack/skills/jstack-init/scripts/lint_agents.py`.
- **Cold start:** read `BRAIN.md` → `knowledge_home` in the brain for everything venture-specific.
"""

BRAIN_TMPL = """# BRAIN.md — second-brain pointer

This repo is a **satellite** of the owner's second brain. Knowledge (decisions, research, durable
facts) lives in the brain; this repo holds the work product. Link, don't duplicate.

- brain_path: ~/second-brain
- knowledge_home: wiki/personal/ventures/{slug}.md   # this venture's hub page in the brain
- read_order: ~/second-brain/AGENTS.md → wiki/hot.md → wiki/index.md → knowledge_home → [[wikilinks]]
- capture_rule: durable decision/fact here → /jstack-savetobrain (never write ~/second-brain/wiki/ from here)
- link_rule: cite brain pages by path; the brain page may point back here via a `workspace:` field

A cold agent in this repo that needs a brain-resident fact: read `knowledge_home` (and what it links)
under `brain_path`. The brain's satellite registry — `~/second-brain/wiki/maps/satellites.md` — lists
every sibling repo.
"""

DECISIONS_TMPL = """# Operational decision log — {name}

Append-only. One line per operational decision (tooling, process, repo mechanics). **Durable strategic
decisions (offer, pricing, positioning, the *why*) do NOT live here — capture them to the brain via
`/jstack-savetobrain`.** This log is for repo/execution choices, newest at top.

| Date | Decision | Why |
|---|---|---|
| {today} | Scaffolded `{name}` as a lean venture repo (jstack-init). | New venture spun up; standard lean tree + brain coupling (hub page + satellite registry). |
"""

GITIGNORE_TMPL = """.DS_Store
.env
*.local
node_modules/
__pycache__/
*.pyc
.playwright-mcp/
"""

# Generic operating disposition — NOT venture strategy. Strategy lives in the brain.
DEFAULT_PERSONA = (
    "Operate this venture as a lean strategic partner: decisive, honest about tradeoffs, biased to "
    "the smallest action that creates real signal, allergic to bloat and busywork. You are a thinking "
    "partner, not a yes-machine — push back when something seems off."
)

HUB_TMPL = """---
type: personal-venture
title: "{name}"
summary: "{one_liner} Work product: ~/ventures/{slug}/. Hub stub created {today} via jstack-init; durable decisions land here via /jstack-savetobrain → /jstack-brainwork."
created: {today}
updated: {today}
tags: [venture, {slug}]
workspace: ~/ventures/{slug}/
---
# {name} — venture hub

> **Knowledge home** for the {name} venture. This page is the brain-side context the satellite repo's
> `AGENTS.md` routes to. Hub stub created {today} on scaffold; durable decisions land here via
> `/jstack-savetobrain` → `/jstack-brainwork`.

## What it is
{one_liner}

## Why it exists (the bet)
TODO — capture the thesis/why via `/jstack-savetobrain` (do not hand-write venture canon here).

## Status
- {today}: scaffolded as a [[../../maps/satellites|satellite repo]] `~/ventures/{slug}/` (lean venture standard).
- GTM strategy is open work (route via `/jstack-gtm`).

## Satellite
Work product repo `~/ventures/{slug}/` (`BRAIN.md` points back here). Registry:
[[../../maps/satellites|Satellite Registry]].
"""

# satellites.md row (added to the registry table)
SAT_ROW_TMPL = (
    "| `~/ventures/{slug}` (**{name}** — {short}) "
    "| `wiki/personal/ventures/{slug}.md` | yes |\n"
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def info(msg: str) -> None:
    print(msg)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def gitkeep(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / ".gitkeep").write_text("")


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


# ---------------------------------------------------------------------------
# repo scaffold
# ---------------------------------------------------------------------------

def scaffold_repo(repo: Path, name: str, slug: str, one_liner: str, persona: str,
                  knowledge_home: str, today: str, do_git: bool) -> None:
    # exact lean tree — no extra folders
    repo.mkdir(parents=True)

    write_file(repo / "AGENTS.md", AGENTS_TMPL.format(
        name=name, persona=persona, slug=slug, knowledge_home=knowledge_home))
    write_file(repo / "BRAIN.md", BRAIN_TMPL.format(slug=slug))
    write_file(repo / ".gitignore", GITIGNORE_TMPL)
    write_file(repo / "docs" / "decisions.md",
               DECISIONS_TMPL.format(name=name, today=today))

    gitkeep(repo / "docs" / "scratch")
    gitkeep(repo / "docs" / "superpowers" / "specs")
    gitkeep(repo / "docs" / "superpowers" / "adr")
    gitkeep(repo / "clients")
    gitkeep(repo / "assets")

    # CLAUDE.md -> AGENTS.md symlink
    claude = repo / "CLAUDE.md"
    if not claude.exists():
        claude.symlink_to("AGENTS.md")

    info(f"scaffolded repo: {repo}")

    if do_git:
        r = run(["git", "init"], cwd=repo)
        if r.returncode != 0:
            info(f"warn: git init failed: {r.stderr.strip()}")
            return
        run(["git", "add", "-A"], cwd=repo)
        r = run(["git", "commit", "-m",
                 f"chore: scaffold {name} lean venture repo (jstack-init)"], cwd=repo)
        if r.returncode == 0:
            info("git: initial commit created")
        else:
            info(f"warn: git commit: {r.stderr.strip() or r.stdout.strip()}")


# ---------------------------------------------------------------------------
# brain wiring
# ---------------------------------------------------------------------------

def wire_brain(brain: Path, name: str, slug: str, one_liner: str, short: str,
               today: str) -> None:
    hub = brain / "wiki" / "personal" / "ventures" / f"{slug}.md"
    if hub.exists():
        info(f"warn: hub page already exists, leaving untouched: {hub}")
    else:
        write_file(hub, HUB_TMPL.format(
            name=name, slug=slug, one_liner=one_liner, today=today))
        info(f"created brain hub: {hub}")

    # add satellites registry row (idempotent — skip if slug already present)
    sat = brain / "wiki" / "maps" / "satellites.md"
    text = sat.read_text()
    if f"`~/ventures/{slug}`" in text:
        info(f"warn: satellites registry already lists {slug}, skipping row")
    else:
        row = SAT_ROW_TMPL.format(name=name, slug=slug, short=short or one_liner)
        # insert after the last table row (lines starting with "| `~/")
        lines = text.splitlines(keepends=True)
        last_row = max((i for i, ln in enumerate(lines)
                        if ln.startswith("| `~/")), default=None)
        if last_row is None:
            die("could not find the satellites registry table to append to")
        lines.insert(last_row + 1, row)
        sat.write_text("".join(lines))
        info(f"added satellites registry row: {slug}")


def run_sb(brain: Path, name: str, slug: str) -> None:
    sb = brain / "tools" / "sb.py"
    hub_rel = f"wiki/personal/ventures/{slug}.md"

    r = run(["python3", str(sb), "index", "--write"], cwd=brain)
    info(f"sb index: {'ok' if r.returncode == 0 else 'FAILED'}")
    if r.returncode != 0:
        info(r.stderr.strip() or r.stdout.strip())

    r = run(["python3", str(sb), "log", "init-venture",
             f"Scaffolded {name} as a lean venture repo (~/ventures/{slug}); "
             f"created brain hub {slug}.md + satellites registry row",
             "--source", hub_rel], cwd=brain)
    info(f"sb log: {'ok' if r.returncode == 0 else 'FAILED'}")

    r = run(["python3", str(sb), "check"], cwd=brain)
    if r.returncode == 0:
        info("sb check: GREEN")
    else:
        info("sb check: NOT GREEN")
        info(r.stdout.strip())
        info(r.stderr.strip())


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Scaffold a lean venture repo + wire it into the brain.")
    ap.add_argument("--name", required=True, help="venture display name, e.g. 'GEO Optimization'")
    ap.add_argument("--slug", required=True, help="lowercase-hyphen slug, e.g. geo-optimization")
    ap.add_argument("--desc", required=True, help="one-line description (becomes the hub summary + AGENTS intro)")
    ap.add_argument("--persona", default=DEFAULT_PERSONA,
                    help="generic operating DISPOSITION (e.g. 'a lean strategic partner'). NOT venture "
                         "strategy — strategy lives in the brain. Defaults to a generic partner persona.")
    ap.add_argument("--short", default="", help="short registry-row descriptor (defaults to --desc)")
    ap.add_argument("--ventures-base", default=str(Path.home() / "ventures"),
                    help="override ventures root (testing)")
    ap.add_argument("--brain", default=str(Path.home() / "second-brain"),
                    help="override brain root (testing)")
    ap.add_argument("--no-git", action="store_true", help="skip git init/commit (testing)")
    args = ap.parse_args()

    slug = args.slug.strip()
    if not SLUG_RE.match(slug):
        die(f"invalid slug '{slug}' — must be lowercase letters/digits/hyphens")

    ventures_base = Path(args.ventures_base).expanduser()
    brain = Path(args.brain).expanduser()
    repo = ventures_base / slug
    today = date.today().isoformat()
    knowledge_home = f"~/second-brain/wiki/personal/ventures/{slug}.md"

    # safety: no clobber
    if repo.exists():
        die(f"{repo} already exists — refusing to clobber. Pick a new slug or remove it first.")
    if not (brain / "tools" / "sb.py").exists():
        die(f"brain toolkit not found at {brain}/tools/sb.py")

    scaffold_repo(repo, args.name, slug, args.desc, args.persona,
                  knowledge_home, today, do_git=not args.no_git)
    wire_brain(brain, args.name, slug, args.desc, args.short, today)
    run_sb(brain, args.name, slug)

    print()
    print(f"DONE — {args.name} ({slug})")
    print(f"  repo:  {repo}")
    print(f"  brain: {brain}/wiki/personal/ventures/{slug}.md")
    print()
    print("What next:")
    print("  - Capture durable decisions (offer, pricing, the why) via /jstack-savetobrain")
    print("    (then /jstack-brainwork to compile). NEVER hand-write venture canon into the brain.")
    print("  - Planning docs (specs/designs/ADRs) → docs/superpowers/ in the venture repo.")
    print("  - Work the GTM via /jstack-gtm.")


if __name__ == "__main__":
    main()
