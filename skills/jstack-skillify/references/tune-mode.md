# Mode B — tune an existing skill (accuracy or efficiency)

Adapted faithfully from **`GodModeAI2025/skill-forge`** Skill Mode — the cleanest "Karpathy autoresearch
applied to a SKILL.md" — with the held-out split from `stancsz/skills-flow` / `FishSerrie/skill-evolver`.
The generalized loop engine is **`/jstack-autoresearch`**; this is its skill-specific lens.

You have a skill that works but whose output is **inconsistent, inaccurate, or wasteful**. Tune it: mutate
the SKILL.md / scripts ONE change at a time, score each change against a fixed eval, keep improvements,
revert regressions, until the score plateaus. Two things you can optimize — the composite score covers both:

- **Accuracy** — assertion pass-rate + LLM-judge quality.
- **Efficiency** — tokens / time / tool-calls (or a generic shell metric like bundle size, lint count).

Contents: Execution modes · Principles · S0 sandbox · S1 setup · S2 score · S3 loop · S4 coverage ·
S5 stop · S6 promote+cleanup · Overfitting protection.

## Execution modes

- **Auto** — fully autonomous loop, ideal overnight (hand to `/jstack-handoff goal` to run unattended).
- **Guided** — 5 checkpoints (evals, hypothesis, mutation, keep/revert, continue) where Jono decides.
  Default for a new skill or uncertain evals. Auto skips all five and decides by the thresholds in S3.

## Principles (do not violate — they are the whole point)

- **The eval is the ruler.** Freeze the probes + rubric BEFORE editing; never weaken/delete one to pass.
- **One change per iteration.** Mutate → verify → keep/revert; a win must be attributable to one change.
- **Maker ≠ checker.** A COLD judge subagent grades outputs; never the agent that mutated the skill.
- **Held-out split.** 60% train / 40% held-out. The held-out probes are NEVER shown to the hypothesis or
  mutator step — they only score a candidate. Train-only gains = overfit → revert. Held-out is the verdict.
- **Diagnose from traces; generalize, don't memorize.** Tune the pattern, not the individual test case.
- **Memory is on disk.** snapshots + history + git = the loop's memory; never re-test a logged dead end.
- **Sandbox everything; promote only on green; delete the sandbox at session end** (skillify Iron contract).

## S0 — Sandbox workspace (create now, delete at end of session)

NEVER edit the canonical skill during the loop. Create a temp workspace and work entirely inside it:

```
/tmp/skilltune-<name>-<ts>/
├── snapshots/v0/         # exact copy of the target skill = baseline; vN/ = each kept version
├── evals.json            # probes + assertions + train/held-out split
├── history.json          # structured per-experiment record
├── experiment-log.tsv    # one line per experiment, for quick monitoring
├── coverage-matrix.json  # which categories tried / kept / saturated
└── report.md             # final summary
```

**Lifecycle (this answers "does it clean up?"):** the workspace exists ONLY for this session.
- **Success** → promote the winning snapshot to canonical, copy `evals.json` into the skill's
  `references/eval/` as a permanent regression fixture, write `report.md`, **then `rm -rf` the workspace.**
- **Failure / abandon** → `rm -rf` the workspace entirely. No "almost shipped" state, no orphan temp dir.

## S1 — Setup (the wizard)

- **Goal:** accuracy, efficiency, or both — one line.
- **Target + scope:** the skill dir; scope = its `SKILL.md` + scripts. Copy it to `snapshots/v0/`.
- **Evals:** 6–12 realistic cases, each with **machine-checkable assertions** (+ a 1–2 line judge rubric
  for soft quality). Split **60% train / 40% held-out**; write `evals.json`. (Auto-generate if none exist;
  in Guided, Jono reviews them — checkpoint 1.)
- **Metric:** the composite score (S2) for accuracy; or, for a pure-efficiency/generic target, a shell
  command that prints one number (e.g. `… | tail -1`).
- **Dry-run gate (hard):** run ONE train eval on the baseline; confirm grading yields valid JSON with
  `passed`/`total` and a composite in [0,1]. Record the **baseline score**. The loop does not start until this passes.

## S2 — Composite score

```
composite = 0.50 * assertion_pass_rate   # hard facts: do the assertions pass?
          + 0.30 * llm_judge_score        # soft quality: cold-judge rating [0,1]
          + 0.20 * efficiency_score       # tokens / time / tool-calls (less = higher)
# no comparator available → 0.80 * assertion_pass_rate + 0.20 * efficiency_score
# pure generic/efficiency target → use the shell metric directly, with a direction
```

## S3 — The experiment loop (per iteration)

1. **Hypothesis** (cold "scientist"): read the last evals' raw traces (input → output → per-assertion
   pass/fail) + the coverage matrix + any near-misses; pick the weakest area or least-covered category;
   form ONE testable hypothesis AND state how it generalizes beyond the train cases. *(Guided checkpoint 2.)*
2. **Mutate** (the "surgeon"): copy the current best → `vN/`; apply ONE focused change — wording, an
   example, structure, a script, or a tightened/trimmed instruction (for efficiency). Log what + why. *(Guided checkpoint 3.)*
3. **Run:** for each TRAIN eval, spawn a subagent with the mutated skill; grade with the cold judge →
   `grading.json`. Held-out runs too, but only to score — never shown to steps 1–2.
4. **Score:** composite on train and held-out.
5. **Decide** *(Guided checkpoint 4 — Jono may override)*:
   - **KEEP** if `composite > baseline + 0.02` AND the held-out moved with the train set.
   - **REVERT** if `composite < baseline − 0.05`, OR train improved but held-out did not (overfit).
   - **NEAR_MISS** if delta ∈ [−0.05, +0.02]: revert, but mark the hypothesis promising (retry a different
     way / combine; drop it after 2 near-misses in the same category).
   - **NEUTRAL** (tie): keep the simpler/cheaper version (efficiency tiebreak — rule 6).
6. **Log:** append to `history.json` + `experiment-log.tsv` (timestamp, hypothesis, before, after, delta,
   decision, category); update the coverage matrix.

## S4 — Coverage matrix (steer exploration → exploitation)

Categories: `formatting · content_quality · examples · workflow · edge_cases · efficiency · scripts ·
structure`. Track per category: experiments, kept, best_delta, saturated. **Saturated** = ≥3 experiments,
none > +0.01. The hypothesis step prefers untouched categories early (explore), re-tries high-success
categories late (exploit), and avoids saturated ones.

## S5 — Stop criteria *(Guided checkpoint 5 to continue)*

composite ≥ target (e.g. 0.95) on the held-out set · `max_experiments` (default 10) · 3 consecutive
NEUTRAL/REVERT (plateau) · 3 consecutive crashes (infra problem) · Guided: Jono says stop.

## S6 — Promote + clean up

On green (held-out ≥ baseline, no regression): back up canonical, `rsync` the winning snapshot over the
canonical skill, re-run the eval against canonical to confirm identical-green (roll back the backup if
not). Copy `evals.json` → the skill's `references/eval/` (permanent regression fixture — the skill now
carries its own ruler). Write `report.md` (start→end score, top 3 mutations, dead ends, coverage, ASCII
score chart). **Then delete the sandbox workspace.** Report baseline vs final score per held-out probe.

## Overfitting protection (carried from skill-forge)

Held-out probes never feed hypothesis/mutation (only scoring); every hypothesis must justify how it
generalizes; coverage-matrix diversity + saturation prevents tunnel-vision; refresh/rotate the eval split
every 5 experiments; a 3-consecutive-crash circuit breaker stops an infra loop instead of spinning.

> Provenance: Karpathy `autoresearch` (one metric · constrained scope · fast verify · auto-rollback · git
> memory) → `skill-forge` Skill Mode (composite score on a SKILL.md) → this. Generic loop mechanics live in
> `/jstack-autoresearch`. More prior art: `justinwetch/Skill-RSI` + `SkillEval`, `stancsz/skills-flow`.
