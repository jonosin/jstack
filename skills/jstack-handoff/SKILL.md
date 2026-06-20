---
name: jstack-handoff
description: Compact the current conversation into a handoff for another agent to pick up. Two categories — Normal (a handoff document the next attended session reads and continues) and Goal (an autonomous /goal prompt that runs unattended in a fresh session). Modes — recap, directive, goal. Saves to ~/.jstack/handoffs/session-YYYY-MM-DD-[slug].md.
argument-hint: "[recap | directive <what to do> | goal <objective>]  (omit = recap — re-orient a fresh session to continue this work, file-pointer handoff)"
---

If given a file path, read that file as the conversation source instead of the current conversation.

## Two axes decide everything

1. **What artifact?**
   - **Normal** — a handoff *document* the next session reads and continues. You'll be back at the
     keyboard (attended).
   - **Goal** — an autonomous **`/goal` prompt** that runs *unattended*: `/goal` loops turns, an
     independent judge grades "done" each turn, persists across `/resume`. You're away.
2. **Who sets the objective?** You describe it (**directed**), or the agent infers it from this
   session (**agent-decides**).

| | agent-decides | directed |
|---|---|---|
| **Normal** | `recap` | `directive` |
| **Goal** | `goal` | `goal <objective>` |

## Parse the argument → mode

| Argument | Mode | Reference |
|----------|------|-----------|
| empty | **recap** (Normal / agent-decides) — re-orient a fresh session to continue this work (file-pointer handoff) | `references/recap.md` |
| starts with `directive` (or any descriptive text with no keyword) | **directive** (Normal / directed) | `references/directive.md` |
| starts with `goal` | **goal** — rest of the line is the objective (directed); empty rest = agent-decides | `references/goal.md` |

**Goal requires the explicit `goal` keyword** — never fire an unattended autonomous run from bare
text. If you're unsure whether the user wants Normal or Goal, ask one line:
*"Directive (you'll be at the keyboard) or goal (autonomous, unattended)?"*

## Shared rules (all modes)

- Save to `~/.jstack/handoffs/session-YYYY-MM-DD-<short-slug>.md` (append `-2`, `-3` if the path
  exists). Slug from the directive/goal, or the session topic in recap. The **goal** mode suffixes
  the slug with `-goal`.
- Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues, commits,
  diffs). Reference them by path or URL instead.
- Redact any sensitive information (API keys, passwords, PII).
- If your setup has a canonical-state save skill, mention it so the user can run that too when canon
  changed.
- Include a **Suggested skills** section listing skills the next agent should load.

## Next skills

| Next | When |
|------|------|
| `/jstack-handoff-from-claude` | Companion — you need to pull a different (non-current) Claude session into a handoff via its session ID. |
| `/jstack-savetobrain` | The session also produced durable knowledge worth preserving in the second brain, separate from the next-agent handoff. |
