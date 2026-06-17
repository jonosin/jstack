---
name: jstack-sf
description: "StayFrame front door: routes by intent + current state to jstack-sf-new (start/run the pipeline for a resort), jstack-sf-check (apply dashboard feedback), jstack-sf-learn (promote a passed reel's method to canon), or the right playbook/index.md craft doc. Bare invocation = read-only status (where am I / next gate / next step), no render. Keeps the workhorse skills independently invocable."
---

# jstack-sf — StayFrame front door (router)

The one StayFrame command. It reads intent + current state and **dispatches** — it never re-implements
phase logic, feedback logic, or craft rules. The workhorses (`jstack-sf-new`, `jstack-sf-check`,
`jstack-sf-learn`) and the playbooks stay the source of truth; this skill points at the right one.

All paths under `~/ventures/stayframe/` (abbrev `SF`). The canonical map is `SF/playbook/index.md`
(pipeline → playbook, and the engine matrix). When a craft/engine question comes up, open that.

## Awareness: explicit intent wins; bare invocation = status

- **If Jono names what he wants**, do that (the table below). His words override detection — same rule
  `jstack-sf-new` uses internally.
- **If he just says `/jstack-sf`** (no intent), run **status mode** (read-only — see below). Never
  auto-launch a render on a bare call; rendering spends credits and is Jono's call.

## Dispatch table

| Jono says / state shows | Do |
|---|---|
| bare `/jstack-sf`, "where am I", "status", "what's next" | **status mode** (read-only report + one recommended command). No render, no write. |
| "make / build / start / render / harvest / advance the reel for <resort>", "go" | invoke **`jstack-sf-new`** (it self-detects phase from disk and runs to the next gate) |
| "I saved feedback", "check the dashboard", "I left a note", "iterate <reel>"; or a `SF/qa/reels/*.json` has an actionable (non-empty `note`) `feedback` entry | invoke **`jstack-sf-check`** |
| "the reel passed", "what did we learn", "promote to canon", "save the method"; or a reel just cleared every GATE B and was assembled | invoke **`jstack-sf-learn`** (diff brief method vs `playbook/`, write the proven rule into the playbook + `DECISIONS.md`; canon is the home — no brain copy) |
| "lead list", "add/enrich leads", "prospect table", "S6", "rank leads", "S7" | invoke **`jstack-sf-leads`** (canonical prospect CSV, Apify enrichment, S7 ranked file) |
| "outreach", "cold DM/email", "first 50 sends", "contact leads", "owner contact" | invoke **`jstack-sf-outreach`** (S7/S8 message/channel playbook; drafts route to `jstack-msgdraft`) |
| "what's the rule for <step>", "which engine / prompt format", or about to do a craft sub-step | open **`SF/playbook/index.md`** → route to the governing playbook + engine-matrix row. No sub-skill. |

If both an advance intent and pending feedback exist, surface the feedback first (`jstack-sf-check`),
then advancing is the next step — don't silently skip his notes.

## Status mode (this skill's own job — read-only, no side effects)

This is what makes the router more than an alias: a safe "where am I / what's next" that neither
workhorse offers (`-reel` runs forward and spends credits; `-check` applies feedback). Steps:

1. **Resolve the active resort/reel.** From the most recently touched `SF/clients/<slug>/` (or ask if
   ambiguous). Reel id = `<client>__<reel>`.
2. **Detect phase** with the same furthest-artifact logic `jstack-sf-new` documents (brief exists →
   Produce; `catalog.json` → Creative; completed screen batch → Catalog; open batch → Screen; nothing
   → Harvest).
3. **Read produce sub-step + gates** from `SF/qa/reels/<reel_id>.json` `steps`
   (refok→still→gatea→clip→gateb→saved) and pending `feedback` (non-empty notes only).
4. **Name the governing playbook** for the next sub-step from `SF/playbook/index.md` §1.
5. **Report**, terse: `resort · phase · next gate · pending feedback (n) · next-step playbook` and a
   single **recommended command** (`/jstack-sf-check` if feedback pending, else `/jstack-sf-new` to
   advance, else the relevant gate is on Jono in the dashboard).

Read files; write nothing. Do not call the generation engines.

## Stays thin / separation guarantee

- **No duplication.** Phase detection, gate handling, and per-beat production live in `jstack-sf-new`
  (+ its `references/`). Feedback apply lives in `jstack-sf-check`. Engine matrix + craft rules live in
  `SF/playbook/`. This skill only decides *which* of those to hand off to.
- **Both workhorses remain directly invocable.** `/jstack-sf-new <resort>` and `/jstack-sf-check`
  still work exactly as before — this router is an additive front door, not a wrapper that hides them.

## See also
- `SF/playbook/index.md` — pipeline map + canonical engine matrix (Seedance / Kling O3 / Nano Banana / GPT Image 2) + higgsfield reference map.
- `jstack-sf-new` — the pipeline orchestrator (start a resort → finished reel). `jstack-sf-check` — the dashboard-feedback loop. `jstack-sf-learn` — promote a passed reel's method to canon.
- `SF/tools/sf_lint.py` — freshness gate (run in maintenance/pre-commit).

## Next skills

| Next | When |
|------|------|
| `/jstack-sf-new <resort>` | Advance the pipeline to its next gate (or start a resort). |
| `/jstack-sf-check` | Feedback is pending in the dashboard — apply it, then iterate. |
| `/jstack-vidgen` | At the Render Gate and generating agent-side (stills/clips) — the universal video-gen router (asks duration+resolution, shows the exact prompt + craft skill, no dup-frame). |
| `/jstack-sf-learn` | A reel just cleared every GATE B — promote what worked to canon. |
| `/jstack-sf-leads` | Add, enrich, validate, or rank prospect leads. |
| `/jstack-sf-outreach` | Turn ranked leads into contact strategy, message drafts, and the first manual send plan. |
