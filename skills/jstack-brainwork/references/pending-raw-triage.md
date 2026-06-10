# Pending Raw Triage

A raw file is **pending** if it exists on disk and **no wiki page references it** — in frontmatter
(`source:`, `raw:`, or `sources:`) or anywhere in the page body. The wiki is ground truth; the
SHA256 cache (`raw/.ingest-cache.json`) is only a secondary speed hint and **can drift**, so do not
use it as the ledger.

## Fast path — one deterministic command

Run from anywhere inside the vault:

```bash
python3 tools/sb.py pending
```

Output is newest-first with a count (`pending: N`). `pending: 0` means no backlog. For automation:

```bash
python3 tools/sb.py pending --json
```

This is the single source of truth for the backlog number. Every agent (Claude Code, Hermes cron,
Codex) gets the same answer because the logic lives in `tools/sb.py`, not in a copy-pasted snippet.

> Historical note: an earlier version of this file shelled out a Python snippet that did
> `set(cache.keys())`. The cache is nested (`{"files": {...}, "ingested_at": ..., "rebuild": ...}`),
> so `cache.keys()` returned `["files", "ingested_at", "rebuild"]` and matched no raw paths — making
> **every** raw file look pending and massively inflating the count. Use `sb.py pending` instead; it
> cross-references the wiki, not the cache.

## Prioritization

`sb.py pending` already sorts newest-first. Prioritize newest `raw/drops/` unless the user
supplied a path or topic — drops are the canonical destination for `/jstack-savetobrain` captures, so
they are the highest-signal default for `/jstack-brainwork` follow-up.

If the user supplied a topic (e.g. "ingest the travel ones"), filter the pending list by directory
prefix.

## Token discipline

Do **not** read every raw file. Read only the candidate(s) needed to choose the next action — usually
just the first newest pending raw. Defer per-source analysis to the ingest runbook.

## Excluded zones (never pending)

`raw/scratch/**` is a working/holding area (e.g. session-transcript dumps), **not** an ingest
target. `sb.py pending` excludes it automatically and reports the excluded count separately. If a
durable fact lives in a scratch file, capture it as its own `raw/drops/` artifact via
`/jstack-savetobrain` rather than ingesting the transcript wholesale.

## Edge cases

- If `sb.py pending` shows a file you believe was ingested, the ingest never wrote a wiki reference to
  it (or the page was deleted). Re-ingest or add the missing `sources:`/`raw:` ref — that is the fix,
  not editing the cache.
- The SHA256 cache is only used to detect *content changes* for re-ingest (`sb.py cache check`), never
  to decide pending. Rebuild it from the wiki with `sb.py cache rebuild` if it has drifted.
