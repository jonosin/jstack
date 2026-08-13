# new-build — build path operating doc

Scaffold a real **codebase** at `~/builds/<slug>/` and wire it into the second brain as a full
satellite — repo and brain hub born together. Use this path when the deliverable is running software
(app, agent, internal tool, dashboard, library). For lean strategy/service satellites, use
`references/new-venture.md` instead.

## Build vs venture

- **BUILD** = ships running code; has a build/test/deploy loop; lives in `~/builds/<slug>/`.
- **VENTURE** = delivers a service/strategy/GTM; tracks clients/ops, not code; lives in
  `~/ventures/<slug>/`.

A venture that needs an app spawns its own build (e.g. `~/ventures/stayframe` work product +
`~/builds/stayframe-qa` dashboard). When unsure, ask: *does it run code?* yes → build.

## What it produces

**Repo** (`~/builds/<slug>/`) — a code repo:

```
AGENTS.md               Karpathy "good CLAUDE.md" coding guidelines (verbatim base)
                        + docs/index.md routing + an empty project-specific stub
CLAUDE.md -> AGENTS.md   symlink
BRAIN.md                satellite pointer back to the brain
.gitignore
docs/_template.md       starter metadata/body for a new strategy artifact
docs/index.md           generated registry — read first, brain-visible by symlink
docs/strategy/.gitkeep  canonical strategy, research, and architecture rationale
.scratch/.gitkeep       local tracker workspace when Matt's Markdown tracker is selected
```
Then `git init` + an initial commit. (Source layout is the build's own concern — the scaffold seeds
the contract, not the app skeleton.)

**Brain** (`~/second-brain/`) — wired as a **full satellite**, same coupling as ventures:
- `wiki/personal/builds/<slug>.md` — hub stub (frontmatter `type: personal-build`, title, summary,
  created/updated, tags, `workspace:`; body: satellite and documentation-registry pointers only).
- a row in `wiki/maps/satellites.md` (the registry).
- `wiki/personal/builds/<slug>.docs-index` — symlink to the exact generated `docs/index.md`, never
  a copied catalog.
- runs `sb.py index --write`, appends `sb.py log` (`init-build` op), runs `sb.py check` → reports
  GREEN. The new page is referenced by the index + the registry row, so it is **not orphaned**.

## AGENTS.md = Karpathy coding guidelines base

The build's `AGENTS.md` base is Karpathy's "good CLAUDE.md" behavioral coding guidelines, written
**verbatim** by `new_build.py`, then `docs/index.md` routing and an empty project-specific stub for
build-local conventions. The four load-bearing pillars (the verbatim text expands each):

- **Think before coding** — restate the goal, surface unknowns, plan before editing; no coding from
  vague intent.
- **Simplicity first** — the smallest change that satisfies the contract; no speculative
  abstraction, no gold-plating.
- **Surgical changes** — touch only what the task needs; don't drift into unrelated refactors;
  preserve working behavior.
- **Goal-driven execution** — define done, verify against it, stop when the contract is satisfied or
  a real blocker is hit.

Project-specific conventions (stack, entrypoints, deploy identity, gotchas) go in the stub. Durable
strategy and architecture rationale live in `docs/strategy/`. Specs and tickets live in the configured
tracker—repository-root `.scratch/` when Matt's local Markdown tracker is selected. The brain sees
only the generated `docs/index.md` symlink, never a duplicated artifact.

## Durable docs and summary guidance

The detailed document-writing contract lives in `docs/_template.md`. Copy it into `docs/strategy/`
for each durable artifact, replace its placeholders, and keep `summary` as a factual, specific cue
that lets an agent decide whether to open the document: exactly one sentence and no more than 160
characters. The linter enforces this contract for canonical strategy docs; preserved legacy zones
remain warning-only.

## Run it

Collect the inputs (prompt for any missing):

- `--name` build display name, e.g. `"Subscription Watcher"`
- `--slug` lowercase-hyphen slug, e.g. `subscription-watcher`
- `--desc` one-line description (becomes the hub summary + the AGENTS.md intro line)
- `--short` (optional) terse registry-row descriptor; defaults to `--desc`
- `--with-design` (optional) also initialize a `DESIGN.md` design system — see below

```bash
python3 ~/jstack/skills/init/scripts/new_build.py \
  --name "Subscription Watcher" --slug subscription-watcher \
  --desc "Watches free trials + subscriptions and warns before they renew." \
  --short "Free-trial / subscription renewal watcher"
```

Deterministic + self-reporting (each step prints ok/FAILED; ends with a "what next" block). Refuses
if `~/builds/<slug>/` already exists (no clobber) and **warns rather than overwrites** an existing
brain hub page or registry row, so a partial re-run is safe.

Testing flags (never scaffold a throwaway under the real `~/builds/`): `--builds-base <dir>`,
`--brain <dir>`, `--no-git` redirect everything to a temp sandbox.

## Design system (optional, deterministic) — folds in deprecated ggdesign-init

The deprecated `ggdesign-init` skill is baked in here. Initialize a Google `DESIGN.md` design
system **only when the build has UI/frontend that needs design consistency** (skip it for headless
agents, CLIs, libraries). It is fully deterministic.

- At scaffold time: pass `--with-design` to `new_build.py`.
- Later / standalone (any existing repo): `python3 ~/jstack/skills/init/scripts/init_design.py --repo <path>`.

`init_design.py` copies a starter `DESIGN.md` (template + spec/lint reference in
`references/design/`), wires a `## Design system` section into the repo's `AGENTS.md`, and can
lint/export tokens. The format is YAML frontmatter (machine-readable tokens) + Markdown body
(rationale); the CLI (`npx -y @google/design.md`) lints structure + WCAG contrast, diffs versions
for regressions, and exports to Tailwind or W3C DTCG JSON. Full reference: `references/design/`
(`spec.md`, `starter.md`, `lint-rules.md`).

## Size cap + lint

Build routers are capped at **~200 lines** (per Anthropic guidance — builds carry more legitimate
project-specific context than venture routers). Enforce with:

```bash
python3 ~/jstack/skills/init/scripts/lint_agents.py
```

## Workspace docs + brain gate (important)

Same rule as ventures: agents never write `wiki/` from conversation without an explicit save/ingest.
**This structural init is the authorized exception** — the hub stub + registry row are the build's
birth certificate, written once by this skill. From then on, build and strategy canon stays in its
`docs/` tree; the brain sees only its generated index symlink. Use this skill to scaffold, not to
write build canon.

## BUILD-only engineering workflow phase (required after scaffold)

Stay in the new BUILD repo. Install the Matt engineering workflow **locally to this project** — never
globally and never in `~/jstack` — then invoke `/setup-matt-pocock-skills` in the same session:

```bash
cd ~/builds/<slug>
npx skills add mattpocock/skills \
  --skill setup-matt-pocock-skills --skill implement --skill prototype \
  --skill to-tickets --skill code-review --skill triage \
  --agent codex claude-code --yes
```

`setup-matt-pocock-skills` remains interactive: investigate first, then ask for tracker and triage
choices and confirmation before writing. Its domain-document outcome is adapted here: retain
`CONTEXT.md` at the BUILD root, keep its engineering routing in the repo's root instructions, and
treat `docs/strategy/` (not `docs/adr/`) as the canonical home for ADR-like technical decisions.
`docs/index.md` remains the mandatory router and brain-visible artifact.

## BUILD-only Impeccable workflow (optional, project-local)

During interactive initialization, ask: **"Set up Impeccable for this project?"** Only after the
user confirms, remain in the new BUILD repo and install Impeccable locally:

```bash
cd ~/builds/<slug>
npx impeccable install
```

Then invoke `/init` from the installed Impeccable skill in the same session. It configures the
website design and build workflow for this repository. Never install it globally and never add it
to `~/jstack`.

For multi-session delivery, `/to-spec` creates the durable execution specification. For code
work, `/to-tickets` can create vertical execution slices in the configured tracker. Do not duplicate
specs or tickets into `docs/`; `docs/index.md` routes durable decisions, not execution records.

## Fresh execution policy

After `/to-spec` has created the execution spec, use `/handoff goal` to package it as a
paste-ready `/goal` prompt. The prompt tells the new task to read the spec, which owns the outcome,
scope, decisions, validation, and Progress. It does not reconstruct the plan or create a task.

## After it runs (tell Jono)

- Keep durable strategy and architecture rationale in `docs/strategy/`; regenerate `docs/index.md`
  after each edit. Keep specs/tickets in the configured tracker (`.scratch/` for the local Markdown
  tracker). The brain exposes only the generated index by symlink.
- Complete the BUILD-only engineering workflow phase above: project-local Matt skills, then
  `/setup-matt-pocock-skills`.
- If the user opts in, install Impeccable locally with `npx impeccable install`, then invoke `/init`
  in the same session.
- If it has UI and you skipped `--with-design`, run `init_design.py` before building screens.
