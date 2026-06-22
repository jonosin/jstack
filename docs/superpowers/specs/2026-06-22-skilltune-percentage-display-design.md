# jstack-skilltune — percentage display + plain-English report

Date: 2026-06-22
Status: approved
Scope: presentation-only (dashboard + report + chat summary). No math, schema, or eval logic changes.

## Goal

Two user-facing changes to `jstack-skilltune`:

1. **Show scores as percentages, not decimals.** Everywhere a score is shown to the user — the live
   dashboard, the orchestrator's chat summary, and the final report — render `×100` with **2 decimals**
   and a `%` suffix (`0.834 → 83.40%`, delta `0.02 → +2.00%`).
2. **Make the final `report.md` easy to understand** — short, concise, plain English, least jargon.

## Core principle — convert at the display layer, never in the math

The loop computes everything in `[0,1]`. That stays. Converting only at render is one surgical layer that
cannot regress the loop.

- **Unchanged (internal math):** `history.json` / `data.js` schema; the S2 weights (`0.50 / 0.30 / 0.20`);
  the S2/S3 decision thresholds (`+0.02` keep, `−0.05` revert, `[−0.05, +0.02]` near-miss); the dry-run
  gate's "composite in `[0,1]`" validation; the chart's internal 0–1 y-scaling.
- **Converted (display only):** any score / delta / target / baseline / best shown to the user.

**Exception:** raw-metric runs (the optional `metric` block — bundle size KB, latency ms, tokens, lint
count) keep their real units. Percentage applies only to the `[0,1]` score convention.

## Change 1 — `scripts/dashboard.py` (display functions only)

- `fmt(v)`: score case (no `metric` block) → `(v*100).toFixed(2) + "%"`; metric case unchanged. This one
  edit fixes the header stats (baseline / best / target), the train + held columns, **and** the Δ column
  (it reuses `fmt`, so deltas render `+2.00%`).
- `fmtAxis(t)`: score case → `(t*100).toFixed(0) + "%"` → gridlines read `0% / 25% / 50% / 75% / 100%`;
  metric case unchanged.
- Coverage `best_delta`: score case → `(x*100).toFixed(2) + "%"` with sign; metric case unchanged.

The chart's internal 0–1 scaling is untouched — only axis/value labels change.

## Change 2 — rewrite the final `report.md` (S6) into plain English

Replace the terse data-dump brief ("start→end score, top 3 mutations, dead ends, coverage, ASCII chart")
with a short, plain-English report. Sections, in this order:

1. **Goal** — one or two sentences: which skill, why it was tuned (what was off), what "better" meant.
2. **What I changed** — the kept changes, each one plain line ("before, it did A; now it does B").
3. **What I tried that didn't stick** — brief, with the reason it didn't help.
4. **Outcome & what to expect** — `baseline X% → final Y% (+Z%)` and, in plain words, what you'll notice
   when you use the skill now.
5. **The stats** — the mutations table (change · train% · held% · Δ% · decision) plus baseline / final /
   target. The table is the one place technical labels are acceptable.

Rules for the report:
- All numbers as percentages, 2 decimals.
- Translate jargon: *composite* → "overall score"; *assertion pass-rate* → "the automatic checks";
  *held-out* → "fresh cases kept hidden so it couldn't game them".
- Drop the ASCII chart — the table carries the per-experiment detail, the prose carries the story (the live
  chart already lives on the dashboard, which the report outlives).
- Keep it short. Lead with goal + outcome; back it with the stats table.

## Change 3 — display rule + chat summary

- Add one rule to `references/tune-mode.md` Principles (and a short note in `SKILL.md`): scores are `[0,1]`
  internally; any score / delta / target / baseline shown to the user — chat, dashboard, or report — is
  `×100`, 2 decimals, `%` (e.g. `0.834 → 83.40%`, `0.02 → +2.00%`). The S2 weights and S2/S3 decision
  thresholds are internal math — leave them decimal. Raw-metric runs keep their units.
- S6 "orchestrator reports baseline vs final per held-out probe" → reported as percentages, plainly.
- Human-facing example numbers in the prose (e.g. "target (e.g. `0.95`)") → "`95%`", while the threshold
  math (`+0.02` / `−0.05`) stays decimal.

## Files touched

- `skills/jstack-skilltune/scripts/dashboard.py`
- `skills/jstack-skilltune/references/tune-mode.md`
- `skills/jstack-skilltune/SKILL.md`

## Verification

- Build a synthetic 2–3 experiment `history.json`, run `python3 scripts/dashboard.py <sandbox>`, open the
  generated `dashboard.html`: confirm header, axis labels, train / held / Δ columns, and coverage delta all
  read `NN.NN%`.
- Build a `metric`-block `history.json` (e.g. bundle size KB), run the dashboard, confirm it still renders
  raw units (`KB`), **not** `%`.
- Check `report.md` brief against the new outline.
- Run `bash tools/secrets-gate.sh` before any push.

## Out of scope

- No change to which mutations the loop keeps (presentation-only).
- No change to eval generation, the held-out split, or the composite formula.
