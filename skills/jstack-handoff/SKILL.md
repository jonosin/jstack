---
name: jstack-handoff
description: Compact the current conversation into a handoff document so a fresh agent can continue. Two modes — recap (preserve session state) and directive (you describe what the next session should do, and the handoff is curated around that goal). Save to ~/.jstack/handoffs/session-YYYY-MM-DD-[slug].md. Use when the user wants to preserve session state or set up the next session's task.
user_invocable: true
---

If given a file path, read that file as the conversation source instead of the current conversation.

## Pick the mode

- **Recap** — no argument, or the user just says "save context" / "hand off" / "preserve this". Summarize the session so any new agent can continue where this one left off.
- **Directive** — the user describes what they want to do next (e.g. `/jstack-handoff start building the X parser`). The next session may pivot to something new. Curate the handoff around that goal: pull in only the current-session context that serves it, then end with the directive so the next agent just starts executing.

## Write the handoff

Save to `~/.jstack/handoffs/session-YYYY-MM-DD-[short-slug].md`. Append `-2` if that path exists. Slug from the directive in directive mode, from the session topic in recap mode.

**Recap** answers: what we were doing, what changed, what we decided, what's undecided, what files matter, what to do next, what not to redo.

**Directive** is a self-contained brief written for a cold agent who has only this file:
- **Task** — the user's directive, stated as the next session's goal.
- **Context** — only the session facts, decisions, files, and constraints that serve that goal. Drop the rest.
- **Start here** — the concrete first action, so the next session begins doing the work instead of re-planning.

Don't duplicate content already in artifacts (PRDs, plans, ADRs, issues, commits). Reference them by path. Suggest skills the next session should load.

When done, output the full absolute path and a copy-pasteable line the user can send to resume:

```
Handoff saved at: ~/.jstack/handoffs/session-YYYY-MM-DD-[slug].md

Copy-paste to resume:
  Please read ~/.jstack/handoffs/session-YYYY-MM-DD-[slug].md and continue from there.
```

Output the resolved absolute path (expand `~`) so the line is directly copy-pasteable.

This skill captures session state. If your setup also has a canonical-state save skill, mention it so the user can run that too when canon changed.
