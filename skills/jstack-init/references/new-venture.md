# new-venture — venture path operating doc

Scaffold a lean **work-product** venture as a satellite of the second brain: the repo at
`~/ventures/<slug>/` AND its brain wiring are born together. Use this path when the deliverable is
strategy/services/GTM/clients, not running code. (Code → `references/new-build.md`.)

> v0 first cut. A detailed hardening pass (per-venture extras, GTM seeding, richer hub) is a later
> session. Prioritize a working deterministic scaffold + clean brain wiring.

## What it produces

**Repo** (`~/ventures/<slug>/`) — the exact lean standard tree, no extra folders (reference impl:
`~/ventures/geo-optimization`):

```
AGENTS.md               pure router: generic persona + the ritual + identical operating rules
CLAUDE.md -> AGENTS.md   symlink
BRAIN.md                satellite pointer back to the brain
.gitignore
docs/decisions.md       append-only operational log (seeded header)
docs/scratch/.gitkeep
docs/superpowers/specs/.gitkeep
docs/superpowers/adr/.gitkeep
clients/.gitkeep
assets/.gitkeep
```
Then `git init` + an initial commit.

**Brain** (`~/second-brain/`) — always wired, this is the coupling:
- `wiki/personal/ventures/<slug>.md` — lean hub stub (frontmatter `type: personal-venture`, title,
  summary, created/updated, tags, `workspace:`; body: What it is / Why / Status / Satellite).
- a row in `wiki/maps/satellites.md` (the registry).
- runs `sb.py index --write`, appends `sb.py log` (`init-venture` op), runs `sb.py check` → reports
  GREEN. The new page is referenced by the index + the registry row, so it is **not orphaned**.

## AGENTS.md is a PURE ROUTER — no venture strategy

AGENTS.md carries **only** generic pointers + operating rules. It never states what the venture *is
or does* (that is strategy, and strategy lives in the brain). Sections 1–3 (where-context-lives,
folder map, operating principles) are byte-identical boilerplate across every venture.

- **Persona (§0) is GENERIC** — an operating *disposition* (e.g. "a lean strategic partner;
  decisive, honest about tradeoffs, a thinking partner not a yes-machine"), the same kind of thing
  for any venture. It is **not** the offer/pricing/wedge. `--persona` is optional and defaults to a
  generic partner persona; only override it with another *disposition*, never with strategy.
- **The ritual (§0)** is baked into every venture: when a strategic decision reshapes the venture,
  write a two-sentence "what this venture has become" summary and capture it to the brain hub via
  `/jstack-savetobrain`. The reshaping lives in the brain, never in AGENTS.md.

If you find yourself wanting to write a fact about the business into AGENTS.md, that is the signal it
belongs in the brain hub (`wiki/personal/ventures/<slug>.md`) instead.

## Run it

Collect the inputs (prompt for any missing):

- `--name` venture display name, e.g. `"GEO Optimization"`
- `--slug` lowercase-hyphen slug, e.g. `geo-optimization`
- `--desc` one-line description (becomes the hub summary + the AGENTS.md intro line)
- `--persona` (optional) generic operating *disposition*; defaults to a generic partner persona.
  NOT strategy — keep it a disposition.
- `--short` (optional) terse registry-row descriptor; defaults to `--desc`

```bash
python3 ~/jstack/skills/jstack-init/scripts/new_venture.py \
  --name "GEO Optimization" --slug geo-optimization \
  --desc "A Generative Engine Optimization service for owner-operated boutique hotels." \
  --short "Generative Engine Optimization for boutique hotels"
```

The script is deterministic and self-reporting (each step prints ok/FAILED; ends with a "what next"
block). It refuses if `~/ventures/<slug>/` already exists (no clobber) and **warns rather than
overwrites** an existing brain hub page or registry row, so a partial re-run is safe.

Testing flags (never scaffold a throwaway under the real `~/ventures/`): `--ventures-base <dir>`,
`--brain <dir>`, `--no-git` redirect everything to a temp sandbox.

## Adding a folder later (keep AGENTS.md in sync deterministically)

The folder map is **never hand-edited**. To add a top-level folder (and only when there's a real
reason — keep the tree lean + shallow), use the companion script, which creates the dir + inserts the
table row in one shot, idempotently, and rejects nested paths:

```bash
python3 ~/jstack/skills/jstack-init/scripts/register_folder.py \
  --venture <slug> --path <name> --desc "<one line>"
```

## Size cap + lint

Venture routers are capped at **~120 lines** (the router stays thin; detail lives in the brain).
Enforce with:

```bash
python3 ~/jstack/skills/jstack-init/scripts/lint_agents.py
```

## The brain gate (important)

The brain contract says agents never write `wiki/` from conversation without an explicit save/ingest.
**This structural init is the authorized exception** — the hub stub + registry row are the venture's
birth certificate, written once by this skill. From then on, **all ongoing venture knowledge flows
through `/jstack-savetobrain` → `/jstack-brainwork`**, never hand-edited into the brain. Do not use
this skill to write venture canon; use it only to scaffold.

## After it runs (tell Jono)

- Capture durable decisions (offer, pricing, the *why*) via `/jstack-savetobrain`.
- Planning docs (specs / designs / ADRs) → `docs/superpowers/` in the venture repo.
- Work the go-to-market via `/jstack-gtmarketing`.
