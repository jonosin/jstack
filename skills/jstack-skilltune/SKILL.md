---
name: jstack-skilltune
description: "Tune an EXISTING jstack skill to improve its ACCURACY or EFFICIENCY — a metric-driven autoresearch loop (adapted from GodModeAI2025/skill-forge) that, in a temp sandbox, mutates the SKILL.md one change at a time, scores each against a held-out eval set (assertions + cold judge + efficiency), keeps wins / reverts regressions, promotes on green, then deletes the sandbox. Use when Jono names an existing skill and says 'tune this skill', 'make this skill more accurate', 'make this skill's output consistent / reliable', 'improve/iterate/optimize this skill', 'make the skill more efficient', 'eval this skill', or '/jstack-skilltune <name>'. NOT for creating a new skill or restructuring one into deterministic code — that is /jstack-skillify."
---

# jstack-skilltune

Tune an existing skill that works but whose output is **inconsistent, inaccurate, or wasteful**. Mutate the
`SKILL.md` / scripts ONE change at a time, score each change against a frozen eval set, keep improvements,
revert regressions, until the score plateaus. The composite score covers two optimization targets:

- **Accuracy** — assertion pass-rate + cold-judge quality.
- **Efficiency** — tokens / time / tool-calls (or a generic shell metric like bundle size, lint count).

The generalized loop engine is **`/jstack-autoresearch`**; this skill is its skill-specific lens. To
*restructure* a skill or push fuzzy steps into deterministic code, use **`/jstack-skillify`** (harden) —
tuning never redesigns or widens scope.

**Invoke:** `/jstack-skilltune <existing-skill-name>`. The full S0–S6 loop mechanics live in
**`references/tune-mode.md`** — load and follow it.

**Live dashboard.** The loop runs `scripts/dashboard.py <sandbox>` to render a dependency-free,
`file://`-safe `dashboard.html` — composite-over-experiments chart (train vs held-out vs baseline vs
target), a color-coded mutations table (KEEP / REVERT / NEAR_MISS), and a coverage heatmap. It auto-reloads
every 5s, auto-stops when the run finishes, and has a sticky **Stop/Resume** button. **The agent opens it
ITSELF the moment it is first generated (S1) — `open` / `xdg-open` / `start` — and MUST NOT wait for or
rely on a human to open it; this is identical in BOTH Auto and Show-eval modes** (in Auto/cron there is no
human to tell, so a deferred "tell Jono to open it" guarantees the live tab never appears). The already-open
tab survives S6 teardown frozen on the final state, so it stays viewable after the sandbox is deleted —
S6 also copies a static, self-contained snapshot of it plus `metric-explainer.md` into the target skill's
`references/eval/`, so the result survives even a closed tab. An interrupted run resumes from
`<sandbox>/resume.json` (written at every stage transition) instead of a hand-written re-brief — see
"Resuming an interrupted run" in `references/tune-mode.md`.

**Scores are shown as percentages — no exceptions.** The loop computes in [0,1] internally, but every
score / delta / target / baseline shown to Jono — the dashboard, the chat summary, and `report.md` — is
rendered as a percentage (×100, 2 decimals, e.g. `83.40%`, delta `+2.00%`). **Never write a raw decimal
like `0.83` in any user-facing output.** Raw-metric runs (KB / ms / tokens / lint) keep their real units.
`report.md` is written in **plain English, zero jargon, short** — skill purpose, what changed, what
didn't stick, the result + what to expect, then a stats table. Forbidden jargon in the report: `eval`,
`dry-run`, `composite`, `assertion`, `held-out`, `train set`, `S1`–`S6`, `snapshot`, `baseline_composite`.
See `references/tune-mode.md` S6 for the exact report template and translation table.

## Execution modes — two only

Both modes run the S3 loop under the **`/goal` engine** (turn-looping, an independent judge each turn,
maker ≠ checker). They differ only in whether Jono gates the eval set first.

- **Auto** — fully autonomous; decides and runs end-to-end until an S5 stop. Triggered when invoked under
  `/goal` (`/goal /jstack-skilltune <name>`, or `/loop 30m /goal /jstack-skilltune <name>` for runs past
  ~20 turns) **or** with an explicit `auto` arg (`/jstack-skilltune <name> auto`). It generates the evals
  (S1) and **surfaces them + the reasoning in its thinking/output** so Jono can watch and abort — but it
  does **NOT** wait for confirmation; it continues automatically.
- **Show-eval** (default — a bare `/jstack-skilltune <name>` with no `/goal`/`auto`) — the ONE attended
  gate. Infer the optimization target, generate the 6–12 evals + record the baseline (S1 incl. dry-run
  gate), **show them with the "why"**, and wait for Jono to approve/edit. On approval, do NOT run the loop
  inline and do NOT re-invoke this skill (it is already in context) — emit a ready-to-paste `/goal`
  objective pointing the already-loaded loop at the approved sandbox. A fresh/unattended session is
  delegated to `/jstack-handoff goal`, not handled here. (Full detail: `references/tune-mode.md`.)

## Iron contract

Skills are user-trust artifacts. A broken skill erodes confidence. Work in a temp sandbox, test there, and
only move into the canonical path on test pass plus explicit user approval (Show-eval) or a green held-out
gate (Auto). On either failure, remove the sandbox entirely. No "almost shipped" state. **The eval is the
ruler — never weaken or delete a probe to force a green gate.**

## Orchestration — Opus drives, Sonnet does the grunt work

The main session is the **orchestrator on Opus 4.8** and does the *important, non-repetitive* work itself:
forming hypotheses, mutating the skill/files, and every keep/revert · stop/promote decision. Delegate only
**grunt / repetitive / token-heavy** work — running eval cases, machine assertion checks, writing the
report, bookkeeping — to **Sonnet 4.6 subagents** (`claude-sonnet-4-6`), spawned aggressively, one job
each, so their bulky output never enters the main context. When an *important* task must run as a
**separate** subagent (the cold quality-judge, to keep maker ≠ checker), use an **Opus 4.8 subagent**
(`claude-opus-4-8`). Smart / creative / judgment → Opus; repetitive / mechanical / verbose → Sonnet 4.6.

## Next skills

| Next | When |
|------|------|
| `references/tune-mode.md` | The S0–S6 loop mechanics, principles, coverage matrix, overfitting protection. Load before running. |
| `/jstack-autoresearch` | The generic metric loop engine this specializes — read for the underlying rules. |
| `/jstack-skillify` | You need to *restructure* the skill or push fuzzy steps into deterministic code (harden), not tune it. |
| `/goal` (or `/loop 30m /goal …`) | Run unattended: `/goal /jstack-skilltune <name>` is Auto mode — the loop runs itself end-to-end. |
| `/jstack-handoff` (goal) | Hand a fresh/unattended session the job of running the tune loop with approved evals. |
| `/jstack-savetobrain` | The tuned skill's eval results are durable knowledge worth ingesting into the second brain. |
