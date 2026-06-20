# Core loop — modify → verify → keep/discard against a metric

Ported faithfully from `uditgoenka/autoresearch` `.agents/skills/autoresearch/autoresearch.md`.
Invocation: bare `/jstack-autoresearch ...`. EXECUTE IMMEDIATELY — do not deliberate before reading this protocol.

## Parse arguments

Extract from the invocation:
- `Goal:` — what to improve
- `Scope:` or `--scope` — file globs
- `Metric:` — what to measure
- `Direction:` — higher_is_better (default) or lower_is_better
- `Verify:` — shell command that outputs a number
- `Guard:` — optional safety command (must always pass)
- `Iterations:` or `--iterations` — integer N for bounded mode (default: 25); "unlimited" for unbounded
- `--evals` — enable mid-loop checkpoints; `--evals-interval N` — checkpoint frequency override
- `--chain <targets>` — comma-separated downstream commands

## Setup (if required context missing)

If Goal, Scope, Metric, or Verify is missing → ask the user in a single batched call:
- Q1 (Goal): "What do you want to improve?"
- Q2 (Scope): "Which files?" — suggest globs from the project
- Q3 (Metric+Verify): "How to measure? Provide a shell command that outputs a number"
- Q4 (Guard): "Safety command that must always pass?" — options: test cmd, build cmd, skip

If ALL provided inline → skip setup, proceed directly.

## Precondition checks

1. Verify a git repo exists (`git rev-parse --git-dir`).
2. Check a clean working tree (`git status --porcelain`) — warn if dirty.
3. Check for stale lock files, detached HEAD.
4. If Guard set → run Guard to establish the guard baseline.
5. Fail fast on any critical issue; warn on non-critical.

## Verify safety screen

Before the first dry-run, screen the Verify command for: `rm -rf`, fork bombs, `curl|sh`, embedded
credentials, outbound writes. Block dangerous commands.

## Establish baseline (iteration 0)

1. Run Verify → extract the numeric metric.
2. Record as iteration 0 in the TSV: `0\t{timestamp}\t{commit}\t{metric}\t0.0\t{guard}\t-\tbaseline\tinitial state`.
3. Create the output directory: `autoresearch/loop-{YYMMDD}-{HHMM}/`.
4. Write the TSV header: `# metric_direction: {direction}` then
   `iteration\ttimestamp\tcommit\tmetric\tdelta\tguard\tguard-metric\tstatus\tdescription`.

## Iteration loop

For each iteration (1..max, or unbounded):

**Phase 1 — Review (git history as memory):** read the last 10–20 TSV lines; run `git log --oneline -20`
to see what worked/failed; if the last iteration was a keep, run `git diff HEAD~1` to see what improved the
metric. Identify: what worked, what failed, what is untried.

**Phase 2 — Modify:** based on the review, make ONE focused, atomic change to improve the metric.

**Phase 3 — Commit:** stage + commit with an `experiment: {description}` prefix. Record the commit SHA.

**Phase 4 — Verify:** run Verify → extract the new metric; compute delta from the previous iteration. Metric
improved in the correct direction → candidate for keep.

**Phase 5 — Guard (if configured):** run Guard. If it fails → revert regardless of metric improvement.

**Phase 6 — Decide:**
- **keep** — metric improved, guard passed → commit stays.
- **discard** — metric worsened → `git revert HEAD --no-edit`.
- **crash** — verify/guard command failed → `git revert HEAD --no-edit`.
- **no-op** — no change made this iteration.
- **hook-blocked** — a git hook blocked the commit.
- **metric-error** — verify output not a valid number → `git revert HEAD --no-edit`.

**Phase 7 — Log:** append a TSV row: iteration, timestamp, commit/-, metric, delta, guard status,
guard-metric, status, description.

**Eval checkpoint:** if `--evals` and `current_iteration % interval == 0` → run checkpoint analysis.

**Bounded check:** if bounded and `current_iteration >= max_iterations` → exit loop, print summary.

## Summary (after the loop)

Print: total iterations, kept/discarded counts, starting metric → final metric, improvement %, and the
top 3 most effective changes.

## Eval checkpoint (`--evals`)

- Interval = `floor(max_iterations / 3)`, min 1. Fixed 10 if unbounded. Override `--evals-interval N`.
- Every interval, pause and analyze the current TSV. Print 5 lines max:
  ```
  --- Eval Checkpoint (iterations {X}-{Y}) ---
  Metric: {start} → {end} ({delta}) | Kept: {n}/{total} | Trend: {up/flat/down}
  {one-line recommendation}
  ---
  ```
- If plateau for 3+ checkpoints → recommend early stop. At loop end → full summary to
  `evals-summary.md` in the output directory.

## Chain handoff

After completion, write `handoff.json` to the output directory: version "2.1.0", source "loop", timestamp,
status (COMPLETE | USER_INTERRUPT | BOUNDED | ERROR), `results_tsv` path, `findings[]`,
`config{goal, scope, metric, direction, verify}`. Invoke the next `--chain` target in order; propagate `--evals`.
