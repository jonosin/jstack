# improve — research ICP challenges, discover improvements, generate PRDs

Ported faithfully from `uditgoenka/autoresearch` `.agents/skills/autoresearch/improve.md`.
Invocation: `/autoresearch improve [Goal: <text>] [--icp <text>] [--discover] [--seeds <cats>]
[--depth shallow|standard|deep] [Iterations: N] [--evals]`. EXECUTE IMMEDIATELY.

A research loop, not a code loop: it discovers what to build (insights → ranked features → PRDs), rather
than optimizing a number. Use it to turn a product area into an evidence-backed improvement plan.

## Parse arguments

- `Goal:` — product area to improve (or full input if no keyword).
- `--icp`/`ICP:` — ideal customer profile. `--discover` — force inline codebase scan. `--no-discover` —
  skip auto-discover, warn instead. `--seeds <categories>` — override default research seeds.
- `--depth` — shallow (5 iters) / standard (15) / deep (30). `--features` — comma-separated names to
  pre-select for PRDs. `Iterations:`/`--iterations` (default 15; "unlimited"). `--evals`/`--evals-interval N`.

If an upstream `handoff.json` exists in CWD → read it; map source findings to default seeds (probe → ICP
challenges, UX; predict → competitor gaps, revenue; debug/security → competitor gaps, ICP challenges).
Override with `--seeds`.

## Setup (if Goal or ICP missing)

Ask the user in a single batch: Q1 (Goal) product area; Q2 (ICP) ideal customer; Q3 (Pain points) top 3;
Q4 (Competitors) key ones or "skip"; Q5 (Depth) shallow/standard/deep. If all inline → skip.

## Phase 1 — Product context

Resolve in priority order: 1. most recent `autoresearch/learn-*/summary.md`; 2. README.md (≥500 chars,
non-boilerplate); 3. manifest description (`package.json`/`pyproject.toml`/`Cargo.toml`, ≥10 chars);
4. if all absent and not `--no-discover` → auto-discover (scan ~10 key files, cap 1500 tokens);
5. `--discover` forces the scan; 6. nothing found → warn and suggest `learn --mode summarize`.

## Phase 2 — Research loop

Output dir `autoresearch/improve-{YYMMDD}-{HHMM}/`; TSV header `# metric_direction: higher_is_better`;
columns `iteration|timestamp|category|research_question|status|source|insight_problem|insight_mechanism|confidence|classification`.

**5 research categories:** ICP challenges · competitor gaps · market trends · UX & experience · revenue & growth.

**Iteration protocol:** reserve the first 5 iterations (one per category, forced breadth); remaining
iterations target the richest-signal categories. Per iteration: form a research question → web search →
synthesize → normalize to the insight schema → classify (new/extension/duplicate) → tag confidence (HIGH
3+ sources, MEDIUM 2, LOW 1) → cross-check against the codebase → log. **Saturation:** net-new insights < 2
for 3 consecutive non-reserved iterations → SATURATED, exit. The Iterations flag is the infinite-loop guard.

**Insight schema:** `{problem: 10-word canonical, affected_persona, proposed_mechanism, expected_outcome}`.
**Classification:** New = novel {problem, persona}; Extension = same pair, different mechanism; Duplicate =
same pair + mechanism → skip.

## Phase 3 — Feature ranking + selection

1. ICP binary gate (drop insights not serving the stated ICP). 2. 3-tier bucketing (Must-have /
Nice-to-have / Moonshot). 3. Pairwise ranking within Must-have only (cap 7–10). 4. 2-sentence rationale per
item citing evidence. 5. Confidence indicator per item. Write `improvement-plan.md`. Then ask the user
(multi-select) which features become PRDs (`--features` pre-selects, still confirm).

## Phase 4 — PRD generation

Per selected feature, write `prd-{slug}.md`: top disclaimer (auto-generated, DECISION NEEDED + LOW-confidence
need judgment); problem statement (evidence chain); user stories (ICP + persona); requirements (functional +
non-functional, MoSCoW from tier); acceptance criteria; technical approach (codebase context as "suggested
starting points"); risks + confidence (primary = codebase, secondary = web); success metrics; `DECISION
NEEDED` markers; `Open Questions`. Also write `research-findings.md` (all insights + citations) and
`summary.md` (overview, stats, coverage, saturation).

## Summary + handoff

Print: total iterations, insights (new/extension), categories covered, saturation status, PRDs generated,
output path. `--evals` → `evals-summary.md`. Write `handoff.json` (source "improve", status COMPLETE|
SATURATED|..., findings = improvements with tier + confidence + prd_path). Improve is a terminal emitter —
no downstream chain invocation.
