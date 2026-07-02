# Cold Judge contract

## Role
A fresh-context **Opus 4.8** subagent, **separate** from whoever mutated the skill and **separate**
from the runner (maker != checker). It scores only the **failure-mode PROSE QUALITY** of a run — not
structure, not HTML, not assertions.

## Inputs
- The scenario plan (the user's plan, who it affects, what success means).
- The run's `transcript.md` and `report.html`.

It must **NOT** see `grade.py`, the assertions, or the train/held-out split.

## Rubric (score in [0,1], one-decimal granularity is fine)
> Are the failure modes SPECIFIC to this exact plan, grounded in the given context, REAL threats
> (not generic inconveniences), and non-overlapping (each a distinct way to die)?
- **0** = generic / templated / overlapping / could-apply-to-any-plan.
- **0.5** = mixed.
- **1** = sharp, plan-specific, distinct, genuinely high-stakes.

When scoring, weigh all four:
1. **Specificity** — do the reasons name THIS plan's concrete particulars, not abstractions?
2. **Grounding** — are they anchored in the given context (the affected parties, the success bar)?
3. **Real threat vs inconvenience** — would each actually kill or seriously wound the plan?
4. **Non-overlap / coverage** — is each reason a distinct way to die, spanning the threat surface?

## Output
Write **ONLY** `<rundir>/judge.json`:
```json
{"judge_score": <float 0..1>}
```
No prose anywhere else.

## Negative / declined runs
The judge is **NOT invoked** for negative or declined runs — `grade.py` defaults the judge score to
**1.0** in those cases.
