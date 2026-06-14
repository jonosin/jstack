# Phase 3 — Catalog (approved photos → queryable reference DB)

Precondition: at least one `reference-images` batch for the slug is `completed: true` in
`~/ventures/stayframe/qa/verdicts/`. Never catalog an open batch — if none is complete, report which
batches are still open and stop.

## Run the driver (owns all logic — don't reimplement)
```bash
python3 ~/ventures/stayframe/tools/refcatalog.py <slug>
```
1. **PROMOTE** — approved images from every completed `reference-images` batch → `clients/<slug>/refs/`
   (copies whose approval was revoked are pruned).
2. **DESCRIBE** — only ids missing a `clients/<slug>/.gv-raw/` envelope go to Gemini (`gv`,
   jstack-vision, Vertex billing). The envelopes are the cache — re-runs are free. Force a
   re-describe by deleting that id's envelope (never wipe `.gv-raw/`).
3. **ASSEMBLE** — `clients/<slug>/catalog.json`: `objective` (Gemini description) + `curation`
   (Jono's verdict/tags/note, re-read each run) + `catalog-overrides.json` (hero ids, caveats).

## Single-image / --add mode
Jono pointed at specific image(s)? Run per image instead of the batch flow:
```bash
python3 ~/ventures/stayframe/tools/refcatalog.py <slug> --add <path> [--note "<verbatim>"] [--context]
```
Registers in `direct-adds.json` (survives rebuilds), describes only that image. `--context` = it's
intel, not frame-worthy.

## On `FAIL <id>` lines
Re-run the driver once (cache makes it cheap). Still failing → report the ids and stop; never fall
back to Claude vision.

## Semantics (pointer, not copy)
Reading the catalog is governed by `~/ventures/stayframe/clients/AGENTS.md` (`context_only` = intel
never a frame · `defect_tags` = what MUST change · `note`/`caveat` precedence · hero confirmation).
`qa/AGENTS.md` owns verdict semantics.

## Hand off
Report: image count, new-describe count (= Gemini spend), pruned count, catalog path. `catalog.json`
+ overrides are git-tracked (commit after a clean run if the repo is tidy); `refs/` + `.gv-raw/` are
gitignored. → next phase: **creative**.
