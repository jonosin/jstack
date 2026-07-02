---
name: jstack-savetobrain
description: >
  Save durable output to the second brain. Routes: (1) YouTube URL → deterministic
  transcript capture via references/youtube-route.md; (2) X/Twitter URL →
  deterministic raw clip capture via references/x-link-route.md; (3) conversation
  content → curated raw drop from session. Use when the user says /jstack-savetobrain,
  save to brain, save this to the second brain, capture this, remember this in the
  second brain, or provides a YouTube/X link to save in the brain.
user_invocable: true
---

# jstack-savetobrain — curate this session into the brain

## Intent router — read this first

Before any other action, check the user's input:

1. **YouTube URL detected** (`youtube.com/watch`, `youtu.be/`, `youtube.com/shorts`, `youtube.com/live`) → load `references/youtube-route.md` and follow it exactly. Do not read the rest of this SKILL.md — the YouTube route is self-contained and deterministic.
2. **X/Twitter URL detected** (`x.com/<handle>/status/<id>`, `twitter.com/<handle>/status/<id>`) → load `references/x-link-route.md` and follow it exactly. Do not read the rest of this SKILL.md — the X route is self-contained and deterministic for raw clip capture.
3. **Conversation content** (decisions, facts, synthesis, links, external non-YouTube/X content) → continue below.

## What you are writing into

The second brain (`${SECOND_BRAIN_PATH}` from `~/.jstack/config.env`, default `~/second-brain`) is
an **agent-only system of record**. No human reads it. It has two layers:

- `raw/` — the ground-truth layer. Immutable, append-only. Only things that actually happened:
  what the user said, what a session actually concluded, what an external source actually contains.
- `wiki/` — compiled knowledge. A *different* agent (`/jstack-brainwork`) builds it later by
  reading `raw/`. Every future agent that plugs into this brain answers from the wiki and escalates
  to raw for work-grade tasks.

**You are the only agent that will ever see this full session.** When it ends, everything not
written down is gone. Everything you do write becomes permanent context that every future agent
inherits. You are the curator standing between this conversation and every agent that comes after —
under-save and future agents lose the session's output forever; over-save noise and you bloat the
ground-truth layer every future agent pays tokens to read.

Both failures have actually happened (2026-06-10):
- **Under-save:** a 2-hour strategy session killed four niches with reasons and landed a full
  business direction. The capture kept only the user's literal quotes; the synthesis — the valuable
  output — was nearly lost.
- **Fabrication:** a thin session got a drop padded with margins, comparables, and next-step plans
  that were never discussed. The permanent record briefly contained things that never happened.

## Your mandate — you decide

You have the full session transcript in your context window. Use all of it. Then make four
editorial calls yourself:

1. **Whether anything is worth saving.** The invocation is a request to *curate*, not an order to
   write a file. The brain stores knowledge: decisions, durable facts, conclusions, plans,
   relationships, preferences. It does not store execution work — code written, bugs fixed,
   refactors, builds run, drafts produced — the repo, git history, or artifact itself is the record
   for those. A session that was *pure execution* (however long and however successful) has nothing
   to save: say exactly that, write no file, and let the user override you if they disagree.
   "Nothing here is worth saving — the fix lives in the repo" is a correct, professional outcome.
2. **Which parts of the session to save.** Be ruthlessly selective. A 2-hour session where only the
   last three turns produced durable output gets a capture of those three turns; note that the rest
   was dead ends in one line if it helps a future agent avoid re-walking them, otherwise drop it.
3. **The structure.** There is no mandatory body template. Choose sections that fit *this*
   session's content: a one-fact drop can be three lines; a strategy session may need decision
   records, options-killed-with-reasons, open questions, and next actions. Write for machine
   consumption by the next agent — terse, structured, zero human-facing niceties.
4. **The depth.** Proportional to what actually happened. Rich session → rich, curated record
   (hundreds of lines is fine and may be required). Thin session → thin drop. The two must not
   look alike.

A good test: a brand-new agent reading only your file should know (a) what the user actually said
that matters, (b) what the session concluded and *why*, (c) what was considered and rejected,
(d) what is still open, and (e) where related artifacts/pages live — without ever seeing the
transcript you saw.

## Hard rules — the freedom ends here

1. **Nothing that didn't happen.** Every claim in the file must trace to this session's transcript
   (or to content the user supplied). Sharpening a vague statement into a precise one ("maybe
   60-70%, haven't done the math" → "65% margin") is fabrication. Inventing precision the
   transcript doesn't contain — dates, plan names, tiers, figures — is fabrication. A
   "next actions" section may contain only actions explicitly agreed in the session; if none were
   agreed, there is no such section. Record an action as *done* only if the transcript shows it
   done; an assistant offer the user deferred is recorded as "offered, deferred" — never as done.
   Do not assert world-states the transcript didn't verify ("X is live", "Y is working in
   production") — record exactly what was verified and nothing more.
   When the session was vague, the record stays vague — mark open things as open.
   **The drop records this session only.** Existing brain pages may be cited by path, but never
   restate their content as session output and never merge vault knowledge into the session's
   conclusions — connecting this session to prior brain content is brainwork's job, not yours.
2. **Provenance stays legible.** A reader must always be able to tell the user's own words from
   the session's agent-authored conclusions from external content. Quote load-bearing user
   statements exactly (decisions, constraints, corrections, facts) — and never present an
   assistant line as the user's words. If the file contains *any* agent-authored sentence
   (framing, context, synthesis), add `synthesis_by: "<model/harness>"` to the frontmatter. How
   you arrange the body (sections, inline quoting, labels) is your call — that provenance stays
   unmistakable is not.
3. **Frontmatter minimum — these exact keys:** `title`, `source: conversation` (or the external
   origin), `collected: YYYY-MM-DD`, `tags`. Do not substitute your own schema (`date`, `slug`,
   `type` instead of `title`/`collected` breaks downstream tooling). If the user said this
   *replaces* an earlier decision/plan/fact ("we pivoted", "scrap X, now Y"), add
   `supersedes_hint: ["..."]` quoting the user's own description of what is replaced ("the per-post
   pricing idea from last week"), or a wiki/raw path you verified exists on disk — never an
   invented or guessed date. Brainwork resolves the hint and applies the supersession protocol.
4. **Destinations are fixed.** Conversation-derived material → `raw/drops/YYYY-MM-DD-<slug>.md`.
   External sources the user shared (article, paste, transcript) → `raw/clips/<slug>.md`, content
   preserved verbatim — never editorialize external content. Topic goes in `tags`, not folders.
5. **Reuse, don't duplicate.** Check `raw/.ingest-cache.json` and the target directory first. If an
   artifact for this content already exists, reuse or extend the record via a new dated drop —
   `raw/` is immutable, never edit an existing raw file.
6. **Raw only.** No `wiki/` writes, no `tools/sb.py` write subcommands, no ingest. The single
   allowed call is read-only `python3 tools/sb.py pending` for the final report. Brainwork is a
   separate, later invocation.
7. **Confirmation gate** (`AGENTS.md` §2): an explicit "save this" / "/jstack-savetobrain" /
   "capture" counts as the yes. Otherwise offer first; writing needs a yes.

## Downstream contract — who reads your file

- **`/jstack-brainwork`** (fresh agent, no session memory) compiles wiki pages from it. Make its
  job mechanical: decisions findable, current-vs-killed unmistakable, reasoning attributed to the
  session date.
- **Future working agents** may read the raw directly for drafting/deciding/building. Save enough
  that they don't need the transcript.
- You may annotate: mark a block `<!-- background only — do not compile -->` or flag low-confidence
  items. Brainwork honors annotations.

## Final report

Run `python3 tools/sb.py pending` (read-only), then report in two lines:

```
Saved raw source: raw/drops/<file>.md — <one-line description of what you curated>. Brainwork deferred.
Pending ingest backlog: <N> source(s). Run /jstack-brainwork to process.
```

If you saved nothing: `Nothing worth saving from this session: <reason>. No file written.`
If several sources are pending, recommend `/jstack-brainwork all pending`.

## Next skills

| Next | When |
|------|------|
| `/jstack-brainwork` | After saving — process/ingest the new raw drop into the wiki (default next hop; bare `/jstack-brainwork` drains all pending). |
