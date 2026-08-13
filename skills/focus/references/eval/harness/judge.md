# Cold judge contract — focus ruler (readability + completeness)

The judge scores the soft axis (the 0.30 term in the composite): **is this response easy
to read and follow at a glance, while keeping everything that needed surfacing?** The
deterministic hard constraints (em dashes, filler openers, required facts present, shape
flags) are handled by `grade.py`, not here.

## Inputs (and ONLY these)
1. One candidate file: `<rundir>/<probe_id>.txt`.
2. That probe's `gold_example` (a reference for what a good answer looks like).
3. That probe's `judge_rubric` (1–2 lines on what this probe is testing).

The judge does **not** see the SKILL.md, the assertions, or any other probe. Blind
comparison against the reference so the skill text can't game it.

## Scoring
Score the candidate on these, weighted by the probe's `judge_rubric`:
- **Scan-ability** — can the user get the answer in the first line/glance? Lead with the
  point, not preamble.
- **Right shape** — the format fits the content. Prose for a simple answer; a list/table
  or a small ASCII diagram ONLY when it genuinely makes the content faster to grasp.
  Penalize gratuitous structure on a simple answer AND a wall-of-prose where a 3-item
  list or diagram would have been far clearer.
- **Completeness** — every decision-relevant fact is still there. Compression must not
  drop something the user needed.
- **Decisiveness** — when options are weighed, a clear recommendation leads, not a
  neutral menu.
- **Texture** — warm, direct, no narration, no padding, plain honesty.

Return a single number in `[0, 1]`:
- `1.0` = effortless to read, perfectly shaped, nothing important lost.
- `~0.5` = right content but mis-shaped (wall of text that should be a list, or a list
  that should be one sentence) OR slightly padded / buried lead.
- `0.0` = hard to read, or dropped something important, or off-voice.

## Output
Output **only the number**. No words, no JSON, no explanation.

## Repetition
Run each probe **at least 3 times** and take the mean. Collect per-probe means into a
judge file the grader consumes:

```
{ "<probe_id>": [s1, s2, s3], ... }   # each s in [0,1]
```

Pass it with `--judge <judge.json>`.
