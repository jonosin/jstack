---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up. Use when you need a recap, a directed attended handoff, or a `/goal` prompt from an existing execution spec.
argument-hint: What will the next session be used for? "[recap | directive <instruction> | goal [focus]]"
---

# handoff

If the user gives a file path, read that file as the conversation source instead of the current
conversation.

| Argument | Mode | Reference |
|---|---|---|
| empty or `recap` | Recap | `references/recap.md` |
| `directive <instruction>` or bare text | Directive | `references/directive.md` |
| `goal [focus]` | Goal | `references/goal.md` |

## Recap and directive

Write a handoff document summarising the current conversation so a fresh agent can continue the
work. Save it to `~/.jstack/handoffs/session-YYYY-MM-DD-<slug>.md` (add `-2`, `-3`, and so on when
needed).

Include a `## Suggested skills` section in the document.

Reference content already captured in specs, plans, ADRs, issues, commits, or diffs by path or URL.
Redact sensitive information, such as API keys, passwords, and personally identifiable information.

Treat the directive or bare argument as the next session's focus and tailor the document to it.

## Goal

Use goal only when an execution spec already exists. If it does not, direct the user to
`/to-spec`. Goal returns the prompt described in its reference; the spec remains the source
of truth.