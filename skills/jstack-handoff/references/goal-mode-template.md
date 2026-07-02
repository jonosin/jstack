# Goal-mode prompt template

The recurring `/goal` preamble is generated from this template, not hand-typed each session. Fill
the `{SLOTS}`; everything else ships verbatim into the handoff.

```
/goal {ONE-SENTENCE GOAL with a single verifiable stop condition: command + expected output}
You have NO memory of the planning session — read {HANDOFF-FILE-PATH} first; it is the
self-contained state file. Run from {REPO-PATH}; all relative paths resolve against it.
Execute autonomously, milestone by milestone: spawn subagents for each milestone's heavy
work, each returning a short summary; then a SEPARATE checker subagent verifies the
milestone's done-condition by running its stated command and matching the stated output
(maker ≠ checker). Keep the main context lean: orchestrate and review; never do heavy work
inline. Re-read the plan's constraints at the start of every milestone. After each
milestone update the plan's Progress/Decision Log so you can recover from compaction.
Resolve ambiguities yourself and log them. Commit only as the plan directs. Never stop to
ask. Stop only when: {STOP CONDITION}.
```

## Slots

| Slot | Fill with |
|------|-----------|
| `{ONE-SENTENCE GOAL...}` | The measurable objective from `references/goal.md` Step 1 — one sentence, one verifiable stop condition. |
| `{HANDOFF-FILE-PATH}` | The absolute path the plan was saved to (`~/.jstack/handoffs/session-YYYY-MM-DD-<slug>-goal.md`). |
| `{REPO-PATH}` | The repo the executor must run from — never assume it's inferable; state it explicitly. |
| `{STOP CONDITION}` | The same stop condition as the goal sentence, restated as the exact command + expected output. |

Count the filled result with `wc -c` and keep it under 1500 characters (per `references/goal.md`
Step 3); tighten prose before dropping a verifiable condition.

## The rule this template encodes

Every goal handoff document MUST open with:
- A **repo + working-directory block** — `Run from `{REPO-PATH}`; all relative paths resolve against
  it.` — cross-repo continuations break silently without this.
- The **stop-condition command and its exact expected output**, not a subjective description of done.
