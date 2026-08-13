# Use case: create a NEW design system in Claude Design

Jono wants a fresh design system designed *by* Claude Design — not a deliverable built on an existing
one. The session creates the project and hands CD a prompt to **design the system itself** (the brand
foundation: type scale, color, spacing, core components), which Jono can then attach to future builds.

Read first: `designsync-mechanics.md`, `prompt-authoring.md`.

## When this applies

- "create a design system for X", "set up a new design system in Claude Design", "have Claude Design
  design a brand system" — and there is **no existing published system** to reuse, and **no real
  component-library repo** to convert (if there IS a component repo, that is `/design-sync`'s converter,
  not this).

## Steps

1. **Capture the brand intent** from the session: the brand's personality, any locked tokens (fonts,
   colors, spacing) Jono has already decided, reference brands/aesthetics, and the components the system
   must define. Quote his decisions; mark what is locked vs open for CD to propose.
2. **Create the project.** `list_projects` to avoid a name collision → `create_project(name)` → record
   `projectId`.
3. **Feed any spec/plan verbatim.** If the session produced a design-system spec, brand brief, or
   implementation plan, **upload that exact document under its own filename** — do not re-curate it into a
   new file (same fidelity rule as uc-build-existing: nothing gets lost in a paraphrase). (`prompt-authoring.md`.)
4. **Stage the package** (`prompt-authoring.md`): `first-message.txt` is a **design-system-generation
   directive** — "design a cohesive design system with these locked tokens, propose the rest." Lock only
   what Jono fixed; **free the composition** (let CD propose scale, states, component variants). Add the
   verbatim spec/plan from step 3, `context.md` for any session-only brand WHY, and `tokens.css` only if
   Jono has seed tokens; otherwise let CD generate them.
5. **Hand back** (`prompt-authoring.md` → hand-back): give the project URL and **summarize** the
   generation directive — do not print it; it is in the project for Jono to copy and paste. CD designs the
   system; once happy it is his to **attach** to future builds (that becomes uc-build-existing).
6. **Record** `.claude-design.json` next to wherever the brand lives.

## Notes

- This produces a *system*, not a page. Do not pack page sections or a deliverable arc here.
- The output of this use case is the **input** to uc-build-existing: once the system exists, future builds
  attach it rather than re-supplying tokens.
- Heavy converter path (system FROM a real component repo) → defer to `/design-sync`.
