---
name: jstack-sf-reel
description: Drive the entire StayFrame reel pipeline for one resort, end to end, as a re-entrant orchestrator. Use when Jono says /jstack-sf-reel, "make a reel for <resort>", "start the reel for <resort>", "harvest images for <resort>", "pull <resort>'s photos and build the reel", gives a Booking.com / Agoda listing link, or wants to advance a resort to its next step (harvest → screen → catalog → creative → produce). Detects which phase the resort is in from disk and runs forward to the next human gate. NOTE — iterating an in-progress reel from dashboard feedback is the separate lean /jstack-sf-check skill, not this one.
---

# jstack-sf-reel — one resort, the whole reel pipeline

A **re-entrant orchestrator**. Invoke it with a resort and it figures out where that resort is in the
pipeline from what's on disk, then runs forward **until it hits a human gate** and hands off. Each
re-invocation resumes at the next phase. The phase logic is here; each phase's mechanics live in a
one-hop reference under `references/`.

## Input (args)
- A **resort name** (`Serenity Sands`) → derive `slug` (`serenity-sands`), or
- a **Booking.com / Agoda listing URL** (used directly in harvest), and optionally
- a **reference reel** handle/URL for the creative phase (else it auto-mines).

All StayFrame paths are under `~/ventures/stayframe/`. Derive `slug` from the name (lowercase,
hyphenated) and confirm against existing `clients/<slug>/` and `qa/queues/*/manifest.json` `property`
fields if ambiguous.

## Phase detection (check top-down; the furthest artifact present wins)

| If on disk… | Phase | Load | Then |
|---|---|---|---|
| `clients/<slug>/briefs/*-brief.md` exists | **5 Produce** | `references/produce.md` | launch runsheet; iteration = `/jstack-sf-check` |
| `clients/<slug>/catalog.json` exists (≥1 approved) | **4 Creative** | `references/creative.md` | auto-mine + draft brief → **soft gate** (Jono approves) |
| a `reference-images` batch for slug is `completed:true` in `qa/verdicts/` | **3 Catalog** | `references/catalog.md` | run `refcatalog.py <slug>` → then Creative |
| a `qa/queues/*` batch for slug exists but **not** completed | **2 Screen** | — | **HARD GATE**: report screening status, point at localhost:7777, STOP |
| nothing for slug | **1 Harvest** | `references/harvest.md` | resolve URL → gallery → write screening batch → **HARD GATE** |

## Run-to-gate rule
After finishing a phase, **continue into the next phase in the same invocation** unless you've hit a
human gate. Gates that STOP the run:
- **Screen** (reference-images triage) — hard; Jono swipes in the dashboard.
- **Creative concept** — soft; Jono approves the chosen reel + drafted brief before produce.
- **GATE A / GATE B** — during produce; per-beat still/clip approval.

So a typical run after screening goes Catalog → Creative → (stop at concept approval) in one shot.
At every stop, tell Jono exactly what to do and that re-invoking `/jstack-sf-reel <resort>` (or
`/jstack-sf-check` to iterate) resumes.

## Explicit intent overrides detection
If Jono names a phase ("re-harvest more photos for X", "rebuild the catalog", "redo the concept"),
do that phase regardless of furthest-artifact state. A re-pull always writes a NEW batch (never
append to a triaged one).

## Dependencies (kept as tools, not folded in)
- **Harvest** calls `jstack-otagallery` (`scripts/booking_gallery.py`, OTA CDN patterns) — general skill.
- **Catalog / Creative** call `jstack-vision` (`gv`, Gemini on Vertex) for description + reel deconstruction.
- Drivers stay in `~/ventures/stayframe/tools/` (`refcatalog.py`, `briefsheet.py`) — references point at them.
- **Iteration is `/jstack-sf-check`** — the lean "I saved dashboard feedback, apply it" loop. Separate by design.
