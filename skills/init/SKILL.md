---
name: init
description: "Scaffold a new project repo and wire it into the second brain. Two paths — VENTURE (lean work-product satellite at ~/ventures/[slug]/: strategy, services, GTM) or BUILD (a codebase at ~/builds/[slug]/: app, agent, internal tool). Both born coupled to the brain (hub page + satellites registry + sb index/log/check). Use when Jono says /init, /jstack-new-venture (legacy alias), new venture, new build, new project, scaffold a repo, spin up a venture/build, start a new app/tool, create a satellite repo, or init a design system / DESIGN.md (the deprecated ggdesign-init folds into the build path here)."
---

# init

Scaffold a new repo and wire it into the second brain in one deterministic shot. The brain coupling
is the whole point — repo and its brain hub are born together so a cold agent landing in either
discovers the other. This skill is a **thin intent router**: decide the path, then read the matching
reference and run the matching script. It does not duplicate per-path detail.

## Decide the path first

Two paths. Classify before scaffolding:

- **VENTURE** — a lean **work-product** satellite at `~/ventures/<slug>/`. The deliverable is
  strategy/services/GTM/clients, not source code. `AGENTS.md` is a pure router; canonical workspace
  artifacts, including strategy decisions, live under `docs/` and are discoverable through its
  GENERATED file registry (`docs_index.py` → `docs/index.md`), while the brain holds cross-project
  knowledge and pointers. The registry lets a
  cold agent finds every ADR/spec without walking the tree; the brain exposes the exact same file through
  a validated no-drift symlink. Choose when the thing *sells or delivers a service* and you'd track clients/ops, not
  a build/test/deploy loop.
- **BUILD** — a real **codebase** at `~/builds/<slug>/` (app, agent, internal tool, dashboard,
  library). The deliverable is shipped software. `AGENTS.md` is Karpathy-style coding guidelines;
  its canonical strategy and architecture rationale live under `docs/strategy/`, routed by generated
  `docs/index.md`; delivery specs and tickets remain in the configured tracker.
  Choose when the thing *runs code* and has a build/test/deploy loop.

Decision rule: **delivers a service / strategy / GTM → VENTURE. Ships running software → BUILD.**
If a venture later needs an app, that app is its own BUILD (e.g. `~/ventures/stayframe` +
`~/builds/stayframe-qa`). If ambiguous, ask Jono one question: *"Is this a lean strategy/service
satellite (venture) or a codebase you'll build/run (build)?"*

## Route

| Path | Read | Then run |
|------|------|----------|
| **VENTURE** | `references/new-venture.md` | `python3 ~/jstack/skills/init/scripts/new_venture.py` |
| **BUILD** | `references/new-build.md` | `python3 ~/jstack/skills/init/scripts/new_build.py` |

Read the reference before running — it owns the inputs, the no-clobber safety, the brain gate, and
the size-cap lint for that path. Do not run the script from this file alone.

## BUILD-only engineering workflow phase

After `new_build.py` finishes its deterministic scaffold, stay in the new BUILD repo and complete
this phase in the same session. It is deliberately interactive: install the selected Matt engineering
skills **project-locally** (never `--global`, never in `~/jstack`) and then invoke
`/setup-matt-pocock-skills`. That setup asks for tracker choices and confirmation before it writes.
Read `references/new-build.md` for the exact install command and the docs-layout adaptation.
For delivery execution, `/to-spec` creates the canonical execution contract. Matt's
`/to-tickets` can split a code delivery into separate execution slices. Use `/handoff goal`
only after the execution spec exists; it packages that spec as a paste-ready `/goal` prompt for a
fresh task.

## Impeccable design workflow (build path only)

After the BUILD scaffold and project-local engineering setup, ask: **"Set up Impeccable for this
project?"** Do not install it unless the user confirms. On confirmation, stay in the new repo and
install it locally:

```bash
cd ~/builds/<slug>
npx impeccable install
```

Then invoke `/init` from the installed Impeccable skill in the same session. This establishes its
project-specific website design and build workflow. Do not install Impeccable globally or into
`~/jstack`.

## Design system (build path only)

The deprecated `ggdesign-init` skill is **folded into the build path here**. When a build has
UI/frontend that needs design consistency, the build path initializes a Google `DESIGN.md` design
system deterministically (`new_build.py --with-design`, or `scripts/init_design.py --repo <path>`
later / standalone). Details live in `references/new-build.md`; format/lint reference in
`references/design/`.

## Next skills

| Next | When |
|------|------|
| `/setup-matt-pocock-skills` | BUILD only, immediately after init has installed the project-local engineering skills. |
| `/init` | BUILD only, after the user opts into a project-local Impeccable setup. |
| `/gtmarketing` | A new venture needs go-to-market strategy (the usual next move after scaffolding). |
| `/brainwork` | Pending raw captured for this venture/build needs compiling into the wiki. |
