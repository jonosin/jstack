# Seedance 2.0 prompt guide (baked from canonical sources)

> What a good Seedance 2.0 prompt looks like — distilled from the top community skills/repos,
> with real example prompts kept verbatim. Companion to the in-plugin craft skills
> `video-prod-skills:seedance-director` and `cinema-worldbuilder-pro-2-0`.

**Sources (fetched 2026-06-25):**
- songguoxs/seedance-prompt-skill (2009★) — https://github.com/songguoxs/seedance-prompt-skill
- songguoxs/awesome-video-prompts (553★, veo3/seedance/kling examples) — https://github.com/songguoxs/awesome-video-prompts
- rich5000/seedance-prompt-guide (EN/中文 engineering guide) — https://github.com/rich5000/seedance-prompt-guide
- HuyLe82US/awesome-seedance-prompts (template vault)

---

## Platform params (Seedance 2.0 / 即梦; also Topview "Standard" = Seedance 2.0)
- Clip length typically 4–15s; native audio supported; multi-image reference (omni) up to ~9 imgs.
- Two entry modes:
  - **First/last-frame mode** (首尾帧) — drive with a start (and optional end) frame.
  - **Omni / all-reference mode** (全能参考) — supply real photos as `@图1 / <<<Name>>>`
    references for character/scene/object consistency.

## Minimum structure checklist (prompt-quality gate)
Before submitting, confirm the prompt hits all four — a prompt missing any of these is not ready:
- [ ] **Shot** — material/role spec pins WHO/WHAT (and which reference image, if omni mode)
- [ ] **Camera** — camera language named (镜头语言: push-in, orbit, close-up, etc.)
- [ ] **Motion** — action/plot described concretely (动作/剧情), not just a static scene
- [ ] **Duration** — the requested duration is within the engine's allowed set (check `list-models`, typically 4–15s) and matches what was asked/confirmed

## Core formula
```
[Material/role spec] + [Action/plot] + [Camera language] + [Atmosphere/audio]
素材角色指定 + 动作/剧情描述 + 镜头语言 + 氛围/音效指令
```
Order matters: pin WHO/WHAT (and which reference image) first, then WHAT HAPPENS, then HOW IT'S
SHOT, then MOOD + SOUND. Seedance follows references tightly when you name them explicitly.

## Two prompt shapes Seedance accepts
1. **Natural-language six-block** (Seedance "Standard"/2.0) — flowing directive prose covering the
   four formula parts. Best for most shots.
2. **JSON-structured** (`shot` / `subject` / `scene` blocks) — maximum control over lens,
   frame_rate, camera_movement, wardrobe, props, location. Used heavily in the awesome-video-prompts
   library for ad/product work.

## Real example — natural language (rich5000, omni reference)
> 参考@图1的男人形象，他在@图2的走廊中，
> 男人下班后疲惫的走在走廊，脚步变缓，最后停在家门口，
> 脸部特写镜头，镜头前推，
> 背景音效为走路声，整体氛围孤独疲惫

Translation: *Reference the man from @img1, in the corridor from @img2; after work he walks the
corridor wearily, steps slowing, finally stops at his door; face close-up, camera pushes in;
background SFX of footsteps, overall mood lonely and tired.* — Note how it hits all four formula
parts in four short lines.

## Real example — JSON structured (songguoxs/awesome-video-prompts, case 50)
```json
{
  "shot": {
    "composition": "wide establishing shots transitioning to medium orbit and macro close-up",
    "lens": "24mm for wide interior, 50mm for orbit, 90mm macro for device",
    "frame_rate": "30fps standard with subtle ramping during gesture moments",
    "camera_movement": "smooth orbital tracking around subject, gentle push-in for close-up"
  },
  "subject": {
    "description": "androgynous individual interacting with futuristic home interface",
    "wardrobe": "monochromatic high-tech loungewear with subtle metallic textures",
    "props": "transparent ripple-reactive interfaces, glass-like control device"
  },
  "scene": {
    "location": "suspended apartment overlooking neon cityscape"
  }
}
```

## Calibration: length/detail
- Natural-language Seedance prompts are **tight** — the gold examples are 4–8 short lines hitting
  the four formula parts. JSON prompts trade brevity for explicit per-field control.
- Like Veo: precision (named refs, concrete camera/lens, explicit SFX) beats verbosity.
- Always end with the atmosphere + audio instruction; Seedance generates sound and will invent it
  if unspecified.
