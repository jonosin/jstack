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
      _template.md         # starter metadata/body for a new strategy artifact
      index.md             # GENERATED file registry (docs_index.py) — read first, brain-visible by symlink
      decisions.md         # append-only operational log (seeded header)
      strategy/.gitkeep
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
> in `~/builds`). Canonical work product and venture strategy live here; the brain holds only
> cross-project knowledge, personal context, and pointers.

## 0. Persona + the one ritual

{persona}

Ritual (every venture, every session): when a strategic decision reshapes this venture, update its
canonical workspace artifact and regenerate `docs/index.md`. Capture only a personal or cross-project
consequence to the brain; never put venture strategy in this router.

## 1. Where venture context lives — start with the docs router

This repo holds canonical **work product and venture strategy**. Its generated `docs/index.md` is
linked from the brain without a duplicate catalog. The brain holds only cross-project knowledge,
personal context, and pointers:

- knowledge_home: `{knowledge_home}`
- Need a venture fact? Read `docs/index.md`, then the relevant durable document. Read the brain only for
  relevant cross-project or personal context.

## 2. Folder map

| Path | What |
|---|---|
| `docs/index.md` | GENERATED registry of every durable decision artifact (read first); regen via `docs_index.py` — never hand-edit |
| `docs/strategy/` | durable strategy, research, and architecture rationale |
| `docs/decisions.md` | append-only operational decision log |
| `clients/<slug>/` | one folder per client/prospect — all work product for that account |
| `assets/` | creatives, exports, downloads tied to the venture |

Adding a top-level folder needs a real reason (keep the tree lean + shallow, avoid nesting). Do it
deterministically so this table stays in sync — **never hand-edit the table**:

    python3 ~/jstack/skills/init/scripts/register_folder.py --venture {slug} --path <name> --desc "<one line>"

**Durable docs.** `docs/index.md` is the GENERATED registry of every durable decision artifact (what it
is about + its status) — **read it first**, never walk the tree blind. After adding/editing any doc
under `docs/`, regenerate + lint (a stale index is a lint error):

    python3 ~/jstack/skills/init/scripts/docs_index.py index --write --venture {slug}
    python3 ~/jstack/skills/init/scripts/docs_index.py lint          --venture {slug}
    python3 ~/jstack/skills/init/scripts/docs_index.py brain-link-lint --venture {slug}

Naming + frontmatter guidance (self-describing filenames; the index reads per-doc frontmatter, never
the body) lives in `docs/_template.md`; this root `AGENTS.md` only points agents there. The brain
exposes the exact generated index at
`~/second-brain/wiki/personal/ventures/{slug}.docs-index`; it is a symlink, never a copied catalog.

## 3. Durable document metadata

For each new durable strategy artifact, copy `docs/_template.md` into `docs/strategy/` and follow its
summary and frontmatter guidance. After any add/edit under `docs/`, run the three `docs_index.py`
commands in §2. Do not create a client profile or account folder until real client work exists.

## 4. Operating principles (identical across every venture)

- **brain ⊥ satellite.** Brain = cross-project knowledge, personal context, and pointers. This repo =
  canonical work product and venture strategy. Never duplicate a catalog or artifact body into the brain — **link**.
- **Capture:** update venture decisions in their canonical docs artifact. The brain link exposes only
  `docs/index.md`; **never write `~/second-brain/wiki/` from inside this repo.**
- **Durable docs** → `docs/strategy/`; the generated `docs/index.md` is the entry point and
  `docs/_template.md` is the document-writing contract. Its brain-visible `.docs-index` symlink must
  resolve to the same file; regenerate + lint after docs/ changes (see §2), never hand-edit.
- **Lean + shallow:** minimal top-level dirs, avoid nesting. Cross-project context belongs in the brain,
  not new folders.
- **Keep this router current — gated.** When the repo's structure or operating mechanics change, update
  this file in the *same* change (add folders via `register_folder.py`; fix routing/pointers inline).
  Before adding any line ask: *is this a durable operating rule needed every session?* If it's a
  procedure, template, research note, or cross-project decision, put it in its canonical artifact and
  **link it** instead. Keep venture strategy in its canonical artifact.
- **Hard size cap (~120 lines).** If this router grows past ~120 lines, move detail into its canonical
  artifact. Check: `python3 ~/jstack/skills/init/scripts/lint_agents.py`.
- **Read flow:** (1) read `docs/index.md` for execution-facing current state and locate durable docs;
  (2) read `BRAIN.md` → `knowledge_home` for venture-specific context; (3) open only the documents
  those indexes identify; (4) escalate to `raw/` or source material only when the output is work-grade.
"""

BRAIN_TMPL = """# BRAIN.md — second-brain pointer

This repo is a **satellite** of the owner's second brain. Canonical venture strategy and work product
live here; the brain holds cross-project knowledge and pointers. Link, don't duplicate.

- brain_path: ~/second-brain
- knowledge_home: wiki/personal/ventures/{slug}.md   # this venture's hub page in the brain
- read_order: docs/index.md → ~/second-brain/AGENTS.md → wiki/hot.md → wiki/index.md → knowledge_home → [[wikilinks]]
- capture_rule: durable venture decision/fact → canonical docs artifact + regenerate docs/index.md (never write ~/second-brain/wiki/ from here)
- link_rule: cite brain pages by path; the brain page may point back here via a `workspace:` field
- docs_index: wiki/personal/ventures/{slug}.docs-index   # brain-visible symlink to this repo's docs/index.md

A cold agent in this repo that needs a brain-resident fact: read `knowledge_home` (and what it links)
under `brain_path`. The brain's satellite registry — `~/second-brain/wiki/maps/satellites.md` — lists
every sibling repo.
"""

DECISIONS_TMPL = """# Operational decision log — {name}

Append-only. One line per operational decision (tooling, process, repo mechanics). **Durable strategic
decisions (offer, pricing, positioning, the *why*) and any architecture rationale live in
`docs/strategy/`.** This log is for repo/execution choices, newest at top.

| Date | Decision | Why |
|---|---|---|
| {today} | Scaffolded `{name}` as a lean venture repo (init). | New venture spun up; standard lean tree + brain coupling (hub page + satellite registry). |
"""

# A starter for new canonical strategy docs.  It intentionally omits `title`:
# the filename is the index label, while `title` remains an optional legacy
# field accepted by docs_index.py.
DOC_TEMPLATE_TMPL = """---
summary: \"Replace this with a factual, specific cue that tells an agent whether to open this document.\"
status: draft
type: strategy
created: {today}
updated: {today}
---

# Descriptive document heading

## Summary guidance

`summary` is a factual, specific cue that lets an agent decide whether to open this document. Write
exactly one sentence with no more than 160 characters.

Good: `Accepted routing keeps customer data in the EU and removes the legacy export step.`

Bad: `This document contains useful information about the project.`

## Outcome

Write the decision, direction, or current state here. Keep the frontmatter summary factual and
specific.

## Context

Record only the evidence and reasoning needed to understand the outcome.
"""

GITIGNORE_TMPL = """.DS_Store
.env
*.local
node_modules/
__pycache__/
*.pyc
.playwright-mcp/
"""

# Generic operating disposition — NOT venture strategy. Canonical venture strategy lives in docs/.
DEFAULT_PERSONA = (
    "Operate this venture as a lean strategic partner: decisive, honest about tradeoffs, biased to "
    "the smallest action that creates real signal, allergic to bloat and busywork. You are a thinking "
    "partner, not a yes-machine — push back when something seems off."
)

HUB_TMPL = """---
type: personal-venture
title: "{name}"
summary: "Workspace router for ~/ventures/{slug}/. Canonical venture artifacts are discoverable through its linked docs/index.md."
created: {today}
updated: {today}
tags: [venture, {slug}]
workspace: ~/ventures/{slug}/
---
# {name} — venture hub

> **Workspace router** for the {name} venture. Canonical strategy and work artifacts live in the
> satellite repository; this page carries only cross-project pointers.

## Satellite
Canonical repository `~/ventures/{slug}/` (`BRAIN.md` points back here). Registry:
[[../../maps/satellites|Satellite Registry]].

## Documentation registry
The generated satellite registry is available without a copy at
`wiki/personal/ventures/{slug}.docs-index` (a symlink to `~/ventures/{slug}/docs/index.md`).
"""

# satellites.md row (added to the registry table)
SAT_ROW_TMPL = (
    "| `~/ventures/{slug}` (**{name}** — {short}) "
    "| `wiki/personal/ventures/{slug}.md` | yes | `wiki/personal/ventures/{slug}.docs-index` |\n"
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

    # Keep document-writing rules in the project-root AGENTS.md.  The docs
    # directory contains only canonical artifacts, the generated index, and
    # the starter template.
    write_file(repo / "docs" / "_template.md", DOC_TEMPLATE_TMPL.format(today=today))

    gitkeep(repo / "docs" / "strategy")
    gitkeep(repo / "clients")
    gitkeep(repo / "assets")

    # Root CLAUDE.md -> AGENTS.md symlink
    claude = repo / "CLAUDE.md"
    if not claude.exists():
        claude.symlink_to("AGENTS.md")

    # generate the initial (empty) docs registry so a cold agent has an entry point from day 1
    docs_index = Path(__file__).resolve().parent / "docs_index.py"
    r = run([sys.executable, str(docs_index), "index", "--write", "--repo", str(repo)])
    info(f"docs index: {'ok' if r.returncode == 0 else 'FAILED'}")
    if r.returncode != 0:
        info(r.stderr.strip() or r.stdout.strip())

    info(f"scaffolded repo: {repo}")

    if do_git:
        r = run(["git", "init"], cwd=repo)
        if r.returncode != 0:
            info(f"warn: git init failed: {r.stderr.strip()}")
            return
        run(["git", "add", "-A"], cwd=repo)
        r = run(["git", "commit", "-m",
                 f"chore: scaffold {name} lean venture repo (init)"], cwd=repo)
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
                         "strategy — canonical workspace strategy lives in docs/. Defaults to a generic partner persona.")
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
    docs_index = Path(__file__).resolve().parent / "docs_index.py"
    r = run([sys.executable, str(docs_index), "brain-link", "--write", "--repo", str(repo),
             "--brain", str(brain)])
    info(f"brain docs index link: {'ok' if r.returncode == 0 else 'FAILED'}")
    if r.returncode != 0:
        info(r.stderr.strip() or r.stdout.strip())
    r = run([sys.executable, str(docs_index), "brain-link-lint", "--repo", str(repo),
             "--brain", str(brain)])
    info(f"brain docs index link lint: {'GREEN' if r.returncode == 0 else 'NOT GREEN'}")
    if r.returncode != 0:
        info(r.stderr.strip() or r.stdout.strip())
    run_sb(brain, args.name, slug)

    print()
    print(f"DONE — {args.name} ({slug})")
    print(f"  repo:  {repo}")
    print(f"  brain: {brain}/wiki/personal/ventures/{slug}.md")
    print()
    print("What next:")
    print("  - Copy docs/_template.md into docs/strategy/ for each durable artifact; follow its summary guidance.")
    print("    Regenerate docs/index.md after edits; its links use filenames, not optional titles.")
    print("  - The brain exposes only the docs/index.md symlink; never duplicate artifact bodies there.")
    print("  - Work the GTM via /gtmarketing.")


if __name__ == "__main__":
    main()
