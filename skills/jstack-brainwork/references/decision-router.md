# Brainwork Decision Router

Start in `${SECOND_BRAIN_PATH}` (default `~/second-brain`).

The router picks **exactly one route** from the user request. Apply the rules in order; the first matching rule wins. Word-level routing in the user's request always wins over automatic pending-raw detection.

## Rules

1. Parse the user request.
2. If request includes `dry run`, do not write. Route = **Dry run**.
3. If request includes a raw path (e.g. `raw/drops/2026-06-03-foo.md`), route = **Ingest** for that path.
4. If request includes `lint`, `check`, `graph`, `health`, `maintenance`, or `fix links`, route = **Maintenance**.
5. If request includes `all pending`, route = **Batch Ingest**.
6. Otherwise inspect pending raw with `references/pending-raw-triage.md` (which runs
   `python3 tools/sb.py pending` — the authoritative wiki-cross-referenced detector, **not** the cache).
7. If `pending > 0`, route = **Batch Ingest** — drain *all* pending newest-first. This is the default:
   a bare `/jstack-brainwork` from any fresh session means "re-read every new raw source and ingest it,"
   and the detector is stateless so a cold session finds exactly the un-ingested files. (Only narrow to
   a single source when the user named one, said `just the newest`/`one`, or token budget forces it —
   the batch runbook's "do what fits, report the rest" valve lets the next fresh session resume.)
8. If `pending: 0`, route = **Maintenance**.

## After choosing

Load only the needed runbook from this skill package:

- **Ingest** / **Batch Ingest** → `references/ingest-runbook.md`.
- **Maintenance** → `references/maintenance-runbook.md`.
- **Dry run** → no runbook; report intent and stop without writing.
- **No-op** → load `references/final-report.md` only.

Then load the canonical `llm-wiki` reference that runbook points to. Do not load every reference up front.

## Reporting the route

Always state the chosen route at the top of the final report, e.g. `Route: maintenance (user asked for lint)`, `Route: ingest (newest pending: raw/drops/2026-06-03-foo.md)`, or `Route: no-op (no pending raw, vault healthy)`.
