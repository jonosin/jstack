# investigate — diagnosis, research, data analysis on GPT-5.5

Prompt skeleton:

```
# Outcome
Answer [question] from repo evidence, provided data, and/or primary sources.

Success means:
- sources or observed commands are listed
- factual claims are cited or tied to evidence
- uncertainty and inferences are labeled (prefix INFERENCE:)
- final answer directly resolves the question

# Research
Use primary sources first. Start with one broad pass; search again only if required
facts are missing, results conflict, or exhaustive coverage was requested. Stop once
the core answer is supported.

# Constraints
Read-only. Do not modify files or external systems.

# Output
Markdown: Answer / Evidence / Inferences / Confidence & gaps
```

Run: `codex-run.sh run <prompt> --effort medium --timeout 900`,
`run_in_background: true`.
- Add `--search` when the question concerns the current world (docs, releases, prices).
- Raise to `--effort high` for deep multi-system diagnosis.

Scope note: the global research-routing rule still applies — for general web research
the research-router stack (Exa/Tavily) comes first. codex investigate is for
repo-grounded questions, data crunching, and when an independent second-model read is
the point.
