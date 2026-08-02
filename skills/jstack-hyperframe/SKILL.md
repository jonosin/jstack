---
name: jstack-hyperframe
description: >
  Thin router to HeyGen HyperFrames — the HTML-native motion-graphics engine (write HTML,
  render deterministic MP4 locally via headless Chrome + FFmpeg). Use when the user says
  "hyperframe", "hyperframes", "animated overlay", "motion graphics", "html to video",
  "animated caption", "animated hook text", "kinetic captions", "kinetic titles",
  "end card", "lower third", or wants to author/render an HTML composition to MP4 or
  browse the HyperFrames block catalog. NOT for generative video (that is /jstack-vidgen)
  and NOT for StayFrame static text overlays (that stays on /jstack-sf-caption).
---

# jstack-hyperframe — router to HeyGen HyperFrames

HyperFrames (Apache-2.0, github.com/heygen-com/hyperframes) turns HTML/CSS/JS compositions into
deterministic MP4s: the renderer seeks each frame in headless Chrome and encodes with FFmpeg.
This skill is a THIN router — all real knowledge lives upstream in the cloned repo and its own
20 agent skills; never duplicate upstream docs here.

## Local paths

Resolution: `HYPERFRAMES_HOME` env var → `~/.jstack/config.env` → default below.

| What | Where |
|---|---|
| Cloned repo (canonical local copy) | `~/.jstack/vendor/hyperframes` |
| Upstream router skill (READ FIRST for any make-me-a-video request) | `~/.jstack/vendor/hyperframes/skills/hyperframes/SKILL.md` |
| Its 20 agent skills (also installed into `~/.claude/skills/` + `~/.agents/skills/` by `hyperframes init`) | `~/.jstack/vendor/hyperframes/skills/` |
| Block/component registry (70+ blocks: lower-thirds `lt-*`, code-*, logo-outro, glitch, data-chart…) | `~/.jstack/vendor/hyperframes/registry/{blocks,components}` |
| Docs source (Quickstart, concepts, reference, catalog) | `~/.jstack/vendor/hyperframes/docs/` |
| Online: docs + block catalog | hyperframes.heygen.com (Quickstart/Docs/Catalog), hyperframes.dev (playground + design templates) |

## Install / health check

Requirements: Node 22+ and FFmpeg on PATH (verified working on this machine, CLI v0.7.48).

```bash
npx --yes hyperframes doctor          # environment health check
npx --yes hyperframes init my-video   # scaffold a project (also installs/refreshes its agent skills)
cd my-video && npm run render         # → renders/*.mp4
```

`init` scaffolds `index.html` + `hyperframes.json` and pins the CLI version in `package.json`
scripts (`dev`/`check`/`render`/`publish`). Refresh the clone with
`git -C ~/.jstack/vendor/hyperframes pull`.

## Dispatch table

Route the intent, then OPEN/RUN the upstream target — do not improvise a workflow.

| Intent | Go to |
|---|---|
| Any "make me a video/animation" request (entry point) | Read the `/hyperframes` router skill: `~/.jstack/vendor/hyperframes/skills/hyperframes/SKILL.md` — it picks the workflow |
| Animated hook text / kinetic titles / stat hit / logo sting / end card / lower-third (short, unnarrated, design-led) | `/motion-graphics` workflow: `skills/motion-graphics/` in the clone; lower-third blocks = registry `lt-*`, end card = `logo-outro` |
| Kinetic captions / subtitles on an existing talking-head video | `/embedded-captions` workflow: `skills/embedded-captions/` (footage untouched, captions rendered over it) |
| Author or edit an HTML→MP4 composition (the `data-*` timing contract, clips, tracks) | `/hyperframes-core` then `/hyperframes-animation`: `skills/hyperframes-core/`, `skills/hyperframes-animation/` |
| Browse / install blocks and components | Registry dirs `registry/{blocks,components}` or hyperframes.heygen.com/catalog; install + wire via `/hyperframes-registry` and `npx hyperframes add [block]` |
| Render / preview / lint / validate a composition | `/hyperframes-cli`: `npx hyperframes preview`, `npx hyperframes lint && npx hyperframes validate`, `npx hyperframes render`, `npx hyperframes doctor` |
| BGM / SFX / voiceover / icons / background removal for a composition | `/media-use`: `skills/media-use/` |
| Deck / slideshow, product promo, PR-to-video, music-synced, website tour, Remotion port | The matching workflow skill in `skills/` (see the `/hyperframes` router's cheat-sheet) |

## When NOT to use (StayFrame red line)

StayFrame's feed-aesthetic north star (ADR 0002, editorial-minimal — "would this sit unnoticed in
the Aman/Soneva grid?") makes heavy motion-graphics styles OFF-BRAND: Hormozi-style kinetic
captions, glitch/VFX blocks, news tickers, liquid-glass widgets. For StayFrame reels use
HyperFrames only for SUBTLE minimal overlays, and:

- **Static text overlays stay on the existing lane** — headless-Chrome + ffmpeg via
  `/jstack-sf-caption`. Do not migrate that to HyperFrames.
- **Generative video (i2v/t2v) is never HyperFrames** — that is `/jstack-vidgen`.

## Gotchas

- `hyperframes init` has no `--yes` flag (errors on unknown flags); it is already non-interactive.
- `init` side-effect: installs/refreshes HyperFrames' own core skills into `~/.claude/skills/` and
  `~/.agents/skills/` — expected, keeps the upstream router current.
- Installing skills standalone: `npx skills add heygen-com/hyperframes --full-depth` — keep
  `--full-depth` or you get a stale skills.sh registry blob that lags `main`.
- Telemetry is on by default; disable with `hyperframes telemetry disable`.
- Render output lands in `renders/[project]_[timestamp].mp4` inside the project dir.

## Next skills

| Next | When |
|---|---|
| `/jstack-vidgen` | The composition needs generated footage (i2v/t2v clips) as source media — video generation always routes there, never direct to a backend. |
| `/jstack-sf-caption` | A StayFrame reel needs plain static text overlays — that lane stays on headless-Chrome + ffmpeg, not HyperFrames. |
| `/jstack-sf-trim-stitch` | A rendered HyperFrames overlay/end card needs assembling into a StayFrame reel. |
