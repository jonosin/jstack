# Strategy grilling

Use this branch for product, business, marketing, GTM, offer, positioning, or strategic decisions.

## Canonical artifact and ownership

The relevant venture or build repository owns the full strategic artifact. Create it at
`docs/strategy/YYYY-MM-DD-<self-explanatory-outcome>.md`; it is the sole detailed record. The
second brain does not restate its decisions, create a source card for it, or receive a raw capture
of the session.

Before writing, identify the relevant workspace. Read its `BRAIN.md`, `AGENTS.md`, `docs/index.md`,
and any directly related artifact. If no workspace is in scope, ask the user which one owns the
decision; do not create a strategy artifact in the second brain.

The second brain is an available evidence layer for better strategic judgment. When it could change
the answer, read `~/second-brain/wiki/hot.md`, then `wiki/index.md`, then only the relevant detail
pages. For work-grade claims, follow a source card's raw pointer and inspect the relevant source
section—especially saved X articles, transcripts, and research clips under `raw/`. Do not browse the
whole vault or treat it as a required preflight; use progressive disclosure and bring back only
evidence that materially improves the current decision.

Create the document lazily after the outcome and scope are clear enough to name. Use this shape:

```markdown
---
title: "<clear, outcome-led title>"
summary: "<one-line current verdict or decision state>"
status: draft
type: strategy-grill
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# <clear, outcome-led title>

## Outcome

## Current position

## Decisions

## Evidence and assumptions

## Risks and tensions

## Open decisions

## Deferred / out of scope

## Validation or next boundary
```

After each user contribution that materially changes the work, update the artifact. Record the
current position, decision, reason, and assumptions that could reverse it. Do not transcribe the
conversation or preserve discarded questioning.

## Conversation posture

Start by reading the workspace and offering a concise assessment: what appears true, what matters
most, and the direction you currently recommend. Be a strategic partner, not a questionnaire.

Explore connected considerations in natural prose. Surface non-obvious implications, tensions,
alternatives, and the strongest next decision as they become relevant. Investigate anything the
workspace, brain, or allowed research can answer before involving the user.

Act as an elite thinking partner, not merely a facilitator. Offer independent feedback and a
point of view. Notice the unknown unknowns that could invalidate the frame, the known unknowns that
need an explicit assumption or test, and the unknown knowns—relevant evidence, constraints, prior
decisions, or capabilities already available but easy to overlook. Introduce these when they change
the quality of the decision, not as a mandatory checklist.

Ask only questions that require the user's judgment, using the host's structured user-input tool
rather than inline chat prose. Make each question specific, decision-ready, and paired with your
current recommendation when useful. Do not title exchanges “Frontier Rounds,” dump a long numbered
questionnaire, or fill the conversation with vague prompts such as “what are your thoughts?”

Keep momentum: combine related observations into a coherent reply, then pause for the smallest set
of decisions needed to move forward. Stop when the strategic direction is explicit enough to act on
or the user deliberately defers the remaining decision.

## Closeout and brain connection

Set the final status (`accepted`, `proposed`, or `draft`) and regenerate the workspace registry:

```bash
python3 ~/jstack/skills/jstack-init/scripts/docs_index.py index --write --repo <workspace>
python3 ~/jstack/skills/jstack-init/scripts/docs_index.py lint --repo <workspace>
```

The brain connection is the registered satellite's existing `docs/index.md` symlink. Verify it with:

```bash
python3 ~/jstack/skills/jstack-init/scripts/docs_index.py brain-link-lint --venture <slug>
```

Do not run `/jstack-savetobrain` merely because this artifact exists. It would duplicate the canonical
record. For a session started in this repository, keep the complete strategic record in `docs/`; the
`docs/index.md` symlink is the only second-brain connection.
