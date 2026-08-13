# Authoring a Claude Design message (first-message OR edit)

Claude Design has **zero session memory**. Every message it acts on must carry the full context it
needs, because anything you leave out it invents. This file is how to write that message and the
package behind it. Shared by every use case that produces a prompt.

## The core principle — constrain the guardrails, free the composition

Claude Design's strongest capability is its creative mind. Over-prescribing placement ("asset X in slot
Y") wastes it. So **separate RULES from COMPOSITION** in every message:

- **Hard constraints (LOCK)** — label them "NOT creative choices." Brand tokens, honesty rules
  (decorative-only assets, real screenshots stay truthful), mandatory content changes, exact recipes
  (a tint hex + behavior), voice rules. These never bend.
- **Creative latitude (FREE)** — say it explicitly: "Treat placement, scale, cropping, layering, and any
  motion as YOUR creative call. The pairings below are suggestions, not mandates — override them freely
  if you find something stronger." Describe what each asset *depicts*; let CD decide where and how.

Pin only what would otherwise break brand or honesty. Invite ideas for everything else.

## The self-contained package (on disk, then uploaded into the project)

Create `<deliverable-dir>/<name>-claude-design-package/`. Upload all of it into the project so it is in
the agent's context, not just on disk:

- **`first-message.txt`** — the paste-in directive. Self-contained enough to act on alone, and it points
  CD at the reference docs. Carries:
  1. Brand reuse line, matching the use case: "use the `<name>` design system attached to this project"
     (existing) / "reuse the attached `tokens.css`" (you built tokens) / the aesthetic in words (generic).
  2. Who it is for (audience + tone) in 2-3 lines.
  3. Hard design rules — Jono's prefs verbatim: visual-first if asked, ruthlessly short, **no em dashes**,
     CTAs in his voice ("ask me", not "contact us"), any "do not restate the brief as a headline" rule.
  4. Every section top to bottom, with the **exact copy** and its visual treatment.
  5. The **asset legend** (see below) with the rules-vs-composition split.
  6. A line: "read the attached spec / plan and `context.md` for the full rationale and verbatim before
     building," naming the attached doc files explicitly.
- **The session's real spec / plan / implementation docs — uploaded VERBATIM** under their own filenames
  (e.g. `athar-package-onepager-spec.md`, `implementation-plan.md`). **Do not rewrite or re-curate them
  into a new `spec.md`** — re-curation silently drops detail CD then has to invent. Feed the exact
  artifact the session produced. This holds for **every** use case that has a spec or plan: building on
  an existing system AND generating a new design system. Only if the plan lives *only* in the chat (no
  file) do you write it out once as `plan.md`, quoting the decisions faithfully rather than paraphrasing.
- **`context.md`** — session-only WHY + verbatim **not already in an attached doc**: audience/buyer
  profile, the strategic frame, the reasoning behind each decision, findings (e.g. an ad audit), and
  load-bearing decisions **quoted verbatim**. Lets CD make faithful judgment calls in the gaps. Derive
  from the session; never fabricate. Skip it if the attached docs already carry the WHY.
- **`tokens.css`** — Claude-Design-adapted brand tokens (only when you are providing the brand).
- **`ref-*.<ext>`** — the REAL assets, each named for what it is (`ref-running-now-sands-1.jpg`).

## The asset legend (real vs placeholder — be honest)

- **REAL, attached** → name each file and what it depicts. Mark the honesty rule (decorative vs literal).
- **PLACEHOLDER** → anything CD cannot make: video/reel, real photography, real un-captured screenshots,
  unset numbers/prices. **Describe** these as elegant placeholder frames to leave clearly marked. Never
  fake them. The Claude Code finishing pass (or `/imgen` for images — see uc-assets.md) fills them.

## Edit-message shape (numbered, priority-ordered)

When the message edits an existing build, lead with what must change, stated against what is **actually
in the current build** (you `get_file`'d it — see uc-edit-build.md):

```
0) mandatory content change, stated surgically against the current DOM (name the exact section/elements)
1) exact recipe(s) — hex, behavior — labelled "NOT creative choices"
2) imagery: "you decide composition" + a hard-constraints sublist + asset legend + an OPTIONAL pairing
3) runtime fallback recipe if an asset is missing
   + voice rules echoed at the end (no em dashes, honesty, CTA voice)
```

This shape is a reference, not gospel — the invariant is: lock the few things that break brand/honesty,
free the rest, and never assume a prior edit message was applied (re-assert critical rules every time).

## Hand-back — upload the prompt, summarize in chat (never dump it)

Whenever the move is a paste message (a `first-message.txt` initial build, or an edit message), the prompt
goes **into the project as a file** — not into the Claude Code chat.

1. Write the prompt to the package dir (`first-message.txt`, or `edit-message-NN.txt` for a follow-up
   edit, numbered so successive edits don't collide).
2. `write_files` it into the project alongside its docs/assets, then `list_files` to confirm it landed.
3. In the Claude Code chat, **only summarize** what the prompt does — the change it makes, what it locks,
   what it frees, which assets it references, what stays placeholder. **Do not print the prompt body.**
4. Tell Jono: open the project (give the URL), open the prompt file, copy it, and paste it as the next
   turn in Claude Design. For `build` on an existing system, also remind him to attach the design system.

Why: the chat stays readable, the prompt lives where it's used, and Jono's only action is open → copy →
paste. The exception is a direct Claude-Code edit (mechanical change pushed via `write_files`) — there is
no paste message at all, so just report what you changed and that it's live in the project.
