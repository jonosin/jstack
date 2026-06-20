# jstack-skilltune — the tune loop (S0–S6)

The mechanics of `jstack-skilltune`: tune an existing skill for accuracy or efficiency. Adapted faithfully
from **`GodModeAI2025/skill-forge`** Skill Mode — the cleanest "Karpathy autoresearch applied to a
SKILL.md" — with the held-out split from `stancsz/skills-flow` / `FishSerrie/skill-evolver`. The
generalized loop engine is **`/jstack-autoresearch`**; this skill is its skill-specific lens. To
*restructure* a skill or push fuzzy steps into deterministic code, that is **`/jstack-skillify`** (harden),
not tuning — tuning never redesigns.

You have a skill that works but whose output is **inconsistent, inaccurate, or wasteful**. Tune it: mutate
the SKILL.md / scripts ONE change at a time, score each change against a fixed eval, keep improvements,
revert regressions, until the score plateaus. Two things you can optimize — the composite score covers both:

- **Accuracy** — assertion pass-rate + LLM-judge quality.
- **Efficiency** — tokens / time / tool-calls (or a generic shell metric like bundle size, lint count).

Contents: Execution modes · Principles · S0 sandbox · S1 setup · S2 score · S3 loop · S4 coverage ·
S5 stop · S6 promote+cleanup · Overfitting protection.

## Execution modes — two only

Both modes run the S3 loop under the **`/goal` engine** (turn-looping, an independent judge each turn,
maker ≠ checker). They differ only in whether Jono gates the eval set first.

- **Auto** — fully autonomous; decides and runs end-to-end until an S5 stop. Triggered when invoked under
  `/goal` (`/goal /jstack-skilltune <name>`, or `/loop 30m /goal /jstack-skilltune <name>` for runs past
  ~20 turns) **or** with an explicit `auto` arg (`/jstack-skilltune <name> auto`). It generates the evals
  (S1) and **surfaces them + the reasoning in its thinking/output** so Jono can watch and abort if they look
  wrong — but it does **NOT** wait for confirmation; it continues automatically.
- **Show-eval** (default — a bare `/jstack-skilltune <name>` with no `/goal`/`auto`) — the ONE attended gate.
  Infer the optimization target from the skill, generate the 6–12 evals + record the baseline (S1 incl. the
  dry-run gate), then **show them with the "why"**: each eval + the §S4 category it targets + why it is the
  right ruler, plus the inferred target (Jono can correct it — e.g. "optimize for efficiency instead"). Wait
  for Jono to approve/edit. **On approval, do NOT run the loop inline, and do NOT re-invoke this skill** —
  it is already in context; re-invoking just duplicates `SKILL.md` + this file. Instead **emit a ready-to-
  paste `/goal` objective** that points the already-loaded loop at the approved sandbox:

  ```
  /goal Continue the skilltune for `<name>` from the approved sandbox /tmp/skilltune-<name>-<ts>/
  (evals.json approved, baseline recorded). Run the tune-mode S3 loop already in context: the Opus
  orchestrator forms each hypothesis + mutation and makes keep/revert decisions; delegate running the
  eval cases + machine assertions to Sonnet 4.6 subagents and soft-quality grading to an Opus 4.8
  cold-judge subagent (maker != checker); keep/revert by the S2/S3 thresholds. Stop at S5; promote the
  winner to canonical on green held-out; then delete the sandbox.
  ```

  Jono pastes it in the same session; the `/goal` engine runs the loop using the rules + approved evals
  already in context (the sandbox path keeps it robust to compaction). No skill reload.

  **Same-session only.** There is no fresh-session resume inside this skill. If Jono wants a *fresh*
  session to run the loop, he invokes **`/jstack-handoff goal`** to hand off running `/jstack-skilltune` on
  the skill with the approved evals — that machinery owns the cross-session bridge, not this skill.

## Principles (do not violate — they are the whole point)

- **The eval is the ruler.** Freeze the probes + rubric BEFORE editing; never weaken/delete one to pass.
- **One change per iteration.** Mutate → verify → keep/revert; a win must be attributable to one change.
- **Maker ≠ checker.** A COLD judge subagent grades outputs; never the agent that mutated the skill.
- **Opus drives, Sonnet does grunt work.** The orchestrator (Opus 4.8) does the important, non-repetitive
  work itself — hypothesis, mutation, and every keep/revert · stop/promote decision. Delegate only
  grunt / repetitive / token-heavy work — running eval cases, machine assertion checks, the report,
  bookkeeping — to **Sonnet 4.6 subagents** (`claude-sonnet-4-6`), spawned aggressively, so their bulky
  output stays out of the main context. An important task that must be a *separate* agent (the cold
  quality-judge, for maker ≠ checker) runs on an **Opus 4.8 subagent** (`claude-opus-4-8`). Smart → Opus;
  mechanical / verbose → Sonnet.
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
├── history.json          # structured per-experiment record AND the dashboard's data source
├── experiment-log.tsv    # one line per experiment, for quick monitoring
├── coverage-matrix.json  # which categories tried / kept / saturated
├── dashboard.html        # live dashboard shell — generated once (scripts/dashboard.py)
├── data.js               # dashboard data (window.DATA) — refreshed every experiment
└── report.md             # final summary
```

The **live dashboard** is `scripts/dashboard.py <sandbox>` (committed, deterministic, dependency-free,
`file://`-safe). It reads `history.json` → writes `data.js` (every call) + `dashboard.html` (once). Keep
`history.json` in the schema it expects — `{skill, status: running|stopped|done, baseline_composite,
target, best:{version,composite}, experiments:[{exp,version,category,hypothesis,train,heldout,delta,
decision}], coverage:{<cat>:{experiments,kept,best_delta,saturated}}}`. The page auto-reloads every 5s,
auto-stops when `status != "running"`, and has a sticky **Stop/Resume** button.

This schema is **universal for [0,1]-composite tuning** (accuracy, accuracy+efficiency, assertion-only —
the common case) and the coverage keys are dynamic, so category sets vary freely with no schema change.
For a **pure non-normalized metric target** (bundle size, latency, tokens, lint count) add an optional
`metric:{name,unit,direction:"lower"|"higher",min,max}` — then `train`/`heldout`/`baseline`/`target` hold
raw metric values and the chart scales its y-axis to `[min,max]`, labels the unit, and shows the
better-direction. Absent ⇒ `[0,1]`, higher-better. That one optional field is the only per-scenario change.

**Lifecycle (this answers "does it clean up?"):** the workspace exists ONLY for this session.
- **Success** → promote the winning snapshot to canonical, copy `evals.json` into the skill's
  `references/eval/` as a permanent regression fixture, write `report.md`, **then `rm -rf` the workspace.**
- **Failure / abandon** → `rm -rf` the workspace entirely. No "almost shipped" state, no orphan temp dir.

## S1 — Setup (the wizard)

- **Goal:** accuracy, efficiency, or both — one line.
- **Target + scope:** the skill dir; scope = its `SKILL.md` + scripts. Copy it to `snapshots/v0/`.
- **Evals:** 6–12 realistic cases, each with **machine-checkable assertions** (+ a 1–2 line judge rubric
  for soft quality). Split **60% train / 40% held-out**; write `evals.json`. Auto-generate if none exist.
  **Show-eval:** present them with rationale — the one approval gate. **Auto:** generate and proceed.
- **Metric:** the composite score (S2) for accuracy; or, for a pure-efficiency/generic target, a shell
  command that prints one number (e.g. `… | tail -1`).
- **Dry-run gate (hard):** run ONE train eval on the baseline; confirm grading yields valid JSON with
  `passed`/`total` and a composite in [0,1]. Record the **baseline score**. The loop does not start until this passes.
- **Launch + open the dashboard (mandatory; the agent opens it ITSELF, never defers to a human):** write
  the initial `history.json` (`status: running`, baseline, target, empty `experiments`), run `python3
  scripts/dashboard.py <sandbox>`, **then immediately open it yourself the moment it is generated** — run
  `open <sandbox>/dashboard.html` (macOS) / `xdg-open <sandbox>/dashboard.html` (Linux) / `start
  <sandbox>\dashboard.html` (Windows). This open is **non-optional and identical in BOTH Auto and Show-eval
  modes** — do NOT merely "tell Jono to open it" and do NOT wait on any human; in Auto/`/goal`/cron there is
  no human to act, so the agent opening it itself is the only thing that makes the live tab appear. (In
  Show-eval you may also mention it to Jono, but you still open it yourself.) The opened tab auto-reloads
  every 5s; because S6 regenerates rather than discards the final state before the report is persisted, the
  already-open tab stays frozen on the final view and **survives teardown**. (Deterministic — no subagent.)

## S2 — Composite score

```
composite = 0.50 * assertion_pass_rate   # hard facts: do the assertions pass?
          + 0.30 * llm_judge_score        # soft quality: cold-judge rating [0,1]
          + 0.20 * efficiency_score       # tokens / time / tool-calls (less = higher)
# no comparator available → 0.80 * assertion_pass_rate + 0.20 * efficiency_score
# pure generic/efficiency target → use the shell metric directly, with a direction
```

## S3 — The experiment loop (per iteration)

1. **Hypothesis** (main orchestrator, Opus 4.8): read the last evals' raw traces (input → output →
   per-assertion pass/fail) + the coverage matrix + any near-misses; pick the weakest area or least-covered
   category; form ONE testable hypothesis AND state how it generalizes beyond the train cases.
2. **Mutate** (main orchestrator, Opus 4.8): copy the current best → `vN/`; apply ONE focused change —
   wording, an example, structure, a script, or a tightened/trimmed instruction (for efficiency). Log what + why.
3. **Run + grade:** for each TRAIN eval, spawn a **Sonnet 4.6 subagent** (`claude-sonnet-4-6`) to execute
   the mutated skill and run the machine assertions → outputs; then a SEPARATE **Opus 4.8 cold-judge
   subagent** (`claude-opus-4-8`) scores soft quality → `grading.json` (maker ≠ checker). Held-out runs too,
   but only to score — never shown to steps 1–2.
4. **Score:** composite on train and held-out.
5. **Decide** (both modes decide automatically here, by these thresholds):
   - **KEEP** if `composite > baseline + 0.02` AND the held-out moved with the train set.
   - **REVERT** if `composite < baseline − 0.05`, OR train improved but held-out did not (overfit).
   - **NEAR_MISS** if delta ∈ [−0.05, +0.02]: revert, but mark the hypothesis promising (retry a different
     way / combine; drop it after 2 near-misses in the same category).
   - **NEUTRAL** (tie): keep the simpler/cheaper version (efficiency tiebreak — rule 6).
6. **Log + refresh dashboard:** append the experiment to `history.json` (in the dashboard schema) +
   `experiment-log.tsv` (timestamp, hypothesis, before, after, delta, decision, category); update the
   coverage matrix and `best`; then run `python3 scripts/dashboard.py <sandbox>` to refresh `data.js` (the
   open dashboard picks it up on its next 5s tick). Deterministic — no subagent.

## S4 — Coverage matrix (steer exploration → exploitation)

Categories: `formatting · content_quality · examples · workflow · edge_cases · efficiency · scripts ·
structure`. Track per category: experiments, kept, best_delta, saturated. **Saturated** = ≥3 experiments,
none > +0.01. The hypothesis step prefers untouched categories early (explore), re-tries high-success
categories late (exploit), and avoids saturated ones.

## S5 — Stop criteria

composite ≥ target (e.g. 0.95) on the held-out set · `max_experiments` (default 10) · 3 consecutive
NEUTRAL/REVERT (plateau) · 3 consecutive crashes (infra problem).

## S6 — Promote + clean up

On green (held-out ≥ baseline, no regression): back up canonical, `rsync` the winning snapshot over the
canonical skill, re-run the eval against canonical to confirm identical-green (roll back the backup if
not). Copy `evals.json` → the skill's `references/eval/` (permanent regression fixture — the skill now
carries its own ruler). Have a **Sonnet 4.6 subagent** write `report.md` (start→end score, top 3 mutations,
dead ends, coverage, ASCII score chart). Set `history.json` `status: "done"` (or `"stopped"` if aborted)
and run `scripts/dashboard.py <sandbox>` once more so an open dashboard freezes on the final state and stops
auto-refreshing. **Then delete the sandbox workspace** (the ephemeral dashboard goes with it). The
orchestrator reports baseline vs final score per held-out probe. The dashboard tab the agent opened at S1
stays open in the browser, now **frozen on the final state** (status `done`/`stopped` stops the
auto-refresh) — it **survives this teardown** because it was opened live at S1. **Persist `report.md`
BEFORE deleting the sandbox** so the run's results outlive the ephemeral dashboard file.

## Overfitting protection (carried from skill-forge)

Held-out probes never feed hypothesis/mutation (only scoring); every hypothesis must justify how it
generalizes; coverage-matrix diversity + saturation prevents tunnel-vision; refresh/rotate the eval split
every 5 experiments; a 3-consecutive-crash circuit breaker stops an infra loop instead of spinning.

> Provenance: Karpathy `autoresearch` (one metric · constrained scope · fast verify · auto-rollback · git
> memory) → `skill-forge` Skill Mode (composite score on a SKILL.md) → this. Generic loop mechanics live in
> `/jstack-autoresearch`. More prior art: `justinwetch/Skill-RSI` + `SkillEval`, `stancsz/skills-flow`.
