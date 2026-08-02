# Brainwork Ingest Runbook

Load canonical reference:
`${SECOND_BRAIN_PATH}/skills/llm-wiki/references/ingest-operation.md`

Optionally load `skills/llm-wiki/references/capture-operation.md` for Step 2/3 post-capture reindex/log/check semantics if the raw source was just created by `/jstack-savetobrain`.

## Routing

For a raw source under `raw/drops/**`, use **Personal Ingest** (see `ingest-operation.md`).

For any other `raw/clips/**`, use **Standard Ingest** (see `ingest-operation.md`).

**Session synthesis:** in conversation drops, `## Verbatim` is the human's ground truth and
`## Session synthesis` is the session's agent-authored conclusions — the authoritative record of
what was decided. Compile wiki pages from the synthesis at matching fidelity (a rich synthesis
deserves a substantial venture-page section, not a one-liner); attribute its reasoning to the
session date; do not re-derive generic analysis when the drop already carries the specific one.

**Supersession:** honor `supersedes_hint:` in the raw frontmatter and the ingest Supersession Check —
apply the protocol in `skills/llm-wiki/references/supersession.md` automatically (the new source is
the authority during ingest). Source summaries are written as **hybrid cards**
(`skills/llm-wiki/references/source-card-template.md`; run `python3 tools/sb.py rawmap <raw>` for the
Raw map). Pages/sections marked superseded count as wiki changes in the final report.

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
python3 tools/sb.py cards
```

If `check` is not clean, report and stop. Do not paper over failures.

If `cards` lists **a page you just wrote or touched**, your card violates the template
(`skills/llm-wiki/references/source-card-template.md`) — fix it before reporting: body sections are
exactly `## Claims` / `## Raw map` / `## Load raw when` (+ optional `## See Also`); no narrative
sections; `> SUPERSEDED` markers go on the **old** page (or stale section), never on the new page.
Legacy pages already listed by `cards` are the pending sweep — leave them alone.

## hot.md refresh

Refresh `wiki/hot.md` (LLM judgment) only when current state actually changed: active projects, location, commitments, events, or a notable new learned topic. Keep `hot.md` ≤ ~50 lines.

## Batch ingest mode (`all pending`)

Get the worklist from `python3 tools/sb.py pending`. This is a two-stage flow: the **main session
groups**, then **one subagent ingests each group**.

**Model split.** The main orchestrator session runs on **Opus 4.8** or **Fable 5** (grouping and
coordination is the judgment-heavy part). Each ingest subagent is spawned on **Sonnet 5** — pass
`model: sonnet` (Sonnet 5) when spawning the Task/Agent subagent. Ingest-per-group is well-scoped
execution, so Sonnet 5 is the right cost/speed tier there; the expensive model stays on orchestration.

### Stage 1 — Main session: cluster pending raw into related-subject groups

Do NOT ingest inline. First, in the main context, read enough of each pending raw file (frontmatter
`title`/`tags`/`source`, and skim the body if needed) to cluster the worklist into **related-subject
groups** — sources that will land in the same or overlapping wiki pages/topics belong in one group.
Examples of a group: three clips on the same concept, a venture's session drop plus its follow-up
notes, several sources that all supersede or extend one existing page. A source with no relatives is
its own group of one. Every pending path lands in exactly one group (no source appears twice, none
dropped). Order groups newest-first by their most recent member.

### Stage 2 — One subagent per group, sequential

For each group, spawn **one** dedicated subagent (Task/Agent tool, `subagent_type: general-purpose`,
`model: sonnet` = Sonnet 5) that ingests **all raw sources in that group together**, then wait for it
to finish and read its
report before spawning the next group's subagent. Run them **one at a time, never in parallel** —
each ingest writes shared state (`wiki/index.md`, `raw/.ingest-cache.json`, `wiki/log.md`,
`wiki/hot.md`) via `tools/sb.py`, and concurrent subagents would collide on those files and corrupt
the index/cache. Grouping is what makes one-subagent-per-group correct: related sources hit the same
wiki page, so a single owner writes a coherent, unified page instead of fragmenting it across
subagents that would fight over the same file.

Brief each group subagent with:
- the exact list of raw paths in its group (and nothing outside the group);
- the subject/theme that ties the group together, so it composes unified pages rather than one card
  per source in isolation;
- the instruction to load this runbook + `skills/llm-wiki/references/ingest-operation.md` and follow
  Personal (`raw/drops/**`) vs Standard (`raw/clips/**`) ingest routing per path;
- the requirement to run `python3 tools/sb.py check` after its writes and **stop + report** if not clean;
- a short structured report back: raw paths ingested, wiki pages created/updated, supersession chains
  applied, `check` result, and whether any of its sources still show in `sb.py pending`.

After each subagent returns: if its `check` failed or any of its sources still appear in
`sb.py pending`, stop the batch and report — do not launch the next subagent on a broken vault.

**Drain-to-zero post-condition:** when the batch is done (or the user's scope is satisfied), run
`python3 tools/sb.py pending` again and confirm it reports `0`. If it does not, the batch is not
complete — report the exact remaining paths. A "successful" batch ingest that leaves `pending > 0` is
the failure mode this loop exists to prevent.

If token budget is low, dispatch subagents for as many groups as fit, then report the remaining
`sb.py pending` count so the next fresh `/jstack-brainwork` resumes — rather than cramming more
groups into one context that may truncate. (Subagent contexts are separate, so the constraint is the
orchestrator's budget for grouping + coordination, not the ingest work itself.)

## After a single ingest

Confirm the source you just ingested no longer appears in `python3 tools/sb.py pending`. If it still
does, the wiki pages you wrote did not reference the raw path — add the `sources:`/`raw:` ref (or a
body `Source:` line) so the source is provably ingested. The cache alone does not make a source
"ingested"; a wiki reference does.

## Pitfalls

**rawmap on sources without `#` headings:** `sb.py rawmap` scans for markdown ATX headings (`#`,
`##`, etc.). Raw sources that use plain-text section titles (common in NotebookLM exports, PDF
conversions, and some clipped articles) produce only a line-count line — no heading structure. When
this happens, scan the raw file and manually note key section landmarks in the Raw map (e.g., `L11
Clinical Dosing`, `L33 Circadian Kinetics`). The map still routes to correct line offsets even
without machine-parsed headings. Never skip the Raw map section just because the tool output is
minimal.

**cache check exit code for new files:** `sb.py cache check` returns exit code 2 for files not yet
in the cache. This is expected for first-time ingests — it means "changed/absent", not an error.
Proceed with ingest.

## Reporting

Hand control to `references/final-report.md` after writes complete (or after deciding to skip).
