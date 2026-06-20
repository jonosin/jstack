# evals — analyze a run's results TSV: trends, plateaus, regressions, recommendation

Ported faithfully from `uditgoenka/autoresearch` `.agents/skills/autoresearch/evals.md`.
Invocation: `/jstack-autoresearch evals [path/to/results.tsv] [--format text|json|md]`. EXECUTE IMMEDIATELY.

## Parse arguments

- Positional path to a specific TSV file.
- `--format` — text (default console), json, md (markdown file).

## Input discovery

1. Path provided → use that TSV. 2. No path → scan CWD + `autoresearch/*/` for `*-results.tsv`.
3. Multiple found → ask which to analyze. 4. None found → ask for a path. 5. Also scan the project root
for legacy TSV files (backward compat).

## Parse TSV

1. Line 1: extract `# metric_direction: higher_is_better|lower_is_better`; if missing, infer from column
   names or ask. 2. Line 2: header row → detect available columns. 3. Remaining lines: data rows. 4. Handle
   a missing `timestamp` column gracefully.

## Column detection & analysis

Activate analysis based on the columns present:

| Column | Analysis |
|---|---|
| `metric` | trend direction, plateau (3+ flat iters), diminishing returns, biggest single-iter jumps |
| `delta` | per-iteration efficiency, cumulative improvement, effort-to-gain ratio |
| `status` | keep/discard rate, crash frequency, success streaks, failure clusters, longest winning streak |
| `guard` + `guard-metric` | guard failure rate; metric-improved-but-guard-failed analysis |
| `severity` | severity distribution; critical discovery rate per iteration |
| `hypothesis` + `status` | confirmation rate, investigation efficiency, most productive techniques |
| `commit` | file hotspot analysis (cross-ref `git diff` on kept commits), change-size correlation |
| `technique` | technique effectiveness ranking |
| `dimension` | dimension coverage completeness (X/12) |
| `candidate_label` + `judge_verdict` | convergence speed, oscillation count |
| `error_type` | error category distribution, fix rate per category |
| `classification` | new vs extension vs duplicate ratio, saturation curve |
| `convergence_count` | convergence trajectory |

Unknown columns: report presence, skip analysis (forward-compatible).

## Report structure

```
## Evals Summary — {command} ({N} iterations)

### Key Metrics
- Total iterations: N | Kept: X | Reverted: Y | Revert rate: Z%
- Starting metric: A | Final metric: B | Improvement: C%

### Trend Analysis
- Metric progression: [trajectory]
- Plateau detected at iteration N (stable for M iterations)
- Biggest win: iteration X (+delta, description) | Biggest loss: iteration Y (-delta, description)
- Diminishing returns: [after iteration N, avg delta dropped below threshold]

### Patterns
- What succeeded / what failed [from kept vs discarded descriptions]
- File hotspots [most-changed files in kept iterations, if commit data]
- Technique effectiveness [ranked by confirmation rate, if technique column]

### Recommendation
- [continue / stop / change strategy — based on trend, plateau, revert rate]
- [specific actionable suggestion from pattern analysis]
```

## Output

- Console: structured report (30–50 lines).
- `--format md` → write `evals-summary.md` beside the input TSV. `--format json` → `evals-summary.json`.

## Mid-loop checkpoint protocol (the `--evals` flag other commands embed)

- **Adaptive interval:** `floor(max_iterations / 3)`, min 1. Fixed 10 for unbounded. Override `--evals-interval N`.
- **Checkpoint (5 lines max):**
  ```
  --- Eval Checkpoint (iterations {X}-{Y}) ---
  Metric: {start} → {end} ({delta}) | Kept: {n}/{total} | Trend: {up/flat/down}
  {one-line recommendation}
  ---
  ```
- **Early stop** if plateau for 3+ consecutive checkpoints. **Final summary** at loop end → console + `evals-summary.md`.

Adaptive interval examples: reason(8)→2; learn(10)→3; debug/security(15)→5; fix/scenario(20)→6;
core(25)→8; unbounded→every 10.
