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
docs/_template.md       starter metadata/body for a new strategy artifact
docs/index.md           GENERATED file registry (docs_index.py) — read first, never hand-edit
docs/decisions.md       append-only operational log (seeded header)
docs/strategy/.gitkeep
clients/.gitkeep
assets/.gitkeep
```
Then `git init` + an initial commit. Scaffold also runs `docs_index.py index --write` so the fresh
repo ships with a (near-empty) `docs/index.md` entry point.

**Brain** (`~/second-brain/`) — always wired, this is the coupling:
- `wiki/personal/ventures/<slug>.md` — lean hub stub (frontmatter `type: personal-venture`, title,
  summary, created/updated, tags, `workspace:`; body: What it is / Why / Status / Satellite).
- `wiki/personal/ventures/<slug>.docs-index` — non-`.md` relative symlink to the satellite's canonical
  `docs/index.md`; it makes the generated registry discoverable in the brain without turning it into a
  second wiki page or copied catalog.
- a row in `wiki/maps/satellites.md` (the registry).
- runs `sb.py index --write`, appends `sb.py log` (`init-venture` op), runs `sb.py check` → reports
  GREEN. The new page is referenced by the index + the registry row, so it is **not orphaned**.

## AGENTS.md is a PURE ROUTER — no venture strategy

AGENTS.md carries **only** generic pointers + operating rules. It never states what the venture *is
or does*. Canonical workspace strategy and durable rationale live
in the satellite's generated docs registry and are linked from the brain; Sections 1–3
(where-context-lives, folder map, and document metadata) are byte-identical boilerplate across every
venture, as are the shared operating principles that follow.

- **Persona (§0) is GENERIC** — an operating *disposition* (e.g. "a lean strategic partner;
  decisive, honest about tradeoffs, a thinking partner not a yes-machine"), the same kind of thing
  for any venture. It is **not** the offer/pricing/wedge. `--persona` is optional and defaults to a
  generic partner persona; only override it with another *disposition*, never with strategy.
- **The ritual (§0)** is baked into every venture: when a strategic decision reshapes the venture,
  update its canonical workspace artifact and regenerate `docs/index.md`. Capture only a personal or
  cross-project consequence to the brain; AGENTS.md remains a router.

If you find yourself wanting to write a fact about the business into AGENTS.md, that is the signal it
belongs in the brain hub (`wiki/personal/ventures/<slug>.md`) instead.

The root router carries only a trigger: copy `docs/_template.md` for each new durable strategy
artifact, follow its summary/frontmatter guidance, then run the `docs_index.py` reindex and lint
commands. Do not create a client profile until real client work exists.

## Run it

Collect the inputs (prompt for any missing):

- `--name` venture display name, e.g. `"GEO Optimization"`
- `--slug` lowercase-hyphen slug, e.g. `geo-optimization`
- `--desc` one-line description (becomes the hub summary + the AGENTS.md intro line)
- `--persona` (optional) generic operating *disposition*; defaults to a generic partner persona.
  NOT strategy — keep it a disposition.
- `--short` (optional) terse registry-row descriptor; defaults to `--desc`

```bash
python3 ~/jstack/skills/init/scripts/new_venture.py \
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
python3 ~/jstack/skills/init/scripts/register_folder.py \
  --venture <slug> --path <name> --desc "<one line>"
```

## Docs registry (generated) — the docs/ mirror of the brain's `sb.py`

The venture's `docs/` tree is navigated through a GENERATED registry, `docs/index.md`, the same way the
brain is navigated through `wiki/index.md`. It is produced deterministically from each doc's
frontmatter by `scripts/docs_index.py` — a cold agent reads `docs/index.md` first and learns what
every durable decision artifact is about (filename, one-sentence summary, status) without walking
the tree or opening files.

The detailed document-writing contract lives in `docs/_template.md`; the project-root `AGENTS.md`
only points agents to that template and the reindex commands:

- **Canonical durable zone indexed:** `strategy/*.md`, named `YYYY-MM-DD-kebab-topic.md`, including
  strategy, research, and architecture rationale.
- **Frontmatter is the source of truth** (the index reads it, never the body). Required keys:
  `summary`, `status`. `title` is optional compatibility metadata and is not used as the generated
  link label. Optional: `type`, `created`, `updated`, `supersedes`, `superseded_by`.
- **Summary contract for new canonical strategy docs:** follow the template's factual, specific cue;
  write exactly one sentence with no more than 160 characters. The linter reports an error for a
  strategy doc that breaks this rule; preserved legacy zones report warnings and remain untouched.
- **After ANY add/edit under `docs/`, regenerate + lint** (a stale index is a lint error):

```bash
python3 ~/jstack/skills/init/scripts/docs_index.py index --write --venture <slug>
python3 ~/jstack/skills/init/scripts/docs_index.py lint          --venture <slug>
python3 ~/jstack/skills/init/scripts/docs_index.py brain-link-lint --venture <slug>
```

The scaffold creates the link with `docs_index.py brain-link --write`; it is a relative symlink, not a
copy. `brain-link-lint` is the deterministic no-drift check. Use `--repo <path> --brain <path>` for a
non-standard or test layout.

- `docs/_template.md` is the starter for a new `strategy/` document. Copy it, rename the file, and
  replace its placeholders before indexing.
- `backfill --write` seeds frontmatter on docs that have none (summary←first prose, status←parsed;
  optional title metadata is retained for compatibility); add `--refresh` to recompute
  summary/status from the body after a big edit.
  Use it to migrate a pre-existing venture whose docs predate the convention.
- Lint is GREEN at **0 errors**; warnings (empty summary, unresolved supersedes) are advisory.
- Target with `--venture <slug>` (under `~/ventures`) or `--repo <path>` (testing / non-standard root).

Naming is deliberately self-describing so the filename alone tells the topic; the index layers the
verdict/state on top. Full document-writing guidance lives in `docs/_template.md`; root `AGENTS.md`
only points agents there and to the reindex commands.

## Size cap + lint

Venture routers are capped at **~120 lines** (the router stays thin; detail lives in the brain).
Enforce with:

```bash
python3 ~/jstack/skills/init/scripts/lint_agents.py
```

## The brain gate (important)

The brain contract says agents never write `wiki/` from conversation without an explicit save/ingest.
**This structural init is the authorized exception** — the hub stub + registry row are the venture's
birth certificate, written once by this skill. From then on, ongoing venture canon stays in the
satellite's `docs/` tree; the brain sees only its generated index symlink. Do not use this skill to
write venture canon; use it only to scaffold.

## After it runs (tell Jono)

- Keep all durable venture strategy and rationale in `docs/strategy/`; regenerate the index after each
  edit. The brain receives only the `docs/index.md` symlink, never a copied artifact.
- Work the go-to-market via `/gtmarketing`.
