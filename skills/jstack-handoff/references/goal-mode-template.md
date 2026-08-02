# Goal-mode prompt template

Fill the `{SLOTS}`; the result is the fresh task's initial prompt.

```
/goal {ONE-SENTENCE GOAL with a single verifiable stop condition: command + expected output}
You have NO memory of the planning session — read {HANDOFF-FILE-PATH} first; it is the outcome-led
execution contract. Run from {REPO-PATH}; all relative paths resolve against it. Read its linked
spec/ticket on demand; it owns detailed implementation scope. Re-read the contract's constraints and
AGENTS.md before changing work. Update Progress/Decision Log after material work so you can recover
from compaction. Resolve reversible ambiguity and log it. Use an independent checker for consequential
or ambiguous validation. Never echo secrets or widen scope. Stop only for missing authority, an
irreversible unapproved external action, an interactive credential/login, or a decision that cannot
safely be resolved. State the smallest unblock and exact resume point. Stop when: {STOP CONDITION}.
```

| Slot | Fill with |
|---|---|
| `{ONE-SENTENCE GOAL...}` | One measurable objective and stop condition. |
| `{HANDOFF-FILE-PATH}` | Absolute path to the saved handoff. |
| `{REPO-PATH}` | Explicit repo working directory. |
| `{STOP CONDITION}` | The same exact command and expected output. |

Keep the filled prompt below 1500 characters. Every handoff opens with its repo working directory and
the Outcome stop-condition command plus expected output.
