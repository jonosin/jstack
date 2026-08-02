#!/usr/bin/env python3
"""new_build.py — deterministically scaffold a software BUILD repo AND wire it into
the second brain as a full satellite.

A build is *code* (an app, tool, agent, service). It differs from a venture: no
clients/ or assets/ folders (those are venture concepts), and its source layout is
the agent's choice. The brain coupling is identical in spirit to new_venture.py —
it ALWAYS happens:

  ~/builds/<slug>/
    AGENTS.md              # the BUILD router: Karpathy coding guidelines + brain pointer + project stub
    CLAUDE.md -> AGENTS.md # symlink
    BRAIN.md              # satellite pointer back to the brain
    .gitignore
    docs/
      AGENTS.md            # docs router: naming/frontmatter rules (CLAUDE.md symlink)
      index.md             # GENERATED file registry (read first; brain-visible by symlink)
      decisions.md         # append-only operational log (seeded header)
      strategy/.gitkeep
    .scratch/              # local tracker workspace when Matt's local tracker is selected

Brain side:
  - create wiki/personal/builds/<slug>.md hub stub (warn-not-overwrite)
  - add a row to wiki/maps/satellites.md (idempotent)
  - run sb.py index, append sb.py log (init-build), run sb.py check

Determinism: all mechanics live here. Idempotency: refuses if ~/builds/<slug>/ exists.

Usage:
  new_build.py --name "Subscription Watcher" --slug subscription-watcher \
      --desc "watches free trials + subscriptions and warns before renewal"

  # also lay down a DESIGN.md (UI build):
  new_build.py ... --with-design

  # override roots for testing (no clobber of real dirs):
  new_build.py ... --builds-base /tmp/b --brain /tmp/brain --no-git
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# templates
# ---------------------------------------------------------------------------

AGENTS_TMPL = """# {name}

> Built for agents working in this build repo. `CLAUDE.md` symlinks here. Terse + imperative.
> **Purpose:** this is a software **build** (code). The behavioral guidelines below are the standard;
> project-specific instructions go under "## Project". Canonical strategy and architecture decisions
> live in `docs/strategy/` — see "## Docs". Keep this file under ~200 lines
> (`python3 ~/jstack/skills/jstack-init/scripts/lint_agents.py`).

Coding-specific guidelines. The general behavioral pillars (think before acting,
simplicity first, surgical changes, goal-driven execution) live in the global operating
standard (`~/.claude/CLAUDE.md`); this file carries only the coding-specific bar.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**
- If the task touches existing behavior, name which callers/tests you checked before starting.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**
- No abstractions for single-use code. No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**
- Don't refactor things that aren't broken. Match existing style, even if you'd do it differently.
- Remove imports/variables/functions that YOUR changes made unused; leave pre-existing dead code (mention it, don't delete it).

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**
- "Add validation" -> "Write tests for invalid inputs, then make them pass"
- "Fix the bug" -> "Write a test that reproduces it, then make it pass"
- "Refactor X" -> "Ensure tests pass before and after"

## Project

{desc}

<!-- Project-specific instructions: build/test/run commands, architecture, conventions that differ
     from defaults, non-obvious gotchas. Add only what an agent CANNOT infer from the repo; link long
     material out. Keep it lean. -->

## Docs

`docs/index.md` is the generated router for every durable decision artifact. Read it first; do not
walk `docs/` blind. Strategy, architecture, and durable build rationale live in `docs/strategy/`.
Specs and tickets live in the configured tracker (root `.scratch/` when using Matt's local tracker).
After editing `docs/strategy/`, regenerate + lint the index:

    python3 ~/jstack/skills/jstack-init/scripts/docs_index.py index --write --repo . --satellite-kind build
    python3 ~/jstack/skills/jstack-init/scripts/docs_index.py lint --repo . --satellite-kind build

The second brain sees only the generated docs-index symlink. Do not capture or duplicate repo
artifacts there. Cross-project/personal context, when relevant, is routed through `BRAIN.md`.
"""

BRAIN_TMPL = """# BRAIN.md — second-brain pointer

This repo is a **satellite** of the owner's second brain. Canonical strategy and architecture rationale
live in this repo's `docs/`; the brain sees only its generated docs-index
symlink. Link, don't duplicate.

- brain_path: ~/second-brain
- knowledge_home: wiki/personal/builds/{slug}.md   # this build's hub page in the brain
- read_order: docs/index.md → ~/second-brain/AGENTS.md → wiki/hot.md → wiki/index.md → knowledge_home → [[wikilinks]]
- docs_index: wiki/personal/builds/{slug}.docs-index   # symlink to this repo's docs/index.md
- capture_rule: update canonical docs artifact + regenerate index; never write/capture repo artifacts to ~/second-brain/wiki/
- link_rule: cite brain pages by path; the brain page may point back here via a `workspace:` field

A cold agent in this repo that needs a brain-resident fact: read `knowledge_home` (and what it links)
under `brain_path`. The brain's satellite registry — `~/second-brain/wiki/maps/satellites.md` — lists
every sibling repo.
"""

DECISIONS_TMPL = """# Operational decision log — {name}

Append-only. One line per operational decision (tooling, process, repo mechanics). **Durable strategy
and architecture rationale live in `docs/strategy/`; delivery specs and tickets live in the configured tracker.**
This log is for repo/execution choices, newest at top.

| Date | Decision | Why |
|---|---|---|
| {today} | Scaffolded `{name}` as a build repo (jstack-init/new_build). | New build spun up; standard build tree + brain coupling (hub page + satellite registry). |
"""

DOCS_ROUTER_TMPL = """# docs/ — durable decisions (router)

> Built for agents. **Entry point:** [`index.md`](index.md), the GENERATED file registry. Read it
> first; it says what every durable artifact is about and its status.

## Rules

- Never hand-edit `index.md`. After add/edit under `strategy/`, run:

      python3 ~/jstack/skills/jstack-init/scripts/docs_index.py index --write --repo . --satellite-kind build
      python3 ~/jstack/skills/jstack-init/scripts/docs_index.py lint --repo . --satellite-kind build
      python3 ~/jstack/skills/jstack-init/scripts/docs_index.py brain-link-lint --repo . --satellite-kind build

- `strategy/` holds durable product, business, architecture, and technical decisions.
- Name durable artifacts `YYYY-MM-DD-kebab-topic.md`; include frontmatter: `title`, `summary`,
  and `status` (`active`, `accepted`, `proposed`, `draft`, `superseded`, `deprecated`, `archived`).
- `build/`, `scratch/`, and `superpowers/`, if present in an older repo, are legacy material:
  indexed where applicable but never destinations for new docs. The root `.scratch/` is the local
  tracker workspace when configured; its specs and tickets are not docs artifacts.
- The second brain exposes only `wiki/personal/builds/{slug}.docs-index`, a symlink to this exact
  `index.md`. Do not copy or capture repo artifacts into the brain.
"""

GITIGNORE_TMPL = """.DS_Store
.env
*.local
node_modules/
__pycache__/
*.pyc
.playwright-mcp/
"""

HUB_TMPL = """---
type: personal-build
title: "{name}"
summary: "Workspace router for ~/builds/{slug}/. Canonical durable decisions are discoverable through its linked docs/index.md."
created: {today}
updated: {today}
tags: [build, {slug}]
workspace: ~/builds/{slug}/
---
# {name} — build hub

> **Workspace router** for the {name} build. Canonical durable decisions live in the satellite
> repository; this page carries only cross-project pointers.

## Satellite
Canonical repository `~/builds/{slug}/` (`BRAIN.md` points back here). Registry:
[[../../maps/satellites|Satellite Registry]].

## Documentation registry
The generated satellite registry is available without a copy at
`wiki/personal/builds/{slug}.docs-index` (a symlink to `~/builds/{slug}/docs/index.md`).
"""

# satellites.md row (added to the registry table)
SAT_ROW_TMPL = (
    "| `~/builds/{slug}` (**{name}** — {short}) "
    "| `wiki/personal/builds/{slug}.md` | yes | `wiki/personal/builds/{slug}.docs-index` |\n"
)


# ---------------------------------------------------------------------------
# helpers (copied from new_venture.py to keep this script self-contained)
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

def scaffold_repo(repo: Path, name: str, slug: str, one_liner: str,
                  knowledge_home: str, today: str, do_git: bool) -> None:
    # build tree — no clients/ or assets/ (venture concepts); source layout is the agent's choice
    repo.mkdir(parents=True)

    write_file(repo / "AGENTS.md", AGENTS_TMPL.format(
        name=name, desc=one_liner, knowledge_home=knowledge_home))
    write_file(repo / "BRAIN.md", BRAIN_TMPL.format(slug=slug))
    write_file(repo / ".gitignore", GITIGNORE_TMPL)
    write_file(repo / "docs" / "decisions.md",
               DECISIONS_TMPL.format(name=name, today=today))
    write_file(repo / "docs" / "AGENTS.md", DOCS_ROUTER_TMPL.format(slug=slug))

    gitkeep(repo / "docs" / "strategy")
    gitkeep(repo / ".scratch")

    docs_claude = repo / "docs" / "CLAUDE.md"
    if not docs_claude.exists():
        docs_claude.symlink_to("AGENTS.md")

    # CLAUDE.md -> AGENTS.md symlink
    claude = repo / "CLAUDE.md"
    if not claude.exists():
        claude.symlink_to("AGENTS.md")

    # Generate the empty registry before any cold agent lands in the repository.
    docs_index = Path(__file__).resolve().parent / "docs_index.py"
    r = run([sys.executable, str(docs_index), "index", "--write", "--repo", str(repo),
             "--satellite-kind", "build"])
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
                 f"chore: scaffold {name} build repo (jstack-init/new_build)"], cwd=repo)
        if r.returncode == 0:
            info("git: initial commit created")
        else:
            info(f"warn: git commit: {r.stderr.strip() or r.stdout.strip()}")


# ---------------------------------------------------------------------------
# brain wiring
# ---------------------------------------------------------------------------

def wire_brain_build(brain: Path, name: str, slug: str, one_liner: str, short: str,
                     today: str) -> None:
    hub = brain / "wiki" / "personal" / "builds" / f"{slug}.md"
    if hub.exists():
        info(f"warn: hub page already exists, leaving untouched: {hub}")
    else:
        write_file(hub, HUB_TMPL.format(
            name=name, slug=slug, one_liner=one_liner, today=today))
        info(f"created brain hub: {hub}")

    # add satellites registry row (idempotent — skip if slug already present)
    sat = brain / "wiki" / "maps" / "satellites.md"
    text = sat.read_text()
    if f"`~/builds/{slug}`" in text:
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


def run_sb_build(brain: Path, name: str, slug: str) -> None:
    sb = brain / "tools" / "sb.py"
    hub_rel = f"wiki/personal/builds/{slug}.md"

    r = run(["python3", str(sb), "index", "--write"], cwd=brain)
    info(f"sb index: {'ok' if r.returncode == 0 else 'FAILED'}")
    if r.returncode != 0:
        info(r.stderr.strip() or r.stdout.strip())

    r = run(["python3", str(sb), "log", "init-build",
             f"Scaffolded {name} as a build repo (~/builds/{slug}); "
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
# optional design init
# ---------------------------------------------------------------------------

def run_design(repo: Path) -> None:
    init_design = Path(__file__).parent / "init_design.py"
    if not init_design.exists():
        info(f"warn: init_design.py not found at {init_design}, skipping --with-design")
        return
    info("--with-design: running init_design.py ...")
    r = run(["python3", str(init_design), "--repo", str(repo)])
    if r.stdout.strip():
        info(r.stdout.strip())
    if r.returncode != 0:
        info(f"warn: init_design.py exited {r.returncode}")
        if r.stderr.strip():
            info(r.stderr.strip())


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Scaffold a build repo + wire it into the brain as a satellite.")
    ap.add_argument("--name", required=True, help="build display name, e.g. 'Subscription Watcher'")
    ap.add_argument("--slug", required=True, help="lowercase-hyphen slug, e.g. subscription-watcher")
    ap.add_argument("--desc", required=True, help="one-line description (becomes the hub summary + AGENTS Project stub)")
    ap.add_argument("--short", default="", help="short registry-row descriptor (defaults to --desc)")
    ap.add_argument("--with-design", action="store_true",
                    help="also lay down a DESIGN.md via init_design.py (UI builds)")
    ap.add_argument("--builds-base", default=str(Path.home() / "builds"),
                    help="override builds root (testing)")
    ap.add_argument("--brain", default=str(Path.home() / "second-brain"),
                    help="override brain root (testing)")
    ap.add_argument("--no-git", action="store_true", help="skip git init/commit (testing)")
    args = ap.parse_args()

    slug = args.slug.strip()
    if not SLUG_RE.match(slug):
        die(f"invalid slug '{slug}' — must be lowercase letters/digits/hyphens")

    builds_base = Path(args.builds_base).expanduser()
    brain = Path(args.brain).expanduser()
    repo = builds_base / slug
    today = date.today().isoformat()
    knowledge_home = f"~/second-brain/wiki/personal/builds/{slug}.md"

    # safety: no clobber
    if repo.exists():
        die(f"{repo} already exists — refusing to clobber. Pick a new slug or remove it first.")
    if not (brain / "tools" / "sb.py").exists():
        die(f"brain toolkit not found at {brain}/tools/sb.py")

    scaffold_repo(repo, args.name, slug, args.desc, knowledge_home, today,
                  do_git=not args.no_git)
    wire_brain_build(brain, args.name, slug, args.desc, args.short, today)
    docs_index = Path(__file__).resolve().parent / "docs_index.py"
    r = run([sys.executable, str(docs_index), "brain-link", "--write", "--repo", str(repo),
             "--brain", str(brain), "--satellite-kind", "build"])
    info(f"brain docs index link: {'ok' if r.returncode == 0 else 'FAILED'}")
    if r.returncode != 0:
        info(r.stderr.strip() or r.stdout.strip())
    r = run([sys.executable, str(docs_index), "brain-link-lint", "--repo", str(repo),
             "--brain", str(brain), "--satellite-kind", "build"])
    info(f"brain docs index link lint: {'GREEN' if r.returncode == 0 else 'NOT GREEN'}")
    if r.returncode != 0:
        info(r.stderr.strip() or r.stdout.strip())
    run_sb_build(brain, args.name, slug)

    if args.with_design:
        run_design(repo)

    print()
    print(f"DONE — {args.name} ({slug})")
    print(f"  repo:  {repo}")
    print(f"  brain: {brain}/wiki/personal/builds/{slug}.md")
    print()
    print("What next:")
    print("  - Durable strategy and architecture rationale → docs/strategy/; specs/tickets → configured tracker (.scratch/ for local tracker).")
    print("    Regenerate docs/index.md after edits; the brain sees only its symlink.")
    print("  - BUILD-only engineering workflow (run from this repo; project-local, never global):")
    print("      npx skills add mattpocock/skills --skill setup-matt-pocock-skills --skill implement \\")
    print("        --skill prototype --skill to-spec --skill to-tickets --skill code-review --skill wayfinder --skill triage \\")
    print("        --agent codex claude-code --yes")
    print("    Then invoke /setup-matt-pocock-skills (tracker + triage + CONTEXT.md; asks before writing).")
    print("  - Optional website/frontend workflow: ask whether to set up Impeccable for this project.")
    print("      npx impeccable install")
    print("    On confirmation, run it from this repo, then invoke /init from the installed skill.")
    if not args.with_design:
        print("  - UI build with no design yet? Lay down DESIGN.md:")
        print(f"      python3 {Path(__file__).parent / 'init_design.py'} --repo {repo}")


if __name__ == "__main__":
    main()
