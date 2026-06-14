# Phase 5 — Produce (approved brief → stills/clips through the gates)

Precondition: an approved brief exists at `clients/<slug>/briefs/*-brief.md`. The brief is the single
source of truth; `tools/briefsheet.py` parses it (`--json` feeds the dashboard; default emits the
offline HTML export).

## Launch the runsheet
```bash
curl -s -o /dev/null http://localhost:7777/ || (cd ~/builds/stayframe-qa && node server.js &)
open http://localhost:7777
```
Under **Reels** in the sidebar, Jono picks the reel. The dashboard re-parses the brief live, so any
brief edit shows on reload (restart `node server.js` only if `server.js` itself changed).

## Per beat (Jono drives in the dashboard)
Review the reference image (per-reel gate — approve, or tell Claude to swap/add) → generate the still
→ **build the keyframe pair** (subtle moves only, see below) → **GATE A** (still/keyframes approved) →
generate the clip → **GATE B** (clip approved) → save to `<render_subdir>/stills/beat-N-still.png` ·
`<render_subdir>/beat-N-clip.mp4`. Every tick persists to `qa/reels/<reel_id>.json`
(`reel_id = <client>__<reel>`).

**Engines are per-reel, not hard-coded.** Read the brief frontmatter: `still_model` for the still,
`clip_model` for the clip. Defaults (full matrix + overrides → `playbook/index.md`):
- **still →** Nano Banana Pro (web relax, free; GPT Image 2 = manual alt)
- **subtle move →** Kling O3 i2v fed a **cropped** first+end pair (see keyframe step)
- **motion beat →** Kling O3 Reference-to-Video (9-field Kling director)
- **reference reel →** Seedance 2.0 (Topview "Standard", 720p) · **1080p+audio finals →** Seedance 1.5 Pro
- **drafts →** Seedance 1.0 Pro Fast (0.07 cr/s) — **never "Fast"** (= Seedance 2.0 Fast @ 1.0 cr/s)

### Keyframe pair (subtle camera moves — push-in / zoom / in-frame pan / tilt)
Do **NOT** generate the end frame from a prompt — image-edit models repaint/drift. Build **both**
Kling keyframes by **cropping ONE real still** with `tools/crop_reframe.py` — full method, per-move
recipe, and crop params in **`playbook/end-frame-method.md`**. (Kling O3 i2v *requires* a first+end
pair anyway; the crop produces exactly that.) Jono approves the pair at **GATE A** before the clip
renders. The worded `beat-N` CLIP prompt is unaffected — it still drives Kling's motion.

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
