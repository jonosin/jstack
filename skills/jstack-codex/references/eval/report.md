# jstack-challenge — skilltune report (2026-06-21)

**Target:** invocation reliability + efficiency of the `probe → run → fallback → surface`
protocol — NOT critique prose. Ruler scores a behavior trace, not literary quality.

**Composite:** `0.70 · assertion_pass_rate + 0.30 · efficiency_score`. Graded by a deterministic
Python script against a ground-truth action log (no LLM judge) → maker ≠ checker for free.

## Result

| | train | held-out |
|---|---|---|
| v0 baseline | 0.9564 | 1.0 |
| v1 promoted | **0.9843** | 1.0 |
| Δ | **+0.0279** (KEEP) | 0 (already at ceiling) |

Canonical re-verify after promotion: `happy-codex-ok` 9/9 = 1.0, `efficiency-clean-path` 5/5 —
backgrounding green on both.

## The one change (v1)

Baseline already followed the protocol near-perfectly (6/9 cases flawless). The lone defect:
**`run_in_background: true` was followed only 1/3 of the time on the codex-success happy path** —
agents ran the fast-returning advisor synchronously. It was buried as a per-engine checklist
sub-step.

**Mutation:** hoisted it into a prominent **hard-rule** at the top of "How to spawn," covering
*both* engines, with the latency reason (advisor takes 30–600s; never block the user) and an
explicit "the only synchronous step is `probe`." One focused change.

**Effect:** backgrounding compliance **1/3 → 3/3** across the codex-success cases, zero regressions.

## Eval set (9 cases, 5 train / 4 held-out)

workflow (happy + held-out twin), edge_cases (unavailable / timeout / empty / auth-error fallbacks),
efficiency (clean-path), content_quality (six-section prompt), structure (negative: decline on a
routine question). Held-out covers all fallback failure modes + the negative guard + a backgrounding
twin, so a backgrounding fix is verifiable as generalizing.

### Notes / caveats (honest)
- **Ruler strengthened mid-run:** added held-out case `happy-codex-ok-ho` because backgrounding was
  asserted only in train at first — without a held-out backgrounding signal the S3 KEEP rule would
  auto-revert any legitimate backgrounding fix. Strengthening coverage, not weakening (allowed).
- **Held-out ceiling effect:** the held-out backgrounding case happened to pass at baseline, so
  held-out gives a no-regression guarantee but couldn't show a positive delta for backgrounding.
  Positive evidence comes from train (2 cases fixed) + the universal mechanism.
- **Single-run noise:** one v1 run of `happy-codex-ok` flaked on `took_position` (surfaced verdict
  but dropped the main-agent stance). Majority-vote over 3 runs (took_position 2/3, background 3/3)
  confirmed it as noise. The surfacing-position step is intermittently dropped — a candidate for a
  future tune (left unmade to avoid SKILL.md bloat on an already at-target skill).
- **Harness limitation:** the stub returns instantly, which removes some natural backgrounding
  pressure; the fix was validated on declared intent + the action log, not wall-clock blocking.

## Re-run the regression fixture

```
# from a sandbox where a runner has produced runs/<id>/{actions.log,result.json}:
python3 references/eval/harness/grade.py references/eval/evals.json <eval_id> <rundir>
```
Stub: `references/eval/harness/codex-advisor-stub.sh` (env `STUB_MODE`, `ACTIONS_LOG`).
