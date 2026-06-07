# Brainwork Ingest Runbook

Load canonical reference:
`${SECOND_BRAIN_PATH}/skills/llm-wiki/references/ingest-operation.md`

Optionally load `skills/llm-wiki/references/capture-operation.md` for Step 2/3 post-capture reindex/log/check semantics if the raw source was just created by `/jstack-savetobrain`.

## Routing

For a raw source under `raw/personal/**`, use **Personal Ingest** (see `ingest-operation.md`).

For any other `raw/<topic>/**`, use **Standard Ingest** (see `ingest-operation.md`).

## Before writing wiki pages

Verify the SHA256 incremental cache:

```bash
shasum -a 256 raw/<path>.md
python3 tools/sb.py cache check raw/<path>.md
```

If the hash matches an existing cache entry, the file has not changed since last ingest. Skip and report; do not duplicate work.

## After wiki writes

```bash
python3 tools/sb.py index --write
python3 tools/sb.py cache add raw/<path>.md
python3 tools/sb.py log ingest "<summary>" --source raw/<path>.md --created "<titles>" --updated "<titles>"
python3 tools/sb.py check
```

If `check` is not clean, report and stop. Do not paper over failures.

## hot.md refresh

Refresh `wiki/hot.md` (LLM judgment) only when current state actually changed: active projects, location, commitments, events, or a notable new learned topic. Keep `hot.md` ≤ ~50 lines.

## Batch ingest mode (`all pending`)

Get the worklist from `python3 tools/sb.py pending` and iterate newest-first. After each ingest, run
`python3 tools/sb.py check`; if it fails, stop and report.

**Drain-to-zero post-condition:** when the batch is done (or the user's scope is satisfied), run
`python3 tools/sb.py pending` again and confirm it reports `0`. If it does not, the batch is not
complete — report the exact remaining paths. A "successful" batch ingest that leaves `pending > 0` is
the failure mode this loop exists to prevent.

If token budget is low, ingest one source and report the remaining `sb.py pending` count for the next
invocation rather than attempting a multi-source ingest that may truncate.

## After a single ingest

Confirm the source you just ingested no longer appears in `python3 tools/sb.py pending`. If it still
does, the wiki pages you wrote did not reference the raw path — add the `sources:`/`raw:` ref (or a
body `Source:` line) so the source is provably ingested. The cache alone does not make a source
"ingested"; a wiki reference does.

## Reporting

Hand control to `references/final-report.md` after writes complete (or after deciding to skip).
