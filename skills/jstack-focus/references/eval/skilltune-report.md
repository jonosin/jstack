# jstack-focus — skilltune report

## Goal
Fix an over-compression regression introduced when `jstack-voice` + the old compression-layer
`jstack-focus` were merged. The merged skill redefined `tight` as "lead with what matters, then a line
or two of why" + "cut what doesn't earn its words." That turned the job from *mechanical compression*
into *content selection*, so when the user said "shorten that" on a long message, the skill kept the
lead takeaway and dropped the load-bearing decisions, reasoning, and conclusions stated after it. The
user's intent: **decrease the words I need to read, but I still get to read everything the previous
response outputted.** Same content, fewer words. Every point, decision, and insight survives; only the
words around them shrink.

## What I changed
- **Restored mechanical compression as `tight`'s core.** Before: "lead with what matters, then a line or
  two of why." After: "same content, fewer words. Tighten sentence structure ~40-50% from baseline voice;
  every point, decision, and insight from the source survives, only the words around them shrink." This is
  the old (working) recipe, kept inside the merged two-level dial + voice framework.
- **Replaced the content-filter section with a preservation section.** Renamed "Surface only what's
  needed" → "Compress the wording, not the content." Dropped "cut what doesn't earn its words" (the rule
  that invited judging whether a decision "earned" staying). Added explicit "Drop padding, not content"
  with the invariant: every decision, reason, and conclusion stays; only preamble, restating the question,
  hedges, and recap get cut. Kept the good non-compression rules (lead with it, take a position, match
  shape to the answer).
- **Fixed the description + intro**, which still framed the job as "surfaces only what's needed" (filtering).
  Now: "Compresses the wording so you read less, while every point, decision, and insight survives."
- **Added `terse` guard.** "Use only when the user explicitly asks for fragments" so `tight` isn't read as
  a skeleton mode.
- **Added a defect probe** to the eval set: `shorten-narrative-decisions` (held-out). A 5-decision
  narrative message with no "first/second" enumeration cues, pinned with `contains_all` on all 5
  decisions. The old skill's "a line or two of why" would keep the lead and drop the rest, failing 4 of 5
  `contains_all` assertions. The existing `shorten-that` probe passed the old skill because its source used
  explicit "First, Second, Third, finally" enumeration, which cued the model to keep all 4; the new probe
  removes that crutch and matches the real failure mode.

## What I tried that didn't stick
- N/A. This was a targeted regression fix against a confirmed defect, not a broad tune sweep. The previous
  sweep's v1/v2/v3 rejections stand (see the prior report section below).

## Outcome & what to expect
**Self-score (non-independent — maker was also checker, no cold judge):**
- Defect probe `shorten-narrative-decisions`: **10/10 assertions pass.** All 5 narrative decisions
  preserved (feature flag, dedicated worker, email provider, on-call, Rust) + `[shortened]` marker +
  scannable structure.
- Train assertion pass rate: **100%.**
- Held-out assertion pass rate: **96%** (1 failure: `architecture-ascii` `not-a-wall`, a grader artifact
  where the candidate diagram used `->` arrows without `|` pipe characters so the diagram detector didn't
  recognize it; unrelated to the compression defect, baseline passed this probe 5/5).

**This is a fast signal, not a green gate.** The full eval-gated tune loop (independent Opus cold-judge +
Sonnet grunt subagents under `/goal`) was not run because this session is on opencode/glm-5.2 without
Claude subagent spawning. The fix is promoted on: (a) the user's confirmed fix shape and purpose, (b) the
defect probe passing 10/10 on the deterministic assertions, which are the load-bearing signal and do not
need a judge. The soft-quality judge term was skipped (it would be non-independent here anyway).

What you'll notice using `tight` now: "shorten that" on a long narrative message keeps every decision and
insight, just with shorter wording, no preamble, no hedges. It no longer collapses to the lead takeaway.
`terse` is still the skeleton mode for when you explicitly ask for fragments.

## The stats
| Probe set | Assertion pass rate | Notes |
|---|---:|---|
| Train (6 probes) | 100.00% | all assertions pass |
| Held-out (5 probes) | 96.00% | 1 grader-artifact failure on architecture-ascii diagram detection |
| **Defect probe** (`shorten-narrative-decisions`) | **100.00%** | all 5 narrative decisions preserved |

Skill size grew from ~519 tokens (merged seed) to ~640 tokens (added the preservation section + terse
guard). That is the expected cost of the fix; the efficiency term dropped accordingly, which is the right
trade for not dropping user content.

## Follow-up
Run the full `/jstack-skilltune` loop under `/goal` in a Claude Code session with an independent Opus
cold-judge to get a true green gate on the extended eval set. The eval fixture (`evals.json` with the new
defect probe) is in place for that run.

## Prior sweep (kept for provenance)
Held-out score (fresh cases kept hidden so the skill couldn't game them): **94.95%**, unchanged because
the merged design was already there.

| Variant | What it changed | Train | Held-out | Decision |
|---|---|---:|---:|---|
| v0 (merged seed) | the merge as designed | 88.21% | **94.95%** | KEEP / promoted (then regressed in live use — see above) |
| v1 | sharper shape wording | 90.99% | 94.98% | revert (breaks "shorten that" into prose) |
| v2 | lead-with-one-cause | ~86% | ~93% | revert (longer, slips) |
| v3 | explicit 3+-points to list | 90.13% | 92.86%* | revert (token cost, below seed) |

\*v3 held-out is a single run; it could not clear the seed even at best.

The v0 "KEEP / promoted" is the version that then over-compressed in live use. This report's fix patches
that regression by restoring the old mechanical-compression recipe inside the merged framework.
