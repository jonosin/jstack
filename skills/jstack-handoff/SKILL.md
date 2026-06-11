---
name: jstack-handoff
description: Compact the current conversation into a handoff document for another agent to pick up. Two modes — recap (preserve session state) and directive (curate around a goal the next session will work on). Save to ~/.jstack/handoffs/session-YYYY-MM-DD-[slug].md.
argument-hint: "What will the next session be used for?"
---

If given a file path, read that file as the conversation source instead of the current conversation.

Pick the mode:
- **Recap** — no argument. Summarise the session so any new agent can continue where this one left off.
- **Directive** — user describes the next session's goal. Curate the handoff around it: pull in only the session facts that serve that goal.

Write the handoff to `~/.jstack/handoffs/session-YYYY-MM-DD-[short-slug].md` (append `-2`, `-3` if path exists). Slug from the directive in directive mode, from the session topic in recap mode.

Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information (API keys, passwords, PII).

If your setup has a canonical-state save skill, mention it so the user can run that too when canon changed.

Include a **Suggested skills** section listing skills the next agent should load.

Output the resolved absolute path and a copy-pasteable resume line:

```
Handoff saved at: ~/.jstack/handoffs/session-YYYY-MM-DD-[slug].md

Copy-paste to resume:
  Please read ~/.jstack/handoffs/session-YYYY-MM-DD-[slug].md and continue from there.
```
