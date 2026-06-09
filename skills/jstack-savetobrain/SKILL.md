---
name: jstack-savetobrain
description: Save the current conversation/session's durable output — from a single fact up to the full intellectual synthesis of a strategy session — as a raw source in the user's second brain, without ingesting it yet. Use when the user says /jstack-savetobrain, save to brain, save this to the second brain, capture this, remember this in the second brain, or asks to preserve session state, decisions, synthesis, links, research, personal facts, project context, or reusable knowledge for later brainwork.
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
- Does **not** generate wiki prose, summaries, or interpretations of *external* sources (articles,
  transcripts, pastes stay verbatim). Recording the session's own synthesis in a conversation drop
  is NOT wiki generation — see Workflow step 6.
- Does **not** route into Personal Ingest, Standard Ingest, or any cascade.

Capture preserves what happened — the source as source, the session's output as the session's
output. Brainwork (compiling it into wiki/) is a separate invocation.

## Workflow

1. **Identify what this session produced that is worth keeping, and size the capture to it.** The unit ranges from a single durable fact (a shared link/article, a video URL, a pasted text block, a stated fact, a decision, a research request, a reusable idea) up to **the full intellectual output of a strategy/thinking session** (analysis, options considered and killed, decisions, open questions, next actions). Capture depth must be proportional to session richness — a thin session gets a thin drop; a session that worked out a business direction gets everything, so a brand-new session can read the drop and know exactly what was discussed and decided.
2. **Pick the destination** by matching `capture-operation.md` Step 1's input table. Conversation-derived material with no external source goes under `raw/personal/drops/YYYY-MM-DD-<slug>.md` unless a more specific personal/project raw directory clearly already exists (e.g. `raw/personal/travel/`, `raw/personal/ventures/`).
3. **Slugify** the title (lowercase, hyphenated). Personal facts about the human go under `raw/personal/`. Other topics go under `raw/<topic>/`.
4. **Reuse, don't duplicate.** Before creating the file, check `raw/.ingest-cache.json` and likely existing raw paths for matching slugs or matching SHA256 of identical content. If an artifact for this content already exists, reuse it and report that — do not create a near-duplicate.
5. **Materialize** using the right template:
   - Conversation/text/article → `references/raw-template.md`. Set `source: conversation` for session-derived drops; otherwise set the originating URL or paste origin.
   - YouTube / video → `references/youtube-transcript-template.md`. Fetch the transcript; light cleanup only.
6. **Write the raw file** with valid frontmatter (`title`, `source`, `author`, `published`, `collected`, `tags`) and the source content preserved verbatim where applicable. Do not editorialize.
   **Conversation drops — provenance-separated body, scaled to richness.** `raw/` integrity means
   *nothing that didn't happen* — not *nothing agent-authored*. The user's words and the session's
   synthesis are both things that happened; they must both survive, in clearly separated sections:

   - `## Verbatim` — the user's own load-bearing words, quoted exactly (blockquote): decisions,
     facts, constraints, corrections. The ground truth of what the human said. Never paraphrased.
   - `## Session synthesis` — agent-authored record of the intellectual output this session
     actually produced: what was analyzed, options considered and **killed (with the reasons)**,
     what was decided and why, what remains open, agreed next actions. **Transcribe, don't create:**
     every claim here must be a conclusion actually reached in this session's transcript. Recording
     that output at full fidelity is *required* — a rich strategy session may need a long, detailed
     section (hundreds of lines is fine); losing it is the failure mode this section exists to
     prevent. Producing NEW analysis at save time (numbers, comparisons, plans that never appeared
     in the session) is forbidden. If the session produced no synthesis beyond the user's words,
     omit the section entirely — never pad it.
   - `## Session context` (optional) — links shared, artifacts produced this session (by path),
     related brain pages (cite by path; never restate their content as session output).

   When `## Session synthesis` is present, add `synthesis_by: "<model/harness>"` to the frontmatter
   so the synthesis is always attributable — it is the session's conclusions, never the human's
   words and never an external source.
7. **Supersession hint.** If the user stated the new content *replaces* an earlier decision/plan/fact ("we pivoted", "scrap X, now Y", "this replaces the earlier plan"), add `supersedes_hint: ["<free text or wiki path>"]` to the raw frontmatter. Metadata on the new drop only — still no wiki writes. Brainwork's ingest resolves the hint and applies the supersession protocol (`skills/llm-wiki/references/supersession.md`).
8. **Stop.** Do not touch `wiki/` or run any `tools/sb.py` subcommand.

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

## Regression case (why Session synthesis exists — do not regress to verbatim-only)

2026-06-10: a long strategy session progressively killed four niches with reasons, converged on a
service-as-software business shape, and landed a full hospitality content-operator strategy — almost
all of it agent synthesis in response to the user's questions. Savetobrain (then verbatim-only)
captured just the user's quotes; the entire synthesis survived only because brainwork was run
manually while the transcript was still live (result: `wiki/personal/ventures/thai-ai-ugc-agency.md`
§"Direction pivot (2026-06-10)"). Correct behavior for that session: a long `## Session synthesis`
covering the niche kills + reasons, the business-shape principles, and the full service model. Test
yourself against it: if your drop for a session like that is under a screen of text, you lost the
session's output.

The inverse failure also happened (same date): given a thin session, a capture agent *invented*
margins, comps, and next-step plans that were never discussed. Both failures are the same bug —
the drop not matching what actually happened. Capture everything that happened; nothing that didn't.

## Guardrails

- Conversation-derived material still needs explicit user confirmation per `AGENTS.md` §2, unless the user already said `save this` / `add to brain` / `capture` / `/jstack-savetobrain` / `research X`. Offering is free; writing needs a yes.
- `raw/` is immutable. If a conversation fact must be saved and an old raw artifact is wrong, create a new raw artifact rather than editing the old one.
- Token discipline: do not read the whole vault. Read `AGENTS.md`, the capture reference, and the chosen raw template. Spot-check `raw/.ingest-cache.json` and the target directory for duplicates.
