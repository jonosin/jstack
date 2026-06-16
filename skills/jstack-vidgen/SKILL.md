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

## UNIVERSAL RULES (MANDATORY — every generation, every backend, no exceptions)

1. **ASK for `duration` AND `resolution` before generating.** Never let them fall to
   silent defaults. Also confirm **model** and **aspect ratio** in the same breath. If
   the user has not stated all four, ask before spending anything.
2. **SHOW the exact prompt + the craft skill used.** During generation, surface to the
   user, per video: (a) the EXACT, verbatim prompt string sent, and (b) the exact
   `video-prod-skills:<skill>` file(s) you read to engineer it. You do not have to stop
   generating — but the prompt and its craft source must be visible to the user.
3. **Dup first+end frame is RETIRED.** Never pass the same still as BOTH first and end
   frame — it yields micro-motion only ("never works"). For a single still, use instead:
   - a single-image i2v model — **Vidu Q3 Pro / Seedance 1.0 Pro / Sora 2 Pro**, or
   - a single start-frame model — **Veo 3.1**, or
   - **Kling Reference-to-Video (R2V)**.
4. **Estimate cost before submit; confirm before the FIRST submission.** For the Topview
   backend, defer to the topview-skill's own Pre-Execution Checklist for the exact guard flow.

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
