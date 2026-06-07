---
name: jstack-savetobrain
description: Save the smallest durable unit from the current conversation/session as a raw source in the user's second brain, without ingesting it yet. Use when the user says /jstack-savetobrain, save to brain, save this to the second brain, capture this, remember this in the second brain, or asks to preserve session context, decisions, links, research, personal facts, project context, or reusable knowledge for later brainwork.
user_invocable: true
---

# jstack-savetobrain — raw capture only

Cheap, fast, raw-only capture for the second brain. This skill **only** materializes a raw artifact under `raw/` and stops. The heavier follow-up work (ingest, index, log, lint, graph, hot.md refresh) is deferred to `jstack-brainwork`.

## Operating contract

Before writing anything:

1. Read `${SECOND_BRAIN_PATH}/AGENTS.md` for the live contract (`SECOND_BRAIN_PATH` from `~/.jstack/config.env`, default `~/second-brain`).
2. Treat `${SECOND_BRAIN_PATH}/SKILL.md` as a compatibility router only — it is a symlink to `skills/llm-wiki/SKILL.md`.
3. Load `${SECOND_BRAIN_PATH}/skills/llm-wiki/references/capture-operation.md` and execute **only Step 1: Materialize or reuse the raw artifact**.
4. Load `skills/llm-wiki/references/raw-template.md` for conversation/text/article raw markdown, or `skills/llm-wiki/references/youtube-transcript-template.md` for video transcripts.

Do not load `skills/llm-wiki/references/ingest-operation.md` unless the user explicitly asks to ingest immediately in the same invocation. If they do, hand off to `jstack-brainwork` afterward rather than running it inline.

## Hard scope — what this skill does NOT do

- Does **not** update `wiki/`, `wiki/index.md`, `wiki/log.md`, or `wiki/hot.md`.
- Does **not** run any *writing* `tools/sb.py` subcommand (`index --write`, `graph`, `lint`, `cache add`).
  The one allowed call is the read-only `tools/sb.py pending` in the final report, purely to surface
  the growing backlog so deferred work stays visible (see Final report).
- Does **not** generate wiki prose, summaries, interpretations, or conclusions about the source.
- Does **not** route into Personal Ingest, Standard Ingest, or any cascade.

Capture preserves the source as source. Brainwork is a separate invocation.

## Workflow

1. **Identify the smallest durable unit** worth keeping from the current conversation: a shared link/article, a YouTube/video URL, a pasted text block, a stated durable fact about the user, a project context note, a decision, a research request, or a reusable idea.
2. **Pick the destination** by matching `capture-operation.md` Step 1's input table. Conversation-derived material with no external source goes under `raw/personal/drops/YYYY-MM-DD-<slug>.md` unless a more specific personal/project raw directory clearly already exists (e.g. `raw/personal/travel/`, `raw/personal/ventures/`).
3. **Slugify** the title (lowercase, hyphenated). Personal facts about the human go under `raw/personal/`. Other topics go under `raw/<topic>/`.
4. **Reuse, don't duplicate.** Before creating the file, check `raw/.ingest-cache.json` and likely existing raw paths for matching slugs or matching SHA256 of identical content. If an artifact for this content already exists, reuse it and report that — do not create a near-duplicate.
5. **Materialize** using the right template:
   - Conversation/text/article → `references/raw-template.md`. Set `source: conversation` for session-derived drops; otherwise set the originating URL or paste origin.
   - YouTube / video → `references/youtube-transcript-template.md`. Fetch the transcript; light cleanup only.
6. **Write the raw file** with valid frontmatter (`title`, `source`, `author`, `published`, `collected`, `tags`) and the source content preserved verbatim where applicable. Do not editorialize.
7. **Stop.** Do not touch `wiki/` or run any `tools/sb.py` subcommand.

## Final report

Capturing creates an **ingest debt**: the raw file exists but no wiki page references it yet, so it
counts as pending until `/jstack-brainwork` processes it. Surface that debt so it never accumulates
invisibly — run the read-only detector and report the count:

```bash
python3 tools/sb.py pending   # read-only; do not pass --json here, just read the count
```

Then keep the report to two lines:

```
Saved raw source: raw/<topic>/<file>.md. Brainwork deferred.
Pending ingest backlog: <N> source(s). Run /jstack-brainwork (or `all pending`) to process.
```

If the artifact already existed and was reused without changes, say so explicitly:

```
Reused existing raw source: raw/<topic>/<file>.md (no change). Brainwork deferred.
Pending ingest backlog: <N> source(s). Run /jstack-brainwork to process.
```

If the count is climbing (several pending), gently recommend running `/jstack-brainwork all pending`
or letting the nightly maintenance cron drain it — captures are only worth keeping if they get ingested.

## Guardrails

- Conversation-derived material still needs explicit user confirmation per `AGENTS.md` §2, unless the user already said `save this` / `add to brain` / `capture` / `/jstack-savetobrain` / `research X`. Offering is free; writing needs a yes.
- `raw/` is immutable. If a conversation fact must be saved and an old raw artifact is wrong, create a new raw artifact rather than editing the old one.
- Token discipline: do not read the whole vault. Read `AGENTS.md`, the capture reference, and the chosen raw template. Spot-check `raw/.ingest-cache.json` and the target directory for duplicates.
