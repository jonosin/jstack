---
name: jstack-cdesign
description: "Two-way bridge between a Claude Code session and Claude Design (claude.ai/design). Use when Jono says /jstack-cdesign (optionally with a mode arg: new-system | build | edit | assets), 'hand this to Claude Design', 'set up Claude design for this', 'build a design system in Claude Design', 'build this on my <name> design system', 'edit the Claude Design build', 'pull the design back', 'push this edit to the design', or 'feed/generate assets for Claude Design'. Routes by use case: create a new design system, build a deliverable on an existing one, edit an existing build with session context, or generate assets (jstack-imgen/vidgen) and feed them in. Reads from and writes to the project via the DesignSync MCP connector, so Claude Code can round-trip edits itself. Brain capture stays separate (/jstack-savetobrain)."
---

# jstack-cdesign

Bridge a Claude Code session to **Claude Design**, which has **zero context** on this session. Claude
Design only ever sees (a) the design system / project you point it at and (b) the files + messages in
that design conversation. It cannot read this chat, your local files, the brain, or generate real media.

**You are the only agent that holds the session.** Whatever you do not put into the project, Claude
Design invents. This skill's job is to move the right context and assets across the bridge — and, now
that the `DesignSync` connector reads *and* writes, to **round-trip edits directly** instead of only
handing Jono a paste prompt.

## Invocation — `/jstack-cdesign [mode]`

The optional first arg picks the use case; with no arg, infer from the session and ask if unsure.

| Arg | Use case | Load |
|-----|----------|------|
| `new-system` (`system`) | Have Claude Design **design a new design system** (no existing one, no component repo to convert) | `references/uc-new-design-system.md` |
| `build` | **Build a deliverable on an existing design system** (Jono attaches it; you supply the build + the raw spec/plan) | `references/uc-build-existing.md` |
| `edit` | **Edit an existing Claude Design build** where the change needs session context | `references/uc-edit-build.md` |
| `assets` | **Generate assets** (`/jstack-imgen` images, `/jstack-vidgen` clips) and feed them into a CD design | `references/uc-assets.md` |

All four assume the two shared references — read them once; every use case rides on them:
- `references/designsync-mechanics.md` — read/write/round-trip transport, auth, verify, record, gotchas.
- `references/prompt-authoring.md` — the self-contained package, the asset legend, the hand-back rule, and
  the core **constrain-the-guardrails / free-the-composition** principle for every prompt and edit message.

**`assets` is compositional, not a sibling.** It is a *sub-step* that feeds `build`/`edit`, not a
peer deliverable. Route by the request's **primary deliverable**:
- The task is *only* to generate media and feed it into a design that already exists → **`assets`**
  (e.g. "generate textures and put them in the build").
- The request also **builds or edits a deliverable** ("build the page *using* generated images",
  "remake the hero *with* new shots") → route to **`build`/`edit` as primary** and run `assets` as the
  pre-step that produces the `ref-*` files, then fold them into that use case's package (per
  `uc-assets.md` → "hand off or edit"). Do **not** label the whole job `assets`.

When the mode is ambiguous, ask Jono one short question rather than guessing — a wrong package or a
misdirected edit costs a whole Claude Design round.

## Two communication modes (pick per change)

- **Claude Code edits directly** — mechanical / surgical / code-level changes (copy fixes, asset swaps,
  a footer change, wiring, fills). `get_file` → edit a local mirror → `write_files` → verify. No human
  paste. This is the round-trip and the common case after a build exists.
- **Hand Claude Design a message** — generative / from-scratch / heavy creative composition (initial
  build, design-system generation, "lay these assets out beautifully"). Author a self-contained message
  and **upload it into the project as a file**; Jono opens Claude Design and pastes it as the next turn.

In both modes, mechanics live in `designsync-mechanics.md`. The `edit` use case offers both and lets Jono
(or the nature of the change) decide which.

## Preconditions

- Load the connector: `ToolSearch(query: "select:DesignSync")`. On any auth error, relay its guidance —
  `/design-login` (API-key/token sessions) or `/login` (Claude subscription) — then retry once. No loops.
- `create_project`, `finalize_plan`, and the writes raise their own permission prompts. Explain each in
  plain language before it fires.
- This skill does **not** write to the second brain. Durable knowledge is a separate `/jstack-savetobrain`.

## Hard rules

- Claude Design has no session memory: everything it needs goes into the project + the message.
- **`finalize_plan` ALWAYS takes a `deletes` array — pass `deletes: []` when nothing is deleted.**
  Omitting it is a known recurring validation rejection (`designsync-mechanics.md` → write methods).
  Never call `finalize_plan` without the field, even on a plain "add these files" write.
- **Never paste a full CD prompt or edit message into the Claude Code chat.** Upload it into the project
  as a file and, in chat, **summarize what it changes** — Jono opens Claude Design and copies it from the
  project. (`prompt-authoring.md` → hand-back)
- **Feed real documents, do not re-curate them.** Upload the session's actual spec / plan / implementation
  docs into the package verbatim rather than rewriting them into a new file — re-curation loses fidelity.
  This applies to **every** use case that has a spec or plan (build AND new-system). (`prompt-authoring.md`)
- **Handoff-package completeness.** Whatever gets pushed to Claude Design MUST include, as its own
  section or file: (1) the full spec/plan verbatim, (2) every decision agreed this session stated
  verbatim (not paraphrased), (3) any prior-round feedback already given on this build (so CD doesn't
  re-litigate a settled note). Push all of it into the project yourself via `write_files` — do not ask
  Jono to relay context by hand. His only unavoidable manual step is pasting the message into CD's chat
  (DesignSync cannot drive CD's generative agent — that is an architecture limit, not a shortcut you get
  to skip).
- **Constrain the guardrails, free the composition** — lock only brand/honesty/mandatory changes; let CD
  own placement, scale, layering, motion. (`prompt-authoring.md`)
- **Editing a live build: `get_file` first, diff intent vs reality, re-assert critical rules** — never
  assume a prior edit message was applied. (`uc-edit-build.md`)
- Never fabricate assets. Mark real vs placeholder; describe placeholders, generate real ones via
  `/jstack-imgen` / `/jstack-vidgen` (`uc-assets.md`), never fake them.
- Use sandbox-safe tokens (web-font CDN `@import`, not bundler `@fontsource/*`).
- Keep a local mirror of any build you edit, so the finishing pass / deploy runs against the same bytes.
- Record `.claude-design.json` next to the deliverable so a re-run targets the same project.
- The heavy component-library converter is `/design-sync`'s job, not this skill's.
- **Local preview, never `file://`.** When visually verifying any local HTML artifact (a build mirror
  before pushing, a finishing-pass check), `file://` URLs are blocked in the sandbox. Serve the
  artifact's directory with `python3 -m http.server <port>` and navigate to `http://localhost:<port>/…`;
  kill the server after capture. Write screenshots only inside the session's allowed scratch directory
  (shared rule with `jstack-html`).

## Next skills

| Next | When |
|------|------|
| `/design-sync` | Building a design system FROM a real component-library repo (Storybook / `dist` / per-component cards) — that converter flow, not this skill's plain uploads. |
| `/jstack-imgen` | A use case needs generated images/textures/sprites to feed into the CD design (`uc-assets.md`). |
| `/jstack-vidgen` | The deliverable needs a generated video/clip (e.g. a reel) for an asset or the finishing pass. |
| `frontend-design` | Jono brings the Claude Design output back to Claude Code to finish it — inject real reel/photos, fill numbers, deploy (e.g. Vercel). |
| `/jstack-savetobrain` | The session also produced durable decisions worth preserving in the brain (separate from this handoff). |
