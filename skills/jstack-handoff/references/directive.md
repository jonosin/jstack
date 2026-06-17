# Handoff — directive mode (Normal / directed)

Produces a handoff **document** for an attended next session (you'll be back at the keyboard).

You described what the next session should do. **You set the objective; the agent decides what to
feed forward** — curate the handoff around your directive: pull in only the session facts that serve
it, drop dead ends and tangents, and carry your directive instructions through to the next agent.

Slug from the directive. Apply the shared rules from `SKILL.md` (save path, no-duplication,
redaction, **Suggested skills** section).

Output the resolved absolute path and a copy-pasteable resume line:

```
Handoff saved at: ~/.jstack/handoffs/session-YYYY-MM-DD-<slug>.md

Copy-paste to resume:
  Please read ~/.jstack/handoffs/session-YYYY-MM-DD-<slug>.md and continue from there.
```
