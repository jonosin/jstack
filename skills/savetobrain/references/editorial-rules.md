---
name: savetobrain-editorial-rules
description: Shared curation rules for savetobrain route files. Do not invoke directly.
disable-model-invocation: true
---

# Editorial rules — shared curation contract

Loaded by `raw-drops-route.md` and `venture-route.md`. Contains the curation
mandate and the universal hard rules (fabrication, provenance, frontmatter,
structure). Destination-specific rules live in the route file, not here.

## Your mandate — you decide

You have the full session transcript in your context window. Use all of it. Then
make four editorial calls yourself:

1. **Whether anything is worth saving.** The invocation is a request to *curate*,
   not an order to write a file. Knowledge worth saving: decisions, durable facts,
   conclusions, plans, relationships, preferences. Not worth saving: code written,
   bugs fixed, refactors, builds run, drafts produced — the repo, git history, or
   artifact itself is the record for those. A session that was *pure execution* has
   nothing to save: say exactly that, write no file. "Nothing here is worth saving
   — the fix lives in the repo" is a correct, professional outcome.
2. **Which parts of the session to save.** Be ruthlessly selective. A 2-hour
   session where only the last three turns produced durable output gets a capture
   of those three turns; note that the rest was dead ends in one line if it helps a
   future agent avoid re-walking them, otherwise drop it.
3. **The structure.** There is no mandatory body template. Choose sections that fit
   *this* session's content: a one-fact drop can be three lines; a strategy session
   may need decision records, options-killed-with-reasons, open questions, and next
   actions. Write for machine consumption by the next agent — terse, structured,
   zero human-facing niceties.
4. **The depth.** Proportional to what actually happened. Rich session → rich,
   curated record (hundreds of lines is fine and may be required). Thin session →
   thin drop. The two must not look alike.

A good test: a brand-new agent reading only your file should know (a) what the user
actually said that matters, (b) what the session concluded and *why*, (c) what was
considered and rejected, (d) what is still open, and (e) where related
artifacts/pages live — without ever seeing the transcript you saw.

## Universal hard rules

1. **Nothing that didn't happen.** Every claim in the file must trace to this
   session's transcript (or to content the user supplied). Sharpening a vague
   statement into a precise one ("maybe 60-70%, haven't done the math" → "65%
   margin") is fabrication. Inventing precision the transcript doesn't contain —
   dates, plan names, tiers, figures — is fabrication. A "next actions" section may
   contain only actions explicitly agreed in the session; if none were agreed, there
   is no such section. Record an action as *done* only if the transcript shows it
   done; an assistant offer the user deferred is recorded as "offered, deferred" —
   never as done. Do not assert world-states the transcript didn't verify ("X is
   live", "Y is working in production") — record exactly what was verified and
   nothing more. When the session was vague, the record stays vague — mark open
   things as open. The drop records this session only. Existing brain or workspace
   pages may be cited by path, but never restate their content as session output and
   never merge vault knowledge into the session's conclusions.
2. **Provenance stays legible.** A reader must always be able to tell the user's own
   words from the session's agent-authored conclusions from external content. Quote
   load-bearing user statements exactly (decisions, constraints, corrections, facts)
   — and never present an assistant line as the user's words. If the file contains
   *any* agent-authored sentence (framing, context, synthesis), add
   `synthesis_by: "<model/harness>"` to the frontmatter. How you arrange the body
   (sections, inline quoting, labels) is your call — that provenance stays
   unmistakable is not.
3. **Frontmatter is mandatory.** Every saved file must carry frontmatter. The
   required keys depend on the destination — the route file specifies them. Never
   write a file that fails its route's frontmatter contract.
4. **Structure check before writing.** Confirm the file's frontmatter has every
   required key and that the body has at least one section a reader can act on —
   never write a file that fails this check.
