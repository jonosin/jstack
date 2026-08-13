# Cold runner contract — jstack-voice ruler

The cold runner produces the **candidate** for one probe: the raw text a coding
agent would emit with the voice skill active.

## Inputs (and ONLY these)
1. The full content of the active `SKILL.md` under test (the candidate skill body).
2. ONE probe's `user_turn` string from `evals.json`.

The runner sees **nothing else** — no conversation history, no `gold_example`, no
`judge_rubric`, no other probes, no assertions. This keeps the candidate honest:
the skill text alone has to drive the voice.

## Task
Read the SKILL.md as if it were just activated, then answer the single `user_turn`
exactly as a coding/strategy agent would with that voice in force. Produce only the
response a user would see. Do not explain that a skill is active, do not narrate
your process, do not restate the question.

## Output
Write the response text, and nothing else, to:

```
<rundir>/<probe_id>.txt
```

One file per probe, named by the probe `id`. The grader reads exactly that path.
Raw text only — no JSON wrapper, no surrounding markdown fence around the whole
answer (code fences *inside* the answer are fine and expected on code probes).

## Notes
- Run each probe in a fresh, independent context. No state carries between probes.
- The candidate is graded verbatim, so leading filler, em dashes, or stray planning
  scaffolding will be caught deterministically by `grade.py`.
