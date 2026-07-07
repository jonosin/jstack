# GPT-5.5 prompt style (distilled 2026-07-07 from OpenAI primary sources)

Full research with citations: ~/.jstack/docs/superpowers/specs/2026-07-07-gpt55-prompting-research.md

## The shape (Markdown, outcome-first — replaces all GPT-5.4 XML blocks)

```
# Outcome        ← the completed result + "Success means:" observable criteria
# Constraints    ← scope limits, allowed side effects, conventions to follow
# Autonomy       ← proceed/ask rules: proceed when reversible; ask only when a missing
                   choice changes the outcome or authorizes a risky side effect
# Validation     ← concrete checks to run after changes; what to do on failure
# Output         ← sections + budget; machine-validated JSON goes in --schema, not prose
# Evidence / # Research / # Search Budget ← only for grounded/research tasks
```

## Rules

- Smallest prompt that preserves the contract. Outcome and success criteria over
  process narration — remove step-by-step process unless the path itself matters.
- One clear task per run. Split unrelated asks into separate runs.
- Effort: medium default (implementation); high/xhigh only for reviews and
  eval-proven hard tasks. 5.5 over-searches at high effort — always give research
  prompts a search budget and a stop rule.
- Structured output: use codex-run.sh --schema <file> (maps to --output-schema);
  keep only the human-readable shape in the prompt.
- Dropped from the 5.4 era: <dig_deeper_nudge> (causes over-searching),
  XML block structure (Markdown headers now; XML only for nested examples or
  long-document wrapping), schemas embedded in prompt text.
- Kept from the 5.4 era (shortened): proceed/ask autonomy rules; action-safety
  ("respect the sandbox; no irreversible/external actions unless authorized").
