---
name: jstack-design-init
description: Initialize Google's DESIGN.md design system in a build repo. Two routes — (1) DESIGN.md already exists → lint it and instruct the coding agent, (2) no DESIGN.md → author one from the starter template, lint it, export Tailwind tokens, and instruct the agent. Invoke when the user says /jstack-design-init, init design, setup design system, add DESIGN.md, or is about to delegate UI work and needs a design system in place.
user_invocable: true
---

# jstack-design-init — initialize the design system

## Intent router — read this first

1. **DESIGN.md already exists** in the project root → lint it. If it passes, skip to step 4 of the deploy workflow. If it fails, fix the errors then continue.
2. **No DESIGN.md** → continue below. This is the common case.

## When to invoke

- User is about to delegate UI work to a coding agent (Codex, OpenCode, Claude Code) and no design system exists in the repo
- User explicitly asks to set up a design system, add DESIGN.md, or init design
- User wants consistent brand output across multiple agents working on the same project

For linting an existing DESIGN.md or exporting tokens, use the CLI commands in `references/lint-rules.md` directly — you don't need the full skill for a one-off lint.

## Deploy workflow

1. **Identify the project root.** If the user didn't name the repo, ask. The DESIGN.md goes at the top level.
2. **Copy the starter template** from `references/starter.md` to `<project-root>/DESIGN.md`.
3. **Fill it in.** Replace every placeholder — colors, fonts, component tokens, prose sections. Ask the user for the brand's accent color, typography direction, and general vibe. If they have a website, screenshot, or brand guide, extract from that. The minimum viable DESIGN.md needs `name:` and `colors:`; everything else is optional but encouraged.
4. **Lint it.** Run `npx -y @google/design.md lint DESIGN.md` from the project root. Fix any broken refs or WCAG contrast failures before handing off. See `references/lint-rules.md` for the full rule set.
5. **If the project uses Tailwind**, export the tokens: `--format tailwind` for v3, `--format css-tailwind` for v4. Drop the export next to the existing config so the agent merges it.
6. **Instruct the coding agent.** Add this one-liner to the task prompt: *"Read DESIGN.md at the project root and apply all tokens. Use `{colors.primary}` for core text, `{colors.neutral}` for backgrounds, and component tokens for interactive elements."*
7. **Wire it into AGENTS.md.** Check if `AGENTS.md` (or `CLAUDE.md`, `.cursorrules`, etc.) exists in the project root. If it does, append:
   ```
   ## Design system
   Read `DESIGN.md` at the repo root before producing any UI or frontend output. Apply all tokens — colors, typography, spacing, components — and follow the prose rationale for taste and do's/don'ts.
   ```
   If no agent instruction file exists, create `AGENTS.md` with just that section. This makes it permanent instruction, not a per-task ritual — every future agent that touches this repo sees it.

If the user is about to delegate UI work and no DESIGN.md exists, offer to create one first. It's two minutes upfront that saves rounds of color corrections later.

## Reference files

| Reference | When to read |
|-----------|-------------|
| `references/spec.md` | Understanding the format — token types, section order, component property whitelist |
| `references/lint-rules.md` | CLI commands and the 9 active lint rules |
| `references/starter.md` | The template to copy into the project root |

## Pitfalls

- **Hex colors must be quoted strings.** YAML chokes on unquoted `#` or truncates values oddly.
- **Negative dimensions need quotes.** `letterSpacing: -0.02em` parses as YAML flow — write `letterSpacing: "-0.02em"`.
- **Don't nest component variants.** `button-primary.hover` is wrong; `button-primary-hover` as a sibling key is right.
- **Token references resolve by dotted path.** `{colors.primary}` works; `{primary}` does not.
- **Section order is enforced.** Reorder prose to match the canonical list before saving.
- **Spec is alpha.** v0.3.0 — watch for breaking changes from the upstream repo.

## Related skills

| Skill | When |
|-------|------|
| `design-md` (Hermes) | Full spec authoring, linting, diffing, and export — the canonical reference skill that this jstack skill wraps |
| `popular-web-designs` | Visual inspiration and layout examples to inform the DESIGN.md |
| `claude-design` | Designing one-off HTML artifacts (prototypes, landing pages, decks) once the system is in place |
