# Brainwork Maintenance Runbook

Load canonical references as needed:

- `${SECOND_BRAIN_PATH}/skills/llm-wiki/references/lint-operation.md`
- `${SECOND_BRAIN_PATH}/skills/llm-wiki/references/maintenance-operation.md`

Do not load both up front. Start with `lint-operation.md`; escalate to `maintenance-operation.md` only when running the full daily-maintenance cadence.

## Default deterministic sequence

```bash
python3 tools/sb.py lint
python3 tools/sb.py check
```

Read the reports. `lint` = `graph + check + pending` in one pass. If graph/check are clean **and**
`pending: 0`, this is a no-op route — emit the final report.

## Pending backlog is never silently left

`lint` now prints the ingest backlog (raw sources no wiki page references). If `pending > 0`, the
vault is **not** healthy even when graph/check are clean — captures from `/jstack-savetobrain` are
sitting unprocessed. Do not report a clean no-op. Instead surface the count and switch to the **Ingest**
/ **Batch Ingest** route (`references/ingest-runbook.md`) to drain it, then re-run `sb.py pending` to
confirm `0`. Word-level routing still wins: if the user explicitly asked only for `lint`/`check`, report
the backlog count but do not auto-ingest without their go-ahead.

## Index drift repair

If `check` reports index drift (entries missing from `wiki/index.md` or `[MISSING]` markers for deleted pages), recompile the index from page frontmatter:

```bash
python3 tools/sb.py index --write
python3 tools/sb.py check
```

Never hand-edit `wiki/index.md`. The compiler preserves curated section order.

## Safe link/path repair

Use `python3 tools/sb.py check --fix` **only** for safe single-match path corrections. After it runs, inspect `git diff` before keeping the changes. If a fix looks wrong, `git checkout -- <path>` to revert and surface the issue in the final report instead.

## Graph judgment

Run graph judgment from `lint-operation.md` when:

- The user asked for `graph` or `health`.
- `lint` reports graph issues (orphans, broken wikilinks, sparse communities, knowledge gaps).
- No pending raw exists and the invocation is general brainwork (i.e. the no-argument health route).

Skip expected orphans per `skills/llm-wiki/references/lint-pitfalls.md`.

## Logging

Append a lint/maintenance log entry only when changes are made:

```bash
python3 tools/sb.py log lint "<N> issues, <M> fixed" --updated "<pages>"
```

If nothing changed, do not log — report no-op in the final report instead.

## Final step

Always finish with `python3 tools/sb.py check` (must be clean) **and** `python3 tools/sb.py pending`
(should be `0`, or the remaining count reported). Hand control to `references/final-report.md`.
