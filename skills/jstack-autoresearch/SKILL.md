---
name: jstack-autoresearch
description: "Autonomous goal-directed iteration loop: modify, verify, keep/discard against ANY mechanical metric — until the metric stops improving or the iteration budget runs out. A faithful port of Karpathy's autoresearch (via uditgoenka/autoresearch, the generalized Claude-skill version). Use when Jono says /jstack-autoresearch, 'autoresearch this', 'iterate until <metric> improves', 'optimize X against a metric', 'run an improvement loop', 'keep tuning until the number goes up/down', or wants an unattended modify→verify→keep/revert loop on code, content, configs, or skills. Routes to per-command references: the core loop, plan (goal→config), improve (research→PRDs), evals (analyze runs), regression (stability gate). For tuning a SKILL's output specifically, see /jstack-skillify Mode B, which applies this engine to skills."
---

# jstack-autoresearch — autonomous goal-directed iteration

Ported from **`uditgoenka/autoresearch`** (5k★, MIT), itself a generalization of
**`karpathy/autoresearch`**: *constraint + mechanical metric + autonomous iteration = compounding gains.*
A 630-line script improved ML models ~100 experiments/night via simple principles — one metric,
constrained scope, fast verification, automatic rollback, git as memory. This skill carries those
principles to ANY domain with a number you can measure: code, content, configs, prompts, or skills.

> **"Set the GOAL → the agent runs the LOOP → you wake up to results."** You don't need AGI; you need a
> goal, a metric, and a loop that never quits.

## Invocation — `/jstack-autoresearch [command]`

Bare `/jstack-autoresearch` = the core loop. A leading command word routes to that command's reference
(jstack has no colon-namespaced commands, so `plan`/`improve`/`evals`/`regression` are args, not `:subs`).

## Safety invariants (ALL commands)

- **Never push, publish, or deploy without explicit user approval.**
- **Bounded by default.** Every looping command has a default iteration count; unbounded is opt-in via
  `Iterations: unlimited`.
- All results logged to `autoresearch/{command}-{YYMMDD}-{HHMM}/` (TSV + summary). The log is the memory.
- Chain handoff via `handoff.json`; `evals` reads `*-results.tsv`.
- **Verify-command safety screen** before first run: block `rm -rf`, fork bombs, `curl|sh`, embedded
  credentials, outbound writes.

## The 8 rules (the battle-tested core — do not weaken)

1. **Bounded by default** — unlimited is explicit opt-in.
2. **Read before write** — understand full context before modifying.
3. **One change per iteration** — atomic; if it breaks, you know exactly why.
4. **Mechanical verification only** — a number from a command, never subjective "looks good."
5. **Automatic rollback** — a worse metric or a failed guard reverts the commit instantly.
6. **Simplicity wins** — equal metric + less code/complexity = keep the simpler one.
7. **Git is memory** — commit experiments with an `experiment:` prefix; read `git log`/`git diff` before each iteration.
8. **When stuck, think harder** — re-read, combine near-misses, try a radical change before giving up.

## Commands

| Command | Does | Default iters | Reference |
|---|---|---|---|
| *(bare)* | Iterate against a metric: modify → verify → keep/discard | 25 | `references/loop.md` |
| `plan` | Convert a goal into a validated Scope / Metric / Direction / Verify config | N/A | `references/plan.md` |
| `improve` | Research ICP challenges → discover improvements → generate PRDs | 15 | `references/improve.md` |
| `evals` | Analyze a run's results TSV: trends, plateaus, regressions, recommendation | N/A | `references/evals.md` |
| `regression` | Stability gate: baseline vs candidate across dimensions → STABLE/UNSTABLE before you push | N/A | `references/regression.md` |

**Extension commands available upstream (port on demand — not yet copied):** `debug`, `fix`, `security`
(STRIDE+OWASP), `ship`, `scenario`, `predict`, `learn`, `reason`, `probe`. Fetch from
`uditgoenka/autoresearch` `.agents/skills/autoresearch/<cmd>.md` and drop into `references/` when needed.
The upstream repo also ships 9 Node safety hooks (`.claude/hooks/autoresearch/*.cjs`) — optional hardening,
host plumbing, not part of the loop; port only if you want enforced guardrails.

## Universal flags

| Flag | Applies to | Purpose |
|---|---|---|
| `Iterations: N` / `Iterations: unlimited` | all looping | bounded count / opt-in unbounded |
| `--evals` / `--evals-interval N` | all looping | mid-loop checkpoints + final summary |
| `--chain <targets>` / `--<command>` | all | sequential handoff after completion |

## Next skills

| Next | When |
|------|------|
| `/jstack-skillify` (Mode B) | The thing you are iterating is a SKILL's output consistency — skillify applies this engine with an eval set + holdout split. |
| `/jstack-handoff` (goal) | You want the loop to run unattended overnight — emit a `/goal` prompt that drives this loop in a fresh session. |
| `/jstack-savetobrain` | A loop's findings/results are durable knowledge worth keeping in the second brain. |
