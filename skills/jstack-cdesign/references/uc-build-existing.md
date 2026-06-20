# Use case: build a deliverable on an EXISTING design system

Jono wants to build something (a page, screens, a component) reusing a design system that already
exists. He attaches the design system in Claude Design himself; the skill's job is to **hand him the
prompt of what to build and the self-contained detail doc**, fed with the exact spec / implementation
plan the session produced.

Read first: `designsync-mechanics.md`, `prompt-authoring.md`.

## When this applies

- "build X using the Facet design system", "make a page on my existing design system", "design this on
  brand `<name>`" — a published design system already exists.

## Steps

1. **Ask which design system.** Show `DesignSync(list_projects)` so Jono sees what he has, and **ask him
   to pick**. Assume Jono will attach/feed that design system in Claude Design himself (DesignSync has no
   attach method — it is a UI step he does). Your job is to **name it** in the first-message and stage
   the build context. Record the chosen system's name.
2. **Capture the deliverable** from the session: what it is + who it is for, every section with the exact
   copy and treatment, the do's/don'ts, and the assets split real-vs-placeholder.
3. **Feed the real artifacts verbatim, do not re-curate.** If the session produced a spec or
   implementation plan, **upload that exact document under its own filename** — do not rewrite it into a
   new `spec.md` (re-curation drops detail CD then invents). Add `context.md` only for session-only WHY
   not already in those docs. (`prompt-authoring.md` → package.)
4. **Stage the package** (`prompt-authoring.md`). The brand line is "use the `<name>` design system
   attached to this project." Do **not** upload `tokens.css` — Jono attaches the published system. Upload
   `first-message.txt`, the verbatim spec/plan doc(s), `context.md` (if any), and the `ref-*` assets.
5. **Set up the project.** `list_projects` → ask **fresh dedicated project (recommended)** or reuse. Fresh:
   `create_project(name)`. Reuse: `get_project` (confirm design-system type) + `list_files` + warn before
   overwrite. Then `finalize_plan` (writes incl. the docs + assets, `deletes:[]`) → `write_files` →
   `list_files` to verify. Record `.claude-design.json`.
6. **Hand back** (`prompt-authoring.md` → hand-back): give the project URL and **summarize the
   first-message** — do not print it; it is in the project for Jono to copy. **Remind him to attach the
   `<name>` design system** before pasting. Note what stays placeholder and that Claude Code finishes it.

## Notes

- The differentiator vs uc-new-design-system: here the brand is settled and attached; the work is the
  *deliverable*. Pack the section arc and copy, not a token system.
- If assets need generating first (e.g. decorative images), run uc-assets.md before finalizing the package.
