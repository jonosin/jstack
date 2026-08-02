---
name: jstack-grilling
description: "Work through a code or strategic decision while maintaining its canonical workspace artifact. Use when the user wants to grill, think through, or stress-test a code, product, business, marketing, or strategy decision; choose the branch before asking questions."
---

# jstack-grilling

Choose the artifact owner before asking the first question:

| Situation | Load |
|---|---|
| Codebase design, implementation, architecture, or domain terminology | `references/code.md` |
| Product, business, marketing, GTM, offer, positioning, or strategic decision | `references/strategy.md` |

Do not mix branches. If the request materially contains both, settle the strategic decision first,
then start a fresh code-grilling session from the resulting workspace artifact.

## Questions

Never ask grilling questions as inline chat prose. Use the host's structured user-input tool:

- Claude Code: invoke `AskUserQuestion`.
- Codex: invoke `request_user_input` when it is available.

Put only decision-ready questions in that tool, offer the recommended answer first, and group only
independent questions into a single invocation. Do the investigation and analysis in the normal
conversation; use the tool only at the point where user judgment is required.

The code branch uses frontier rounds. The strategy branch is a natural, opinionated working
conversation: investigate first, contribute a point of view, and only ask bounded questions that
need the user's judgment. Facts are the agent's job to investigate; decisions are the user's.

When the host has no structured-input tool (including ChatGPT), ask the smallest necessary
decision-ready question in ordinary chat, include the recommended option first, and wait for the
answer before continuing. Do not simulate unavailable tools.

For either branch, the workspace owns the full artifact. In a venture/build repository, update the
artifact and regenerate `docs/index.md`; do not capture the session into the second brain. The
brain sees only the registered `docs/index.md` symlink.

When the host cannot write the workspace (including ChatGPT), maintain the canonical artifact in a
single Markdown code block instead. Label it with its recommended path, update that block whenever a
decision changes, and tell the user to save it in the owning workspace. Never claim the file was
created or the index regenerated.

## Next skills

| Next | When |
|------|------|
| `/jstack-premortem` | The resolved strategy or design needs an adversarial failure pass. |
| `/jstack-handoff` | The resulting artifact will be implemented in a fresh session. |
