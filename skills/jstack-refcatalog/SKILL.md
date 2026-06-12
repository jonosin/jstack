---
name: jstack-refcatalog
description: Build or refresh a StayFrame client's reference-image catalog after Jono confirms a QA batch. Use when the user says /jstack-refcatalog, "build the catalog", "refresh the catalog", "run the catalog pass", "catalog the references", or has just finished swiping/marking a reference-images batch done and wants the approved photos promoted and described. Promotes approved photos into the client folder, describes only NEW images via jstack-vision (Gemini on Vertex — zero Claude vision tokens), and rebuilds catalog.json from current verdicts.
---

# jstack-refcatalog — confirm batch → client reference catalog

One command turns Jono's QA swipes into the client's queryable reference database:

```bash
python3 ~/ventures/stayframe/tools/refcatalog.py <property-slug>
```

The driver owns all logic (this skill is a thin invoker — don't reimplement steps):

1. **PROMOTE** — approved images from every *completed* `reference-images` batch for the
   property are copied `qa/queues/*/media/` → `clients/<slug>/refs/`; copies whose approval
   was revoked get pruned.
2. **DESCRIBE** — only ids missing an envelope in `clients/<slug>/.gv-raw/` go to Gemini
   (`gv`, jstack-vision wrapper, Vertex billing). Re-runs are free; the envelopes are the
   cache. To force a re-describe, delete that id's envelope file.
3. **ASSEMBLE** — `clients/<slug>/catalog.json`: per image, `objective` (Gemini's physical
   description) + `curation` (Jono's verdict/tags/note, re-read every run) merged with
   `clients/<slug>/catalog-overrides.json` (`hero` ids, per-id `caveats`).

## Protocol

1. Resolve the property slug. If the user doesn't name one, list candidates from
   `~/ventures/stayframe/qa/queues/*/manifest.json` `property` fields; if there is exactly
   one, use it without asking.
2. If no batch for the property is `completed: true` in `qa/verdicts/`, stop and say which
   batches are still open — never catalog an unconfirmed batch.
3. Run the driver. Stream its stdout to the user (it reports promote/describe/assemble
   counts and failures).
4. On `FAIL <id>` lines: re-run the driver once (envelope cache makes it cheap); if it
   still fails, report the ids and stop — do not describe those images with Claude vision.
5. Report: image count, new-describe count (Gemini spend), pruned count, catalog path.

## Semantics consumers must respect (pointer, not copy)

`~/ventures/stayframe/clients/AGENTS.md` is the binding contract for *reading* the catalog
(`context_only` = intel never a frame · `defect_tags` = what MUST change · `note`/`caveat`
precedence · hero confirmation via one gv call). `qa/AGENTS.md` owns verdict semantics.

## Notes

- Path is currently StayFrame-specific by design; if another venture grows a catalog need,
  generalize the driver's ROOT, don't fork the skill.
- Heavy outputs (`refs/`, `.gv-raw/`) are gitignored; `catalog.json` and overrides are
  tracked — commit them after a successful run if the repo is clean enough to commit.
