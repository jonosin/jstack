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
                        + a one-line brain pointer + an empty project-specific stub
CLAUDE.md -> AGENTS.md   symlink
BRAIN.md                satellite pointer back to the brain
.gitignore
```
Then `git init` + an initial commit. (Source layout is the build's own concern — the scaffold seeds
the contract, not the app skeleton.)

**Brain** (`~/second-brain/`) — wired as a **full satellite**, same coupling as ventures:
- `wiki/personal/builds/<slug>.md` — hub stub (frontmatter `type: personal-build`, title, summary,
  created/updated, tags, `workspace:`; body: What it is / Why / Status / Satellite).
- a row in `wiki/maps/satellites.md` (the registry).
- runs `sb.py index --write`, appends `sb.py log` (`init-build` op), runs `sb.py check` → reports
  GREEN. The new page is referenced by the index + the registry row, so it is **not orphaned**.

## AGENTS.md = Karpathy coding guidelines base

The build's `AGENTS.md` base is Karpathy's "good CLAUDE.md" behavioral coding guidelines, written
**verbatim** by `new_build.py`, then a one-line brain pointer and an empty project-specific stub for
build-local conventions. The four load-bearing pillars (the verbatim text expands each):

- **Think before coding** — restate the goal, surface unknowns, plan before editing; no coding from
  vague intent.
- **Simplicity first** — the smallest change that satisfies the contract; no speculative
  abstraction, no gold-plating.
- **Surgical changes** — touch only what the task needs; don't drift into unrelated refactors;
  preserve working behavior.
- **Goal-driven execution** — define done, verify against it, stop when the contract is satisfied or
  a real blocker is hit.

Project-specific conventions (stack, entrypoints, deploy identity, gotchas) go in the stub, never in
the brain. Strategy/decisions/knowledge go in the brain hub, never in `AGENTS.md`.

## Run it

Collect the inputs (prompt for any missing):

- `--name` build display name, e.g. `"Subscription Watcher"`
- `--slug` lowercase-hyphen slug, e.g. `subscription-watcher`
- `--desc` one-line description (becomes the hub summary + the AGENTS.md intro line)
- `--short` (optional) terse registry-row descriptor; defaults to `--desc`
- `--with-design` (optional) also initialize a `DESIGN.md` design system — see below

```bash
python3 ~/jstack/skills/jstack-init/scripts/new_build.py \
  --name "Subscription Watcher" --slug subscription-watcher \
  --desc "Watches free trials + subscriptions and warns before they renew." \
  --short "Free-trial / subscription renewal watcher"
```

Deterministic + self-reporting (each step prints ok/FAILED; ends with a "what next" block). Refuses
if `~/builds/<slug>/` already exists (no clobber) and **warns rather than overwrites** an existing
brain hub page or registry row, so a partial re-run is safe.

Testing flags (never scaffold a throwaway under the real `~/builds/`): `--builds-base <dir>`,
`--brain <dir>`, `--no-git` redirect everything to a temp sandbox.

## Design system (optional, deterministic) — folds in deprecated jstack-ggdesign-init

The deprecated `jstack-ggdesign-init` skill is baked in here. Initialize a Google `DESIGN.md` design
system **only when the build has UI/frontend that needs design consistency** (skip it for headless
agents, CLIs, libraries). It is fully deterministic.

- At scaffold time: pass `--with-design` to `new_build.py`.
- Later / standalone (any existing repo): `python3 ~/jstack/skills/jstack-init/scripts/init_design.py --repo <path>`.

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
python3 ~/jstack/skills/jstack-init/scripts/lint_agents.py
```

## The brain gate (important)

Same rule as ventures: agents never write `wiki/` from conversation without an explicit save/ingest.
**This structural init is the authorized exception** — the hub stub + registry row are the build's
birth certificate, written once by this skill. From then on, **all ongoing build knowledge flows
through `/jstack-savetobrain` → `/jstack-brainwork`**, never hand-edited into the brain. Use this
skill to scaffold, not to write build canon.

## After it runs (tell Jono)

- Capture durable decisions (architecture, the *why*) via `/jstack-savetobrain`.
- Planning docs (specs / designs / ADRs) → `docs/superpowers/` in the build repo.
- If it has UI and you skipped `--with-design`, run `init_design.py` before building screens.
