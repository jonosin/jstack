# skilltune — the tune loop (S0–S6)

The mechanics of `skilltune`: tune an existing skill for accuracy or efficiency. Adapted faithfully
from **`GodModeAI2025/skill-forge`** Skill Mode — the cleanest "Karpathy autoresearch applied to a
SKILL.md" — with the held-out split from `stancsz/skills-flow` / `FishSerrie/skill-evolver`. The
generalized loop engine is **`/autoresearch`**; this skill is its skill-specific lens. To
*restructure* a skill or push fuzzy steps into deterministic code, that is **`/skillify`** (harden),
not tuning — tuning never redesigns.

You have a skill that works but whose output is **inconsistent, inaccurate, or wasteful**. Tune it: mutate
the SKILL.md / scripts ONE change at a time, score each change against a fixed eval, keep improvements,
revert regressions, until the score plateaus. Two things you can optimize — the composite score covers both:

- **Accuracy** — assertion pass-rate + LLM-judge quality.
- **Efficiency** — tokens / time / tool-calls (or a generic shell metric like bundle size, lint count).

Contents: Execution modes · Principles · S0 sandbox · Resuming an interrupted run · S1 setup · S2 score ·
S3 loop · S4 coverage · S5 stop · S6 promote+cleanup · Overfitting protection.

## Execution modes — two only

Both modes run the S3 loop under the **`/goal` engine** (turn-looping, an independent judge each turn,
maker ≠ checker). They differ only in whether Jono gates the eval set first.

- **Auto** — fully autonomous; decides and runs end-to-end until an S5 stop. Triggered when invoked under
  `/goal` (`/goal /skilltune <name>`, or `/loop 30m /goal /skilltune <name>` for runs past
  ~20 turns) **or** with an explicit `auto` arg (`/skilltune <name> auto`). It generates the evals
  (S1) and **surfaces them + the reasoning in its thinking/output** so Jono can watch and abort if they look
  wrong — but it does **NOT** wait for confirmation; it continues automatically.
- **Show-eval** (default — a bare `/skilltune <name>` with no `/goal`/`auto`) — the ONE attended gate.
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
  session to run the loop, he first creates an execution spec with **`/to-spec`**, then invokes
  **`/handoff goal`** to package the approved evals for the fresh task — that machinery owns the
  cross-session bridge, not this skill.

## Principles (do not violate — they are the whole point)

- **Show percentages — never decimals. Compute in [0,1] internally.** Scores live in [0,1] internally.
  Whenever you show a score, delta, target, or baseline to Jono — in chat, the dashboard, or `report.md`
  — multiply by 100 and write it as a percentage with 2 decimals (`0.834 → 83.40%`, delta `0.02 →
  +2.00%`). **NEVER write a raw decimal like `0.83` in any user-facing output — always `83.00%`.** The
  S2 weights and the S2/S3 decision thresholds stay decimal — they are internal math, not displayed scores.
  Raw-metric runs (KB / ms / tokens / lint) keep their real units, not %.
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
├── .git/                 # per-iteration commit history — see "Git-native sandbox" below
├── .gitignore             # excludes dashboard.html + data.js (derived, regenerated every call)
├── snapshots/v0/         # exact copy of the target skill = baseline; vN/ = each kept version
├── evals.json            # probes + assertions + train/held-out split
├── history.json          # structured per-experiment record AND the dashboard's data source
├── experiment-log.tsv    # one line per experiment, for quick monitoring
├── coverage-matrix.json  # which categories tried / kept / saturated
├── dashboard.html        # live dashboard shell — generated once (scripts/dashboard.py)
├── data.js               # dashboard data (window.DATA) — refreshed every experiment
├── resume.json           # checkpoint written at every S-stage transition — enables resuming an interrupted run
├── metric-explainer.md   # plain-English explanation of the composite metric, written once at S1
└── report.md             # final summary
```

**Git-native sandbox (deterministic, no subagent).** Right after the workspace + `snapshots/v0/` are
created: `git init`, write the `.gitignore` above, then `git add -A && git commit -m "v0: baseline
snapshot"`. From here on, git is the source of truth for *file state*; `resume.json` stays the
source of truth for *loop state* (stage, evals hash, scores) — see S3's commit protocol and
"Resuming an interrupted run" below for how the two stay in sync. This adapts `skill-evolver`'s
commit-before-verify workspace (see the design note at the bottom of this file): every mutation is a
real commit taken *before* it's graded, so a crash mid-verification leaves a clean, checked-out
commit behind instead of a half-written file — resuming is "read the last commit," not a
hand-written re-brief.

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

**Resume checkpoint (write at every S-stage transition):** at the end of every S-stage transition —
S0 done, S1 dry-run passed, each S3 decision, S4 saturation update, S5 stop, S6 promote — write/overwrite
`<sandbox>/resume.json`:

```json
{"stage": "<S-id>", "sandbox": "<path>", "evals_hash": "<sha256 of evals.json>",
 "best_version": "<id>", "baseline_score": <n>, "last_composite": <n>}
```

This is deterministic bookkeeping (no subagent) — fold it into the same step that already writes
`history.json` / `coverage-matrix.json` so it costs nothing extra.

### Resuming an interrupted run

A fresh session (crash, dropped connection, timeout mid-loop) reconciles **git first, then
`resume.json`** — git is the source of truth for what's on disk, `resume.json` is the source of
truth for what stage the loop was in:

1. Verify the sandbox dir still exists. If `.git/` is missing (a run predating this mechanism, or
   S0 never finished), fall back to the file-only reconciliation below with no git step.
2. `git status --porcelain` inside the sandbox. **Dirty tree ⇒ discard**: a mutation was being
   applied when the crash hit, *before* its commit — `git checkout -- .` (or `git clean -fd` for new
   untracked files) to drop it and treat that iteration as never started. A clean tree needs no
   action; git already holds the last completed step.
3. Read the last commit message (`git log -1 --format=%s`). If it ends `[score-pending]`, the
   mutation committed but grading never finished — resume at S3 step 3 (L1 gate) for that same
   mutation; the working tree is already the one to grade, do not re-mutate. Otherwise the last
   commit is a settled score/revert commit — resume at S3 step 1 (next hypothesis) from the
   current tree.
4. Recompute the sha256 of `evals.json` and confirm it matches `resume.json`'s `evals_hash`
   (mismatch ⇒ evals were regenerated or tampered — do not resume, restart at S1).
5. Cross-check `resume.json`'s `last_commit` against actual `git log -1 --format=%H`. They should
   match after step 2's cleanup; if they don't (an even earlier interruption in the
   commit-then-checkpoint order), trust git for file state and `resume.json` only for `stage` /
   `baseline_score` / `best_version` / `target` — those aren't derivable from git alone.
6. Continue the loop from `resume.json`'s `stage`, refined by steps 2–3 above:
   - `S0`/`S1` → redo setup / the dry-run gate.
   - `S3` → resume the experiment loop per steps 2–3 above, with `best_version` / `baseline_score` /
     `last_composite` from `resume.json` in hand.
   - `S4`/`S5` → re-check coverage/stop criteria against the logged state.
   - `S6` → finish promote + report; the sandbox may already be mid-teardown.

`resume.json`'s schema (S0) gains one field, written at the same step as the rest: `"last_commit":
"<sha of HEAD after the write>"`.

This is distinct from the Show-eval mode's same-session approval hand-off (see Execution modes above,
and `/handoff goal` for a session that hasn't started the loop yet) — resume.json recovers a run
that already entered S3, not a pre-approval hand-off.

## S1 — Setup (the wizard)

- **Goal:** accuracy, efficiency, or both — one line.
- **Target + scope:** the skill dir; scope = its `SKILL.md` + scripts. Copy it to `snapshots/v0/`.
- **Evals:** 6–12 realistic cases, each with **machine-checkable assertions** (+ a 1–2 line judge rubric
  for soft quality). Split **60% train / 40% held-out**; write `evals.json`. Auto-generate if none exist.
  **Typed assertion taxonomy (required):** every assertion declares a type — either **program-checkable**
  (`contains`, `regex`, `file-exists`, `script-check`, `line-count`, `structure`) or **judge-scored**
  (`semantic`, `style`). A stylistic preference (tone, phrasing, visual polish) MUST be typed judge-scored
  — never encoded as a hard program assertion; a program assertion on a stylistic detail fails brittle and
  can lock in an implementation choice the skill never claimed. **Pre-lock intent sanity pass (Show-eval
  gate, required before presenting):** for each assertion, run the check "does this assertion test
  something the target skill's own SKILL.md claims or implies?" — any assertion that constrains an
  unclaimed implementation detail is rewritten or downgraded to judge-scored before lock. **Show-eval:**
  present the (now sanity-passed) evals with rationale — each eval + type + the §S4 category it targets +
  why it is the right ruler — the one approval gate. **Auto:** generate, run the same sanity pass, and
  proceed.
- **Metric:** the composite score (S2) for accuracy; or, for a pure-efficiency/generic target, a shell
  command that prints one number (e.g. `… | tail -1`). Also write `<sandbox>/metric-explainer.md` the
  first time the composite is constructed — plain-English: what each component measures (assertion
  pass-rate, judge score, efficiency), what train/held-out means here, and the KEEP/REVERT rule in plain
  words. Any later "explain the metric" ask is answered by reading this file, not re-deriving it. On S6
  promote, copy it to `references/eval/` alongside `evals.json`.
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

**Layered mutation order:** attempt cheaper, higher-leverage layers before expensive ones —
**description/trigger wording → body structure → references → scripts**. Stay in the current layer until
it plateaus (**2 consecutive REVERTs within that layer**), then advance to the next; do not treat all
mutation categories as one flat pool. This is a finer-grained signal than S5's global 3-consecutive-REVERT
stop — a 2-REVERT plateau moves you to the next layer, it does not stop the run.

1. **Hypothesis** (main orchestrator, Opus 4.8): read the last evals' raw traces (input → output →
   per-assertion pass/fail) + the coverage matrix + any near-misses; pick the weakest area or least-covered
   category **within the current mutation layer** (see above); form ONE testable hypothesis AND state how
   it generalizes beyond the train cases.
2. **Mutate** (main orchestrator, Opus 4.8): copy the current best → `vN/`; apply ONE focused change —
   wording, an example, structure, a script, or a tightened/trimmed instruction (for efficiency), matching
   the current layer. Log what + why. **Commit before verifying:** `git add -A && git commit -m
   "iter-N: <one-line mutation summary> [score-pending]"`. This happens before step 3, not after — the
   commit is the audit record of the attempt regardless of what the grading step does next.
3. **L1 quick gate (before spending a grading pass):** run `skills/suite/scripts/skill-lint.sh` on the
   mutated sandbox skill, plus a non-crash dry parse of any changed scripts (`bash -n` for shell,
   `python3 -m py_compile` for Python). **On failure: REVERT immediately** (log as an `L1-FAIL` decision in
   `history.json`/`experiment-log.tsv`, then apply the git revert step under "Decide" below) — do not run
   train/held-out grading on a mutation that fails this cheap check.
4. **Run + grade** (only reached if the L1 gate passes): for each TRAIN eval, spawn a **Sonnet 4.6
   subagent** (`claude-sonnet-4-6`) to execute the mutated skill and run the machine assertions → outputs;
   then a SEPARATE **Opus 4.8 cold-judge subagent** (`claude-opus-4-8`) scores soft quality →
   `grading.json` (maker ≠ checker). Held-out runs too, but only to score — never shown to steps 1–2.
   Record per-case pass/fail (not just the aggregate) for both train and held-out — the AND-gate in step 6
   needs it.
5. **Score:** composite on train and held-out.
6. **Decide** (both modes decide automatically here — an **AND-gate**, not a single threshold):
   - **KEEP** only if ALL THREE hold: (a) `composite > baseline + 0.02` on train; (b) **no previously-
     passing held-out case regresses** — compare this version's per-case pass/fail against the current
     best version's, case by case, not just the aggregate delta; (c) `efficiency_score` does not degrade
     beyond the documented tolerance (default: no more than a 0.03 drop, or the skill's own stated budget
     if narrower). **Fail any leg → REVERT**, even if the aggregate composite moved up — a gain that costs
     a previously-working case or blows the efficiency budget is a trade, not an improvement.
   - **REVERT** if `composite < baseline − 0.05`, OR train improved but held-out did not (overfit), OR any
     AND-gate leg above fails.
   - **NEAR_MISS** if delta ∈ [−0.05, +0.02] and no AND-gate leg failed outright: revert, but mark the
     hypothesis promising (retry a different way / combine; drop it after 2 near-misses in the same
     category).
   - **NEUTRAL** (tie): keep the simpler/cheaper version (efficiency tiebreak — rule 6).

   **Git for the decision (deterministic, right after the call above, before step 7):**
   - **KEEP / NEUTRAL:** `git commit --allow-empty -m "iter-N: score train=<t> heldout=<h>
     decision=KEEP"` — a follow-up commit that replaces the `[score-pending]` marker with the
     result; the mutation commit's tree is what's kept. `best_version` becomes this commit's sha.
   - **REVERT / NEAR_MISS / L1-FAIL:** restore the tree to the last good state, `git checkout
     <best_version sha> -- .`, then `git commit -m "iter-N: REVERT to <best_version sha> after score
     train=<t> heldout=<h> decision=<REVERT|NEAR_MISS|L1-FAIL>"`. This is a *new* commit whose tree
     equals the previous best — the failed mutation commit stays reachable in history for the audit
     trail (nothing is force-reset or rebased away); `best_version` is unchanged.
7. **Log + refresh dashboard:** append the experiment to `history.json` (in the dashboard schema) +
   `experiment-log.tsv` (timestamp, hypothesis, before, after, delta, decision, category); update the
   coverage matrix and `best`; write `resume.json` (see S0), including `last_commit` = the sha the
   Decide step above just produced; then run `python3 scripts/dashboard.py <sandbox>` to refresh
   `data.js` (the open dashboard picks it up on its next 5s tick; `dashboard.html`/`data.js` stay
   gitignored, they're regenerated, not source of truth). Deterministic — no subagent.

## S4 — Coverage matrix (steer exploration → exploitation)

Categories: `formatting · content_quality · examples · workflow · edge_cases · efficiency · scripts ·
structure`. Track per category: experiments, kept, best_delta, saturated. **Saturated** = ≥3 experiments,
none > +0.01. The hypothesis step prefers untouched categories early (explore), re-tries high-success
categories late (exploit), and avoids saturated ones — **within whichever mutation layer (S3) is currently
active**; a category belonging to a later layer (e.g. `scripts`) is not eligible until that layer is reached.

## S5 — Stop criteria

composite ≥ target (e.g. 0.95, shown as 95%) on the held-out set · `max_experiments` (default 10) · 3 consecutive
NEUTRAL/REVERT (plateau) · 3 consecutive crashes (infra problem). Write `resume.json` with `stage: "S5"`
before moving to S6.

## S6 — Promote + clean up

On green (held-out ≥ baseline, no regression): back up canonical, `rsync` the winning snapshot over the
canonical skill, re-run the eval against canonical to confirm identical-green (roll back the backup if
not). Copy `evals.json` → the skill's `references/eval/` (permanent regression fixture — the skill now
carries its own ruler). **Also copy `metric-explainer.md`** into `references/eval/` alongside it (written
at S1 — see above). **Static dashboard snapshot (before sandbox deletion):** run `python3
scripts/dashboard.py <sandbox> --static` — a self-contained variant with `history.json`'s data inlined
directly into the HTML (no external `data.js` fetch, no auto-reload/auto-stop script) — and copy that
file into `references/eval/dashboard-snapshot.html`. This is what survives after the sandbox (and its live
tab) are gone; the already-open live tab is a convenience during the run, not the durable record. Have a
**Sonnet 4.6 subagent** write `report.md` — **short, plain English, zero jargon**, written for Jono to
read after the sandbox is deleted.

**REPORT RULES — the subagent must follow these exactly:**

**❌ Forbidden words — translate every one:**
| Instead of… | Write… |
|---|---|
| `eval` / `evals` | "test cases" or "checks" |
| `dry-run` | "quick test" |
| `composite` / `composite score` | "overall score" |
| `assertion` / `assertion pass-rate` | "accuracy checks" or "automatic checks" |
| `held-out` | "hidden test cases" or "fresh tests it hadn't seen" |
| `train` / `train set` | "practice tests" (only in the stats table; omit label elsewhere) |
| `S1` / `S2` / `S3` … `S6` | do not appear anywhere in the report |
| `baseline_composite` | "starting score" |
| `snapshot` | do not use |
| `NEAR_MISS` | "NEAR MISS" (spaces, no underscores) — stats table only |

**❌ Never write a decimal like `0.83`. Always write `83.00%`.** Every score, improvement, and target is written as `X.XX%` — no exceptions.

**Report structure (follow this order, use these headings):**

1. **What this skill does** — one sentence on what the skill is for in plain English, then one sentence on why it was tuned (what wasn't working consistently enough).
2. **What changed** — each kept change in one plain line ("before, it did A; now it does B"). Describe behavior, not file names or code.
3. **What was tried that didn't help** — one line each, plain reason.
4. **Result & what to expect** — write it as: `Starting score: X% → Final score: Y% (improved by +Z%)`. Then 2–3 sentences in plain English on what Jono will notice when using the skill now compared to before.
5. **The numbers** — a table with these columns: `Change | Score before | Score after | Improvement | Result`. Fill all score columns as `X.XX%`. "Result" column: `KEPT`, `REVERTED`, `NEAR MISS`. This is the one place technical labels are fine.

No ASCII chart. Lead with skill purpose + result. Keep it tight — the goal is one short page.
Set `history.json` `status: "done"` (or `"stopped"` if aborted)
and run `scripts/dashboard.py <sandbox>` once more so an open dashboard freezes on the final state and stops
auto-refreshing. Write a final `resume.json` with `stage: "S6"` (harmless after teardown; only matters if
teardown itself is interrupted). **Then delete the sandbox workspace** (the ephemeral dashboard goes with
it, and so does the entire per-iteration `.git/` history built during S3 — no experiment commit, revert
commit, or intermediate mutation ever leaves the sandbox; only the files named in the "Persist" sentence
below survive). The orchestrator reports baseline vs final score per held-out probe. The dashboard tab the agent
opened at S1 stays open in the browser, now **frozen on the final state** (status `done`/`stopped` stops
the auto-refresh) — it **survives this teardown** because it was opened live at S1. **Persist `report.md`,
`evals.json`, `metric-explainer.md`, and the static `dashboard-snapshot.html` to `references/eval/` BEFORE
deleting the sandbox** so the run's results outlive both the ephemeral dashboard file and the live tab.
(All scores the orchestrator reports here — baseline vs final per probe — are shown as percentages, per
the Principles.)

## Overfitting protection (carried from skill-forge)

Held-out probes never feed hypothesis/mutation (only scoring); every hypothesis must justify how it
generalizes; coverage-matrix diversity + saturation prevents tunnel-vision; refresh/rotate the eval split
every 5 experiments; a 3-consecutive-crash circuit breaker stops an infra loop instead of spinning.

> Provenance: Karpathy `autoresearch` (one metric · constrained scope · fast verify · auto-rollback · git
> memory) → `skill-forge` Skill Mode (composite score on a SKILL.md) → this. The S0/S3 git-native sandbox
> (commit-before-verify, resume = read the last commit) is adapted from `FishSerrie/skill-evolver`'s
> workspace. Generic loop mechanics live in `/autoresearch`. More prior art: `justinwetch/Skill-RSI`
> + `SkillEval`, `stancsz/skills-flow`.
