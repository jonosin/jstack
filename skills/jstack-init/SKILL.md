---
name: jstack-init
description: "Scaffold a new project repo and wire it into the second brain. Two paths — VENTURE (lean work-product satellite at ~/ventures/<slug>/: strategy, services, GTM) or BUILD (a codebase at ~/builds/<slug>/: app, agent, internal tool). Both born coupled to the brain (hub page + satellites registry + sb index/log/check). Use when Jono says /jstack-init, /jstack-new-venture (legacy alias), new venture, new build, new project, scaffold a repo, spin up a venture/build, start a new app/tool, create a satellite repo, or init a design system / DESIGN.md (the deprecated jstack-ggdesign-init folds into the build path here)."
---

# jstack-init

Scaffold a new repo and wire it into the second brain in one deterministic shot. The brain coupling
is the whole point — repo and its brain hub are born together so a cold agent landing in either
discovers the other. This skill is a **thin intent router**: decide the path, then read the matching
reference and run the matching script. It does not duplicate per-path detail.

## Decide the path first

Two paths. Classify before scaffolding:

- **VENTURE** — a lean **work-product** satellite at `~/ventures/<slug>/`. The deliverable is
  strategy/services/GTM/clients, not source code. `AGENTS.md` is a pure router; the strategy lives
  in the brain. Choose when the thing *sells or delivers a service* and you'd track clients/ops, not
  a build/test/deploy loop.
- **BUILD** — a real **codebase** at `~/builds/<slug>/` (app, agent, internal tool, dashboard,
  library). The deliverable is shipped software. `AGENTS.md` is Karpathy-style coding guidelines.
  Choose when the thing *runs code* and has a build/test/deploy loop.

Decision rule: **delivers a service / strategy / GTM → VENTURE. Ships running software → BUILD.**
If a venture later needs an app, that app is its own BUILD (e.g. `~/ventures/stayframe` +
`~/builds/stayframe-qa`). If ambiguous, ask Jono one question: *"Is this a lean strategy/service
satellite (venture) or a codebase you'll build/run (build)?"*

## Route

| Path | Read | Then run |
|------|------|----------|
| **VENTURE** | `references/new-venture.md` | `python3 ~/jstack/skills/jstack-init/scripts/new_venture.py` |
| **BUILD** | `references/new-build.md` | `python3 ~/jstack/skills/jstack-init/scripts/new_build.py` |

Read the reference before running — it owns the inputs, the no-clobber safety, the brain gate, and
the size-cap lint for that path. Do not run the script from this file alone.

## Design system (build path only)

The deprecated `jstack-ggdesign-init` skill is **folded into the build path here**. When a build has
UI/frontend that needs design consistency, the build path initializes a Google `DESIGN.md` design
system deterministically (`new_build.py --with-design`, or `scripts/init_design.py --repo <path>`
later / standalone). Details live in `references/new-build.md`; format/lint reference in
`references/design/`.

## Next skills

| Next | When |
|------|------|
| `/jstack-savetobrain` | A durable decision/fact surfaced and should persist to the brain hub. |
| `/jstack-gtmarketing` | A new venture needs go-to-market strategy (the usual next move after scaffolding). |
| `/jstack-brainwork` | Pending raw captured for this venture/build needs compiling into the wiki. |
