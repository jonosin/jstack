# Cold Runner contract

## Role
A fresh-context **Sonnet 4.6** subagent that EXECUTES a candidate premortem skill against ONE
scenario and writes ground-truth artifacts. It is the **maker** of a run: it never grades, and it
never sees the judge rubric, `grade.py`, the train/held-out split, or which assertions exist. Its
only job is to behave exactly as the candidate `SKILL.md` says when a user pastes the scenario.

## Inputs
1. The candidate `SKILL.md` text — taken from the sandbox snapshot **under test** (not the
   installed copy). This is the behavior the run must reflect.
2. The `scenario` string from `evals.json` (the user's plan, who it affects, what success means).
3. An output `<rundir>` to write artifacts into.

## How to behave
- Follow the candidate `SKILL.md` **faithfully**, as if a user pasted the scenario and triggered the
  skill. Do not add steps the skill does not call for; do not skip steps it requires.
- Deep-dive subagents called for by the skill may be **simulated inline** — but each failure reason
  must still carry its underlying **assumption** plus **>=1 early warning sign**, exactly as a real
  deep dive would produce.
- **Negative / low-stakes ask** (e.g. "quick feedback on this tweet"): per the skill's "Do NOT
  trigger" rule, **decline to run a premortem** and answer directly. Write no report.
- **Under-specified plan** (missing affected-party or success definition): ask the **single most
  important** missing question, then proceed. Do not over-ask — exactly one question.

## Outputs (write into `<rundir>`)
- `transcript.md` — the full premortem transcript: the explicit
  **"6 months from now, it failed, looking backward"** frame, the raw failure reasons, the deep
  dives (assumption + early warning per reason), and the synthesis.
- `report.html` — self-contained, per the skill's artifact contract.
- `result.json` — matches the schema documented at the top of `grade.py`, **accurately reflecting
  what was actually produced**. No inflation: the deterministic grader cross-checks the artifacts
  (e.g. it re-verifies the frame phrasing inside `transcript.md`/`report.html`).

## result.json field reminders
`declined`, `asked_question`, `question_count`, `frame_stated`, `num_reasons`,
`reasons[]{title, has_assumption, has_warning}`,
`synthesis{most_likely, most_dangerous, hidden_assumption, revised_plan, checklist}`,
`revised_plan_text`, `chat_output` (the <=3 sentence chat summary),
`transcript_path`, `report_path`.

For a declined/negative run: set `declined=true`, `num_reasons=0`, and leave `report_path` empty.
