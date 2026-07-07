# implement — clear-spec bulk implementation on GPT-5.5

Only for work that passed the global bulk-lane threshold (5+ files / 100+ repetitive
lines / data-crunching sweep) with a genuinely clear spec. Ambiguous or taste-critical
work stays with the lead model.

Prompt skeleton:

```
# Outcome
Implement [feature/fix] in this repo.

Success means:
- [behavioral acceptance criteria]
- existing conventions are followed
- relevant tests/build/type checks pass
- final answer lists changed files, validation run, and residual risks

# Constraints
Reuse existing patterns and helpers. Keep scope to the requested behavior.
Allowed side effects: edit files inside the workspace and run local validation.

# Autonomy
Proceed with reasonable assumptions. Ask only if a missing choice would materially
change the implementation or cause risky side effects.

# Validation
Run targeted checks first, then broader checks if you touched shared code. If checks
fail, fix clear causes and rerun.

# Output
Concise Markdown: Summary, Files Changed, Validation, Assumptions/Risks.
```

Run: `codex-run.sh run <prompt> --write --effort medium --timeout 1800`,
`run_in_background: true`, from the repo root (codex edits the workspace it runs in).

Parallel implement lanes: each in its own git worktree — never two write-capable codex
runs in one checkout.

After the run: review the diff yourself (`git diff`) before presenting. You own what
ships; codex doesn't.
