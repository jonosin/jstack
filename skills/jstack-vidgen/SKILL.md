---
name: jstack-vidgen
description: "Universal video-generation router: invoke every time we generate a video. Enforces ask-duration+resolution, show-the-exact-prompt-and-craft-skill-used, no dup-frame; routes prompt craft to the video-prod-skills plugin and generation to the available video backend — Topview (Vidu/Seedance/Kling) or Veo 3.1 on Vertex AI (GCP credits via ADC)."
---

# jstack-vidgen — universal video-generation router

**Invoke this skill EVERY TIME we generate a video.** It is the single, stable front
door for all video generation. Two halves, both mandatory:

1. **Prompt craft** — engineer the prompt with the right skill in the **`video-prod-skills`**
   plugin (the renamed `creative-production-skills` plugin — always use the new name
   `video-prod-skills:<skill>`).
2. **Generation backend** — submit to whatever video backend fits. Two today: **Topview**
   (via `topview-skill`) for Vidu/Seedance/Kling, and **Veo 3.1 on Vertex AI** for Veo /
   GCP-credit jobs. This skill is backend-agnostic on purpose: backends are swappable behind
   this front door; the universal rules below never change. See **Backends** below.

---

## Operating principle: RUN-FIRST. Assume the tools work.

Do **NOT** read `scripts/*.py` source or re-derive the SDK call shape before running — just run
the documented command. Each backend's reference doc opens with a copy-paste recipe; that is all
you need to act.

**Common case ("generate a Veo clip"):** go straight to the ▶ recipe at the top of
`references/veo-vertex-backend.md` and run it (validate with `--dry-run` first). You do not need
to read the rest of that doc. For Topview, same idea — the i2v flow is at the top of
`references/topview-backend.md`.

**Only if a run FAILS** do you diagnose: read the actual error, fix the root cause in the
script / reference / SKILL, re-run — and then **update this skill + the script + the reference so
the next agent doesn't hit it.** The skill is a living contract; every real failure should leave
it more correct. (The reference docs keep their deeper SDK/theory material below a "read only if a
run fails" marker for exactly this.)

---

## UNIVERSAL RULES (MANDATORY — every generation, every backend, no exceptions)

1. **ASK for `duration` AND `resolution` before generating.** Never let them fall to
   silent defaults. Also confirm **model** and **aspect ratio** in the same breath. If
   the user has not stated all four, ask before spending anything.
2. **SHOW the exact prompt + the craft skill used — in your VISIBLE RESPONSE TEXT.** Per
   video, surface to the user: (a) the EXACT, verbatim prompt string sent, and (b) the exact
   `video-prod-skills:<skill>` (and any venture canon file, e.g. `reel-prompt-system.md`) you
   read to engineer it. You do not have to stop generating — but both MUST appear where the
   human reads them.
   - **WHERE:** the prompt MUST be in the **prose you write to the human in chat**. Putting it
     ONLY inside a tool call, a `--dry-run` JSON envelope, script stdout, or any
     escaped/encoded payload does **NOT** satisfy this rule — the human cannot read those.
   - **HOW:** render it as clean, readable text — **italicized and wrapped in quotation
     marks** (a blockquote is ideal for a multi-line prompt). No JSON escaping, no literal
     `\n`, no `—`-as-escape. Name the craft source in the prose alongside it.
   - **Format to copy** (craft source: `video-prod-skills:cinematic-motion-language`):
     > *"&lt;the exact prompt text, verbatim, italicized, in quotation marks&gt;"*
3. **Dup first+end frame is RETIRED.** Never pass the same still as BOTH first and end
   frame — it yields micro-motion only ("never works"). For a single still, use instead:
   - a single-image i2v model — **Vidu Q3 Pro / Seedance 1.0 Pro / Sora 2 Pro**, or
   - a single start-frame model — **Veo 3.1**, or
   - **Kling Reference-to-Video (R2V)**.
4. **Estimate cost before submit; confirm before the FIRST submission.** For the Topview
   backend, defer to the topview-skill's own Pre-Execution Checklist for the exact guard flow.

---

## Pre-flight validation (MANDATORY — before any backend call)

1. **Argument validation against the capability table.** Check the requested `model` +
   `duration` + `resolution` (+ `aspect_ratio` where applicable) against
   `references/capability-table.md`. If the combination is not in the allowed set for that
   engine, **fail fast**: tell the user the allowed values from the table and ask them to pick
   one — never let a raw backend/argparse error (`INVALID_ARGUMENT`, `ret:1201`, out-of-set
   resolution, etc.) be the first thing the human sees.
2. **Prompt-quality gate.** The crafted prompt MUST satisfy the "Minimum structure checklist" in
   the matching guide under `references/prompt-guides/` (shot, camera, motion, duration all
   present) before it is submitted. If a required element is missing, fix the prompt first —
   do not submit a prompt that fails its own guide's checklist.

Both checks happen BEFORE Universal Rule 4 (cost estimate + confirm).

---

## Prompt-format routing (which `video-prod-skills` skill for which engine)

| Engine / format | Prompt shape | Craft skill(s) |
|---|---|---|
| **Kling** (O3 / V3) | 9-field director formula | `video-prod-skills:kling-3-prompt-director` (+ `video-prod-skills:cinematic-motion-language` for camera/motion) |
| **Veo 3.1** / **Vidu Q3 Pro** (single-image i2v) | single-start motion block | `video-prod-skills:cinematic-motion-language` |
| **Seedance** (Topview "Standard" / 2.0) | six-block | `video-prod-skills:seedance-director` (or `video-prod-skills:seedance-prompting-skills-for-cinematic-films`) |
| **Planning before spend** | shot list / storyboard | `video-prod-skills:b-roll-shot-planner` / `video-prod-skills:storyboard-generation` |

Read the chosen craft skill, build the prompt to its formula, then surface both per
Universal Rule 2.

**Baked prompt-craft references (length/detail calibration + verbatim gold examples):**
- Veo 3.1 → `references/prompt-guides/veo-3.1-prompt-guide.md` (official five-part formula,
  duration set {4,6,8}s, first-and-last-frame workflow for hard transitions, audio rules).
- Seedance 2.0 → `references/prompt-guides/seedance-prompt-guide.md` (core formula, NL vs JSON
  shapes, omni-reference syntax). Distilled from the canonical Google + top community sources.

---

## Backends

Two backends today, each routing to its own reference doc. The Universal Rules above apply to
**both, unchanged**; each backend owns its mechanical guards.

| Backend | Engines / when | Billing | Reference |
|---|---|---|---|
| **Topview** | Vidu Q3 Pro, Seedance, Kling — non-Google engines | Topview credits | `references/topview-backend.md` |
| **Veo on Vertex** | Google Veo 3.1 / 3.1-Fast (i2v, t2v) | GCP credits via ADC | `references/veo-vertex-backend.md` |

**Backend-selection rule (pick at generation time):** route to **Topview** for Vidu / Seedance /
Kling; route to **Veo-on-Vertex** when the engine is **Veo 3.1** OR the user wants to spend **GCP
credits** instead of Topview credits. Once the backend is chosen, read its reference doc for the
exact call shapes and guards.

**Adding a backend later:** backends slot in as rows in this table, each with a reference doc in
`references/` (Veo is the proof the pattern works). The Universal Rules and prompt-craft routing
stay unchanged.

---

## Relationship to venture pipelines

Venture-specific pipelines layer their own canon on top of this router — e.g. StayFrame's
reel pipeline (via `jstack-sf`) governs prompts with
`~/ventures/stayframe/playbook/prompts/reel-prompt-system.md`. When a venture pipeline is
in play, follow its canon for prompt construction, but the **UNIVERSAL RULES here still
apply to every generation** (ask duration+resolution+model+aspect, show the exact prompt +
craft source, no dup first/end frame, estimate+confirm before first submit).

## Next skills

| Next | When |
|---|---|
| `/jstack-sf-check` | The clip is for a StayFrame reel — review/iterate at GATE B against saved dashboard feedback. |
| `/jstack-sf-new` | Continuing the StayFrame pipeline for a resort after generating the clip. |

Generic standalone video generation has no required next step — control returns to whatever venture skill called this router.
