---
name: jstack-brainwork
description: Process deferred second-brain work after raw capture. Use after /jstack-savetobrain, when the user says brainwork, process the brain, ingest saved drops, compile raw sources, lint the second brain, check the brain, run graph, run maintenance, fix wiki links, or decide what second-brain work is needed.
user_invocable: true
---

# jstack-brainwork — router for deferred second-brain work

The follow-up operator that runs after `jstack-savetobrain`. This skill is intentionally a **router**, not a workflow. It inspects the request and current vault state, picks one route, then loads only the references needed for that route.

## Operating contract

Before deciding anything:

1. Read `${SECOND_BRAIN_PATH}/AGENTS.md` for the live contract (`SECOND_BRAIN_PATH` from `~/.jstack/config.env`, default `~/second-brain`).
2. Treat `${SECOND_BRAIN_PATH}/SKILL.md` as the canonical operation router (symlink to `skills/llm-wiki/SKILL.md`).
3. Load `references/decision-router.md` from this skill package (`skills/jstack-brainwork/references/decision-router.md`).
4. Only after choosing a route, load the runbook for that route. Do not load all references at once.

Work from `${SECOND_BRAIN_PATH}`. Never use `cd` chains; `tools/sb.py` resolves the vault automatically.

## Available routes

The router in `references/decision-router.md` chooses one of:

| Route | When | Local reference | Canonical references to load only after choosing |
|---|---|---|---|
| Batch Ingest (default) | Pending raw exists and the user did not ask for maintenance — bare `/jstack-brainwork` or `all pending`. Drains **all** pending newest-first; the next fresh session resumes if budget runs out | `references/ingest-runbook.md` | `skills/llm-wiki/references/ingest-operation.md` |
| Ingest (single) | A specific raw path is given, or the user said `just the newest`/`one` | `references/ingest-runbook.md` | `skills/llm-wiki/references/ingest-operation.md`, optionally `capture-operation.md` Step 2/3 |
| Maintenance | User asked for `lint`, `check`, `graph`, `health`, `maintenance`, or `fix links`; or no pending raw exists | `references/maintenance-runbook.md` | `skills/llm-wiki/references/lint-operation.md`, optionally `maintenance-operation.md` |
| Dry run | User asked for `dry run` | `references/decision-router.md` (no writes) | none |
| No-op | Nothing to do | `references/final-report.md` | none |

For schema or path questions while routing, consult `skills/llm-wiki/references/architecture-and-toolkit.md` and `conventions.md`.

## How to find pending raw

Use `references/pending-raw-triage.md`. It reads `raw/.ingest-cache.json` as the processed-source ledger and lists unprocessed raw files newest-first. Do not read every raw file. Read only candidates needed to choose the next action.

## Hard rules (inherited from `llm-wiki`)

- Always use `tools/sb.py` for index, log, cache, check, graph, and lint. Never hand-edit `wiki/index.md` or `wiki/log.md`.
- After any write, run `python3 tools/sb.py check`. Report if it is not clean.
- **Card-structure lint matches savetobrain's ingest-time check.** Before compiling a raw source into a wiki page, confirm it carries the same minimum frontmatter savetobrain enforces at write time (`title`, `source`, `collected`, `tags`, plus `supersedes`/`supersedes_hint` when present). A raw file missing these is a savetobrain-side defect — flag it in the final report rather than silently patching around it, so the lint backlog doesn't grow.
- **Surface `supersedes`/`supersedes_hint` chains during processing.** When ingesting a raw source that carries either key, resolve it against the vault, apply the wiki-side supersession protocol (`status: superseded` + `superseded_by:` + `superseded_on:` on the superseded page, per `llm-wiki` conventions), and name the chain explicitly in the final report (`X supersedes Y`) so stale facts stay discoverable rather than silently orphaned.
- Refresh `wiki/hot.md` (LLM judgment) only when current state actually changed: active projects, location, commitments, events, or notable new learned topics.
- Conversation-derived material still needs explicit user confirmation. Brainwork operates on already-saved raw sources by default; it does not capture new ones (that's `jstack-savetobrain`).
- Word-level routing wins: if the user says `lint`/`check`/`graph`/`health`/`maintenance`/`fix links`, choose Maintenance even when pending raw exists. If the user says `dry run`, do not write.

## Workflow

1. Parse the user's request and arguments.
2. Run `references/decision-router.md` to pick exactly one route.
3. If routing requires it, run `references/pending-raw-triage.md` to enumerate pending raw.
4. Load the corresponding runbook only:
   - Ingest / Batch Ingest → `references/ingest-runbook.md`.
   - Maintenance → `references/maintenance-runbook.md`.
   - Dry run → skip writes; report the chosen action and why.
5. After any writes, run `python3 tools/sb.py check` and confirm it is clean.
6. Emit the final report per `references/final-report.md`.

## Final report

Always emit per `references/final-report.md`: one to four short lines covering chosen route, raw sources processed (or why none), wiki/support files changed, `tools/sb.py check` result, and remaining pending work.

## Next skills

| Next | When |
|------|------|
| `/jstack-savetobrain` | Standalone terminal step — brainwork drains the backlog; capture a new session before there is anything to process. |
| `/jstack-brainwork` (re-invoke) | Batch Ingest ran out of budget — a fresh `/jstack-brainwork` resumes the remaining pending raw. |
