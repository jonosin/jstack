# regression — layered stability gate: baseline vs candidate → STABLE/UNSTABLE before you push

Ported faithfully from `uditgoenka/autoresearch` `.agents/skills/autoresearch/regression.md`.
Invocation: `/jstack-autoresearch regression [Base: <ref>] [Scope: <glob>] [--select auto|full|affected]
[--samples N] [--noise-band %] [--matrix] [--max-runs N] [--baseline-cache] [Baseline: <prebuilt-ref>]
[--probe|--no-probe|--probe deep] [--predict --reason --debug --fix --fix-cycles N --evals --chain]`.
EXECUTE IMMEDIATELY.

A regression is a **green→red transition ONLY**. This gate orchestrates the project's OWN
test/bench/snapshot/migrate commands (a protocol, not a bundled framework), captures baseline behavior in
an isolated git worktree, re-runs the candidate, and reports a tiered ship/no-ship verdict.

## Parse arguments

- `Base:`/`--base` — base ref to diff against. Default `git merge-base HEAD main` (else `main`/`master`).
- `Scope:`/`--scope` — file globs limiting the change surface.
- `--select auto|full|affected` — test selection (default `auto`; `auto` = affected-test mapper if
  available, else FULL — never a silent subset).
- `--samples N` — SCORE samples/side (default 7). `--noise-band %` — perf tolerance (default 5%).
- `--matrix` (off by default). `--max-runs N` (default 200). `--baseline-cache` (on) reuses
  `baseline/<full-sha>/` by SHA. `Baseline: <prebuilt-ref>` bypasses capture.
- `--probe`(default)/`--probe deep`/`--no-probe`; `--predict --reason --debug --fix --fix-cycles N --evals
  --evals-interval N --chain <targets>` and `--<sub>` shorthand; `Iterations:` repeat-axis count.

## Setup / probe-on-launch

1. Auto-detect per-dimension verify commands (`package.json` scripts, `Makefile`, `nx`, migrate config,
   bench/snapshot/size scripts). 2. Confirm detected commands + base ref + dimensions with the user (single
   batch). 3. **Auto-skip probe** in CI / no-TTY / autonomous mode / complete-config / chained handoff — log
   the inferred config instead of asking.

## Classification phase (first-class, before any differential)

Establish the baseline green-set per dimension, then tag each unit (match by test-id first, then path):

| State | Meaning | Gated? |
|---|---|---|
| `regression-eligible` | green on baseline | YES — only green→red counts |
| `pre-existing` | red→red (already failing) | no — excluded |
| `new-coverage` | absent→red (brand-new test) | no — ungated |
| `flaky` | nondeterministic on baseline | no — routed to flakiness SCORE |
| `baseline-unavailable` | dimension never green | no — advisory only |

**Core invariant: red→red, absent→red, and flake→red are NOT regressions.** Run flakiness N× on **both**
baseline and candidate; a candidate failure inside the baseline flake-envelope routes to flakiness SCORE,
never to a regression. `5/5 green ≠ non-flaky` — detection probability is `1−(1−p)^n` (≈23% at p=5%, n=5); print it.

## Baseline capture

`git worktree add --detach <full-sha>` → `baseline/<full-sha>/` (detached SHA avoids "branch already
checked out" when Base==HEAD); `--baseline-cache` reuses by SHA. Per worktree: `git submodule update
--init` + dependency install (lockfile is SHA-pinned). Per-dimension setup tiers: api-contract = file-diff,
no build; functional / integration-e2e / data-migration = full env. On completion/crash: `git worktree
remove` + `git worktree prune`. `Baseline: <prebuilt-ref>` bypasses capture.

## Dimension registry (8)

| Dim | Tier | Compare | Key params |
|---|---|---|---|
| functional | HARD | baseline green-set vs candidate; new fail = regression | test cmd, globs |
| api-contract | HARD | schema/exports diff → breaking? | schema cmd, breaking ruleset |
| data-migration | HARD | up applies clean + idempotent re-apply + app boots/schema valid | migrate cmds, fixture, allowlisted DB |
| integration-e2e | HARD | e2e green-set diff | e2e cmd |
| flakiness | SCORE | run N× on baseline + candidate, count nondeterministic | runs (def 5), flake-threshold |
| performance | SCORE | K independent-process samples/side, Mann-Whitney U AND effect beyond `max(noise-band%, k·stdev)` | bench cmd, samples=7, noise-band=5%, k=2 |
| resource | SCORE | mem/bundle/size delta vs budget | size cmd, budget |
| visual-ui | SCORE | containerize render; default maxDiffPixelRatio + AA-detection; SSIM = per-page escalation | snapshot cmd, threshold, masks |

`--select auto` mapper (`jest --findRelatedTests`, `nx affected`) is best-effort static-import — blind to
dynamic/runtime/global-setup couplings. The report names the mapper + its blind-spot caveat; a HARD STABLE
on an affected subset prints "run `--select full` for high-stakes." FULL suite is the correctness default.

- **performance independence:** each sample = an independent process launch (warmups discarded), never an
  in-process iteration. At n=7 the test detects only ≳1σ regressions; raise `--samples` for tight gates.
- **data-migration guard:** opt-in. Before any migration the DB URL MUST pass an **anchored** allowlist —
  host is exactly `localhost`/`127.0.0.1`/a container hostname, OR the db name carries a `_test`/`_ci`
  suffix (a bare substring like `test` in `latest` does NOT qualify). Ephemeral only, never dev/prod, and
  even an allowlisted URL needs explicit confirm. Missing down-migration = forward-only advisory, never a finding.

## Differential loop (per dim × axis × run)

Run candidate verify vs baseline metric → compute `regressed` bool + 0–100 `subscore`. Axes: `diff`
(default), `repeat N×`, `full`, `matrix` (opt-in). One TSV row per cell. **--max-runs ceiling:** projected =
dims × axes × samples × matrix-cells; if > `--max-runs` (200) → warn + require confirm (CI = abort).

## Verdict

- Any HARD `regressed=true` with `classification=eligible` → **UNSTABLE** (green→red hard-blocks).
- Else `stability_score = Σ(weight × dim_subscore)` over SCORE dims that ran (flakiness .30 / performance
  .30 / resource .20 / visual .20, renormalized over present dims). **STABLE iff ≥ 95** (overridable).
- Print the score math (per-dim contribution table) + declare dims-ran vs UNAVAILABLE (never silently passed).

## Hunter (root cause)

On a confirmed HARD regression, auto-engage. Bisect ONLY when the failing case passes a **3/3
reproducibility gate**. SCORE / non-deterministic regressions → differential root-cause (+ optional
`--reason`/`--predict`), no bisect. Non-reproducible → "manual triage" finding.

## --fix re-gate

`--fix` repairs blocking regressions, max **3 cycles** (`--fix-cycles N`). Each cycle MUST strictly shrink
the blocking-set else STOP "fix not converging." Final cycle runs the full battery. No HARD-gate bypass.

## Output, handoff, safety

Output dir `autoresearch/regression-{YYMMDD}-{HHMM}/` → `regression-results.tsv`, `stability-report.md`,
`dimensions/<dim>.md`, `baseline/`, `evals-summary.md` (if `--evals`), `handoff.json`. TSV header:
`# metric_direction: higher_is_better` then `iteration\ttimestamp\tdimension\taxis\ttier\tclassification\t
baseline\tcandidate\tdelta\tregressed\tsubscore\tseverity\tstatus\tfile_line\tdescription`. `handoff.json`
carries `verdict` ∈ {STABLE, UNSTABLE, BASELINE_UNAVAILABLE} (ship reads it for the deploy gate). Safety:
verify-command screen, worktree cleanup/prune on crash, data-migration DB allowlist, chained `ship` never
auto-deploys.
