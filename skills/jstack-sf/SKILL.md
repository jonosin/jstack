---
name: jstack-sf
description: "StayFrame front door: routes by intent + current state to jstack-sf-reel (run the pipeline), jstack-sf-check (apply dashboard feedback), or the right playbook/index.md craft doc. Bare invocation = read-only status (where am I / next gate / next step), no render. Keeps both workhorse skills independently invocable."
---

# jstack-sf — StayFrame front door (router)

The one StayFrame command. It reads intent + current state and **dispatches** — it never re-implements
phase logic, feedback logic, or craft rules. The workhorses (`jstack-sf-reel`, `jstack-sf-check`) and
the playbooks stay the source of truth; this skill points at the right one.

All paths under `~/ventures/stayframe/` (abbrev `SF`). The canonical map is `SF/playbook/index.md`
(pipeline → playbook, and the engine matrix). When a craft/engine question comes up, open that.

## Awareness: explicit intent wins; bare invocation = status

- **If Jono names what he wants**, do that (the table below). His words override detection — same rule
  `jstack-sf-reel` uses internally.
- **If he just says `/jstack-sf`** (no intent), run **status mode** (read-only — see below). Never
  auto-launch a render on a bare call; rendering spends credits and is Jono's call.

## Dispatch table

| Jono says / state shows | Do |
|---|---|
| bare `/jstack-sf`, "where am I", "status", "what's next" | **status mode** (read-only report + one recommended command). No render, no write. |
| "make / build / start / render / harvest / advance the reel for <resort>", "go" | invoke **`jstack-sf-reel`** (it self-detects phase from disk and runs to the next gate) |
| "I saved feedback", "check the dashboard", "I left a note", "iterate <reel>"; or a `SF/qa/reels/*.json` has an actionable (non-empty `note`) `feedback` entry | invoke **`jstack-sf-check`** |
| "what's the rule for <step>", "which engine / prompt format", or about to do a craft sub-step | open **`SF/playbook/index.md`** → route to the governing playbook + engine-matrix row. No sub-skill. |

If both an advance intent and pending feedback exist, surface the feedback first (`jstack-sf-check`),
then advancing is the next step — don't silently skip his notes.

## Status mode (this skill's own job — read-only, no side effects)

This is what makes the router more than an alias: a safe "where am I / what's next" that neither
workhorse offers (`-reel` runs forward and spends credits; `-check` applies feedback). Steps:

1. **Resolve the active resort/reel.** From the most recently touched `SF/clients/<slug>/` (or ask if
   ambiguous). Reel id = `<client>__<reel>`.
2. **Detect phase** with the same furthest-artifact logic `jstack-sf-reel` documents (brief exists →
   Produce; `catalog.json` → Creative; completed screen batch → Catalog; open batch → Screen; nothing
   → Harvest).
3. **Read produce sub-step + gates** from `SF/qa/reels/<reel_id>.json` `steps`
   (refok→still→gatea→clip→gateb→saved) and pending `feedback` (non-empty notes only).
4. **Name the governing playbook** for the next sub-step from `SF/playbook/index.md` §1.
5. **Report**, terse: `resort · phase · next gate · pending feedback (n) · next-step playbook` and a
   single **recommended command** (`/jstack-sf-check` if feedback pending, else `/jstack-sf-reel` to
   advance, else the relevant gate is on Jono in the dashboard).

Read files; write nothing. Do not call the generation engines.

## Stays thin / separation guarantee

- **No duplication.** Phase detection, gate handling, and per-beat production live in `jstack-sf-reel`
  (+ its `references/`). Feedback apply lives in `jstack-sf-check`. Engine matrix + craft rules live in
  `SF/playbook/`. This skill only decides *which* of those to hand off to.
- **Both workhorses remain directly invocable.** `/jstack-sf-reel <resort>` and `/jstack-sf-check`
  still work exactly as before — this router is an additive front door, not a wrapper that hides them.

## See also
- `SF/playbook/index.md` — pipeline map + canonical engine matrix (Seedance / Kling O3 / Nano Banana / GPT Image 2) + higgsfield reference map.
- `jstack-sf-reel` — the pipeline orchestrator. `jstack-sf-check` — the dashboard-feedback loop.
- `SF/tools/sf_lint.py` — freshness gate (run in maintenance/pre-commit).
