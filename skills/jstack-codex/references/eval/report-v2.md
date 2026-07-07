# jstack-challenge — skilltune v2 report (2026-06-21)

**Target:** make the surfacing **"take a position"** step (Surfacing-the-result step 3 — the main
agent states its own agree / partially-agree / disagree stance with a reason) as reliable as the
already-promoted backgrounding rule. Suspected defect: an intermittent 1/3 flake observed last
session where a run surfaced only the verdict and dropped the stance.

**Method:** single-change skilltune loop in a temp sandbox. Heavy work delegated to cold **Sonnet
4.6** runner subagents (one eval run each); grading by the deterministic `harness/grade.py` as a
**separate checker** (maker ≠ checker — a runner never grades its own run). `took_position` is noisy,
so every cell is aggregated over ≥3 cold runs. Two `took_position` cases exercised: `happy-codex-ok`
(train) and `happy-codex-ok-ho` (held-out); both also assert `backgrounded`.

## Result — the flake did not reproduce; baseline was already at ceiling

| metric | v0 baseline | v1 (mutated) |
|---|---|---|
| `took_position` pass | **12 / 12** (denoised; 6 per case) | **6 / 6** (3 per case) |
| `backgrounded` pass | **12 / 12** | **6 / 6** |

- **18 cold runs total** (12 v0 + 6 v1). **Every single run** took a position and ran the advisor in
  the background. Zero `took-position` failures, zero `backgrounded` failures across the whole set.
- Baseline `took_position` was measured at 6/6 on the first batch, then **denoised to 12/12** with a
  second batch to rule out a lucky sample. It is a hard ceiling — the hypothesized intermittent flake
  did **not** reproduce under the prescribed runner harness.

## The one change considered (v1) — NOT promoted

Mirrored the promoted backgrounding fix: hoisted the "state your own position" requirement into a
prominent **hard-rule callout** at the top of the `## Surfacing the result` section, beginning:

> **Hard rule — always state your own position (agree / partially agree / disagree) with a reason.**

…explaining WHY (the user invoked the skill *because* the main agent was too agreeable; a verdict
with no stance defeats the purpose) and marking step 3 non-skippable. One focused edit, +2 lines,
`scripts/` untouched, `diff -rq v0 v1` reported only `SKILL.md` differing.

## Decision

**Decision: REVERT+no-change**

Rationale (mechanical, per the M3 KEEP rule): KEEP requires `v1_took_position ≥ 5/6` **AND
`v1_took_position > v0_took_position`** AND no backgrounding regression. With v0 already saturated at
6/6 (12/12 denoised), `v1 > v0` is **unreachable** — v1 also landed at 6/6. The mutation therefore
produced **no attributable, measured improvement**. Promoting it would add SKILL.md text for zero
demonstrated benefit, violating the loop's core discipline ("a win must be attributable; never
promote on vibes"). An honest REVERT is the correct stop.

- Canonical `~/jstack/skills/jstack-challenge/SKILL.md` was **left untouched**.
- The promoted backgrounding gain is **preserved** (it was never modified or re-tuned; v0 and v1 both
  show `backgrounded` 12/12 and 6/6).
- The KEEP-only regression spot-checks (`codex-unavailable`, `codex-run-empty`,
  `negative-routine-question`) were **not run**: they gate promotion only, and since nothing is
  promoted, canonical is unchanged and a regression is impossible by construction.

## Caveats (honest)

- **`took_position` noise:** known to flake ~1/3 on a single run (last session). This run defeated
  that noise by aggregating 12 baseline + 6 candidate cold runs; the step passed every time.
- **Harness saturation may mask a real-world flake.** The prescribed cold-runner protocol asks the
  runner to follow the full Surfacing protocol and to self-report `took_position`, and the grader
  reads that self-report. Sonnet 4.6 runners surfaced a stance in 18/18 runs, so within this harness
  the step is not droppable. It is possible a *less-primed* harness (or a real multi-turn session
  where the model is mid-flow) would still occasionally drop the stance — but reproducing that would
  require changing the eval harness, which the loop forbids mid-tune (you must not weaken or reshape
  an eval to manufacture a result). If the flake resurfaces in real use, re-open with a harness that
  reproduces it *before* mutating.
- **Stub returns instantly**, removing natural backgrounding latency pressure; backgrounding is
  validated on declared intent + the action log, not wall-clock blocking (same limitation as v1).

## Reproduce

```
sb=<temp sandbox>            # snapshots/v0 = canonical, snapshots/v1 = + hard-rule
# cold runner (Sonnet 4.6) writes runs/<ver>/<id>/<r>/{actions.log,result.json,prompt.md}
python3 references/eval/harness/grade.py references/eval/evals.json <eval_id> <rundir>
# count took-position / backgrounded passes across r1..rN; majority/aggregate, never decide on 1 run
```
Stub: `references/eval/harness/codex-advisor-stub.sh` (env `STUB_MODE=ok`, `ACTIONS_LOG`).
