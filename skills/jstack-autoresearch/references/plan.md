# plan — convert a goal into a validated Scope / Metric / Direction / Verify config

Ported faithfully from `uditgoenka/autoresearch` `.agents/skills/autoresearch/plan.md`.
Invocation: `/jstack-autoresearch plan [Goal: <text>] [--chain <targets>]`. EXECUTE IMMEDIATELY.

This is the setup phase: it turns a fuzzy goal into a ready-to-run loop config. Use it before the core
loop when the metric/verify command isn't obvious.

## Parse arguments

- `Goal:` — text after the keyword, or the full input if no keyword.
- `--chain <targets>` — comma-separated downstream commands; `--<command>` is chain shorthand.
- Remaining text = goal description.

## Setup (if Goal missing)

Ask the user in a single batch:
- Q1 (Goal): "What do you want to achieve?" — open text.
- Q2 (Type): "What kind of goal?" — improve a metric / fix errors / audit security / explore edge cases /
  document code / ship something.
If Goal provided → skip.

## Phase 1 — Analyze goal

Determine: is it measurable (metric-driven vs subjective)? What is the natural scope (files, modules,
whole codebase)? Which command fits best (core loop, fix, debug, security, ...)?

## Phase 2 — Derive scope

1. Scan project structure. 2. Identify files relevant to the goal. 3. Propose file globs. 4. If ambiguous
→ ask the user to confirm.

## Phase 3 — Derive metric + direction

- Metric-driven goals: identify what to measure (test coverage, error count, bundle size, latency, ...);
  determine direction (higher_is_better / lower_is_better); propose a metric name + description.
- Subjective goals: suggest proxy metrics where possible, or recommend the `reason` command for
  non-measurable goals.

## Phase 4 — Derive Verify command

1. Identify how to extract the metric as a number from a shell command.
2. Propose the Verify command (e.g. `npm test -- --coverage | grep "All files" | awk '{print $10}'`).
3. **Safety screen:** check for `rm -rf`, fork bombs, `curl|sh`, credentials.
4. Dry-run it → confirm it outputs a valid number. If the dry-run fails → adjust and retry.

## Phase 5 — Derive Guard (optional)

Propose a Guard if applicable: test suite (`npm test` / `pytest` / `go test ./...`), type check
(`tsc --noEmit` / `mypy`), or build (`npm run build`). None if not applicable.

## Phase 6 — Suggest iterations

By complexity: simple metric improvement → 10–15; moderate refactoring → 20–25; complex multi-file → 30+.
Recommend the bounded default and mention `Iterations: unlimited`.

## Phase 7 — Present config

Output a ready-to-run block:

```
/jstack-autoresearch
Goal: {derived goal}
Scope: {derived globs}
Metric: {derived metric}
Direction: {higher_is_better|lower_is_better}
Verify: {derived command}
Guard: {derived guard or omit}
Iterations: {suggested count}
```

Ask: "Run this config now, or adjust?"

## Chain handoff

If `--chain` set: write `handoff.json` (version "2.1.0", source "plan", timestamp, status COMPLETE,
config = the derived block); invoke the next target with the derived config.
