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
Review the reference image (per-reel gate — approve, or tell Claude to swap/add) → **copy image** into
NB Pro, **copy NB prompt** → generate 9:16 still → **GATE A** (still approved) → upload the approved
still to Veo, **copy Veo prompt** → 9:16 / 8s clip → **GATE B** (clip approved) → save to
`<render_subdir>/beat-N-still.png` · `beat-N-clip.mp4`. Every tick persists to
`qa/reels/<reel_id>.json` (`reel_id = <client>__<reel>`).

## Iterate (separate skill — don't fold it here)
Jono leaves per-beat feedback in the dashboard (ref swap/add · still/clip edit). He triggers
**`/jstack-sf-check`** to apply it: read `qa/reels/<reel_id>.json` → `feedback`, rewrite the brief
prompt preserving craft rules, clear the handled entry. That lean loop stays its own skill.

## Assemble
Per the brief's own edit spec: cut lengths, hard cuts / dissolves / fade, overlay copy rendered via
PIL + ffmpeg (never in-generation), music added at IG post time. Offline export for a no-server
machine: `python3 ~/ventures/stayframe/tools/briefsheet.py <brief.md>` → standalone HTML (decisions in
localStorage; the dashboard is the durable home).
