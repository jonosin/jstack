# review — independent GPT-5.5 review of a diff, branch, or plan

## Route A (default for local git changes): the openai-codex plugin

Use `/codex:review` (standard) or `/codex:adversarial-review` (ship-gates). Their
review contracts and result handling are mature — do not rebuild them.

## Route B (plans, prose, non-git artifacts, or when the plugin is unavailable)

Brief via codex-run.sh. Prompt skeleton:

```
# Outcome
Review [diff/branch/files/plan] for bugs, regressions, security risks, bad
assumptions, and missing tests.

Success means:
- findings are specific, actionable, and prioritized
- each finding cites file/line or exact evidence
- no style-only comments unless they hide real risk
- if no issues are found, say so and name residual risk

# Constraints
Read-only. Do not edit files. Be skeptical of happy-path reasoning. Check contracts,
edge cases, data flow, migrations, permissions, and test coverage.

# Output
Markdown:
1. Findings, highest severity first
2. Open questions
3. Test gaps / residual risk
```

Run: `codex-run.sh run <prompt> --effort high --timeout 900` (xhigh for ship-gates),
`run_in_background: true`, from the repo root so codex can read the tree.

Surface per SKILL.md result handling: severity order, verdict first, NEVER auto-apply —
present findings, then stop and ask which to fix.
