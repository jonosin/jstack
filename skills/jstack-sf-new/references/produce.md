# Phase 5 — Produce (approved brief → stills/clips through the gates)

**Prompts-first rule:** nothing is generated until the brief holds the COMPLETE prompt set for every beat
(still + clip) and Jono has approved it. Engine + manual-vs-agent are NOT assumed here — they are decided
at the **Render Gate** below. The brief is the single source of truth; `tools/briefsheet.py` parses it
(`--json` feeds the dashboard; default emits the offline HTML export).

Precondition: an approved brief exists at `clients/<slug>/briefs/*-brief.md` with a standalone still
prompt + clip prompt for every beat (no `tbd`, no "as above").

## Launch the runsheet
```bash
curl -s -o /dev/null http://localhost:7777/ || (cd ~/builds/stayframe-qa && node server.js &)
open http://localhost:7777
```
Under **Reels** in the sidebar, Jono picks the reel. The dashboard re-parses the brief live, so any
brief edit shows on reload (restart `node server.js` only if `server.js` itself changed).

## Render Gate (per reel — ask BEFORE generating anything)
Prompts are straight and approved; now decide HOW they render. **Ask Jono two things once per reel** (he
can override any single beat):
1. **Manual or agent-generate?** — *manual* = Jono runs the prompts himself (stills on web relax /
   gemini.google.com; clips on his Gemini sub for Veo, or the web UI) and uploads results via the
   dashboard; *agent-generate* = Claude invokes **`/jstack-vidgen`**, the universal video-gen router
   (it enforces the universal rules — ask duration+resolution, show the exact prompt + the
   `video-prod-skills:<skill>` craft file used, no same-still dup-frame — and routes to the Topview
   backend today, `~/builds/topview-skill/scripts/video_gen.py`) for the engines that support it
   (Seedance / Kling). **Veo has no API wired → Veo is manual-only for now.**
2. **Engine?** — the matrix (`playbook/index.md §2`) proposes the default per beat (still → NB Pro;
   moving beat → Veo single-start; flat reframe → Kling O3 i2v; reference reel → Seedance). Jono confirms
   or overrides.

Record the confirmed choice in the brief frontmatter (`still_model` / `clip_model`) so dashboard labels +
`sf_lint` stay true. Only AFTER this gate does any generation start. Detail + lane split → `produce/manual-webui-workflow.md`.

## Per beat (Jono drives in the dashboard)
Per the Render Gate choice (manual or agent-generate): review the reference image (per-reel gate —
approve, or tell Claude to swap/add) → render the still → **build the keyframe pair** (flat micro-reframe
only, see below) → **GATE A** (still/keyframes approved) → render the clip → **GATE B** (clip approved) →
save to `<render_subdir>/stills/beat-N-still.png` ·
`<render_subdir>/beat-N-clip.mp4`. Every tick persists to `qa/reels/<reel_id>.json`
(`reel_id = <client>__<reel>`).

**Engines are per-reel, not hard-coded** — confirmed at the Render Gate, recorded in the brief frontmatter
(`still_model` / `clip_model`). The matrix defaults the gate proposes (full matrix + overrides → `playbook/index.md §2`):
- **still →** Nano Banana Pro (web relax, free; GPT Image 2 = manual alt)
- **any beat with a real camera move (DEFAULT) →** Veo 3.1 i2v, **single start frame, no end frame** —
  manual on gemini.google.com (Jono's Gemini sub, free). See `prompts/reel-prompt-system.md §single-start-frame`.
- **deliberately flat micro-reframe ONLY →** Kling O3 i2v fed a **cropped** first+end pair (keyframe step below)
- **visible-motion beat →** Kling O3 Reference-to-Video (9-field Kling director)
- **reference reel →** Seedance 2.0 (Topview "Standard", 720p) · **1080p+audio finals →** Seedance 1.5 Pro
- **drafts →** Seedance 1.0 Pro Fast (0.07 cr/s) — **never "Fast"** (= Seedance 2.0 Fast @ 1.0 cr/s)

### Keyframe pair (flat micro-reframe ONLY — when a deliberately flat reframe is the intent)
Most moving beats now go to single-start Veo (above) — it takes **only** the approved still, no keyframe
pair. Build a keyframe pair ONLY for a deliberately flat micro-reframe on Kling O3 i2v. Then: do **NOT**
generate the end frame from a prompt — image-edit models repaint/drift. Build **both** Kling keyframes by
**cropping ONE real still** with `tools/crop_reframe.py` — full method, per-move recipe, and crop params
in **`playbook/prompts/end-frame-method.md`**. (Kling O3 i2v *requires* a first+end pair anyway; the crop produces
exactly that.) Jono approves the pair at **GATE A** before the clip renders.

## Review each clip before combining (standing workflow)
The reel view shows each beat's generated still and clip **inline** — the clip in a `<video>` player
(served from the dashboard's `/render` endpoint) the moment the file lands in `renders/`. Jono watches
each scene and approves it at GATE B (or leaves clip feedback) **before anything is assembled**. Do not
stitch until every beat's clip is approved. Model labels on each block come from the brief frontmatter
(`still_model` / `clip_model`), so they read true to whatever generated them.

## Iterate (separate skill — don't fold it here)
Jono leaves per-beat feedback in the dashboard (ref swap/add · still/clip edit). He triggers
**`/jstack-sf-check`** to apply it: read `qa/reels/<reel_id>.json` → `feedback`, rewrite the brief
prompt preserving craft rules, clear the handled entry. That lean loop stays its own skill.

## Assemble
Per the brief's own edit spec: cut lengths, hard cuts / dissolves / fade, overlay copy rendered via
PIL + ffmpeg (never in-generation), music added at IG post time. Offline export for a no-server
machine: `python3 ~/ventures/stayframe/tools/briefsheet.py <brief.md>` → standalone HTML (decisions in
localStorage; the dashboard is the durable home).

## Promote what worked (after the reel passes — do not skip)
A reel that cleared every GATE B taught the system something — a prompt pattern, a camera method, an
engine choice that beat its baseline. That lesson is stranded in this one brief until it's written to
canon. Tell Jono to run **`/jstack-sf-learn`**: it diffs this brief's method against `playbook/`,
surfaces what's new, and on confirm writes the rule into the governing playbook + appends
`playbook/DECISIONS.md`. (Canon is the home — it does not copy the method to the brain.) Skipping this
is how the *next* resort re-invents what this one already proved.
