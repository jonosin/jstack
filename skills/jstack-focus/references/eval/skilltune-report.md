# jstack-skilltune report — jstack-focus

**Target:** accuracy + efficiency (compress ~40%, preserve decision-critical facts, honor auto-clarity
exceptions, emit `[shortened]` only when rewriting a prior message).
**Composite:** 0.50·assertion + 0.30·cold-judge + 0.20·efficiency. Target 0.95 (held-out). Split 60/40.

## Result
| | Baseline (v0) | Final (v1) |
|---|---|---|
| Machine assertions (train) | 4/5 probes full (probe1 fails) | 5/5 full |
| Machine assertions (held-out) | 2/3 probes full (probe8 fails) | 3/3 full |
| Cold-judge soft quality | ~0.95 | train 0.956 / held 0.957 |
| **Composite (held-out)** | **0.93** | **0.987** |

Stopped at S5: held-out 0.987 >= target 0.95. Converged in **1 experiment**.

## Score chart (held-out composite)
```
baseline v0  0.93  ##############################
target       0.95  ################################
final v1     0.99  #################################  KEEP
```

## Top mutation
1. **[formatting] Tighten the `[shortened]` trigger (KEEP, +0.057 held-out).** Baseline fired the
   `[shortened]` block on fresh answers and status updates (probes 1, 8 failed `not_starts_with_marker`).
   Rewrote the section to state the marker is for ONE case only (rewriting a prior long message) and added
   an explicit "every other focus response is compressed inline with NO marker" guard. Fixed both probes;
   soft quality held at ~0.96.

## Dead ends
None. The eval isolated a single dominant defect; the first mutation cleared target, so no further
hypotheses were needed (additional mutations would chase diminishing soft-quality returns already at 0.96
and risk regression).

## Coverage
formatting 1/1 kept. efficiency / content_quality / edge_cases / workflow untouched — all already green at
baseline (the hard-fact assertions passed; the only headroom was the marker-trigger ambiguity).

## Regression fixture
`references/eval/evals.json` (8 probes, train 1,2,4,5,7 / held-out 3,6,8) now ships with the skill.

## Note on the conservative baseline
Baseline composite was anchored at 0.93 using a conservative flat judge during S1. Soft quality of the
baseline outputs was in fact ~0.95 (the only real defect was the machine-checkable false marker), so the
true accuracy gain is concentrated in the assertion dimension; the judge dimension was already strong.
