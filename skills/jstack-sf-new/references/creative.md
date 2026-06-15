# Phase 4 — Creative (pick a reel to clone → replication brief)

Mode: **auto-mine + draft, then Jono approves** (his choice). Discover an outlier reel, deconstruct
it, draft the brief — then surface the pick + brief for a yes before producing. Full method:
`~/ventures/stayframe/playbook/reel-deconstruction.md` and `reel-prompt-system.md`. Engine choice
(`still_model`/`clip_model`) + the higgsfield reference map → `~/ventures/stayframe/playbook/index.md`.

## 1. Mine outlier reels
Apify instagram-reel-scraper on the niche's competitor handles (`APIFY_TOKEN` in
`~/ventures/stayframe/.env`):
```bash
curl -s -X POST "https://api.apify.com/v2/acts/apify~instagram-reel-scraper/run-sync-get-dataset-items?token=$APIFY_TOKEN&timeout=180" \
  -H "Content-Type: application/json" -d '{"username":["<handle>"],"resultsLimit":30}'
```
Outlier filter: plays ≥3× the account's own median (or ≥3× followers). Tag each `person-led` |
`property-led`. Reference-selection rubric (reject early, reel-deconstruction §5): outlier by the 3×
math · property-driven (not borrowed virality) · target can fill every beat from photos it has ·
people not load-bearing or convertible · register reachable (no drone/crew-dependent format).

## 2. Analyze the chosen reel
Download: `uvx yt-dlp <reel-url>` (brew yt-dlp is broken — always `uvx`). Deconstruct with Gemini
(reads the mp4 AND hears the audio in one call):
```bash
export PATH="$HOME/jstack/vendor/gemini-vision:$PATH"; cd <dir>
gv --json -p "<11-section deconstruction prompt> @reel.mp4" | jq -r '.response'
```
Exact cut times matter? Cross-check `ffmpeg -i reel.mp4 -vf "select='gt(scene,0.3)',showinfo" -f null -`.
11-section schema + clone-and-improve: reel-deconstruction §3–4.

## 3. Draft the replication brief
Write `clients/<slug>/briefs/<date>-<reel>-brief.md` in the **Sands brief shape** so the dashboard
renders it. Canonical worked examples: still prompts →
`clients/serenity-sands/briefs/2026-06-12-sands-v3-veo-brief.md`; Veo single-start clip prompts (four
verbatim beats) → `clients/serenity-sands/briefs/2026-06-14-sands-v3-organic-brief.md`.
- Frontmatter: `client, reel, hook ("line1|line2"), kicker, render_subdir, aspect_ratio,
  still_model, clip_model, clip_duration, clip_type`. **Frontmatter MUST match the body** — same engine
  + duration as the per-beat prompts (a brief whose frontmatter and body disagree is a lint-passing bug).
  `still_model`/`clip_model` here are the *proposed defaults* (from the matrix); they're confirmed or
  overridden at the **Render Gate** in Produce, then written back.
- Continuity anchors (grade + property) copied **verbatim** into every prompt; red-line / props rules.
- `## Beat N` per beat: a standalone still prompt + a standalone clip prompt (no "as above").

Prompt standard (binding — the engine picks the format; full matrix → `~/ventures/stayframe/playbook/index.md §2`):
- **DEFAULT — any beat with a real camera move → Veo 3.1 single-start-frame block**
  (`reel-prompt-system.md §single-start-frame`): one start frame, no end frame, dolly/pan/tilt not zoom,
  named-plane parallax, living handheld. Decided 2026-06-15 → `DECISIONS.md`. Invoke
  `creative-production-skills:cinematic-motion-language` for the camera/motion craft.
- **visible-motion beat → Kling O3 ref-to-video, 9-field formula** (Subject / SubjectDescription /
  Movement / Scene / SceneDescription / Camera / Lighting / Atmosphere / Negative) — `reel-deconstruction.md §7`,
  invoke `creative-production-skills:kling-3-prompt-director`.
- **deliberately flat micro-reframe → Kling O3 i2v** on a cropped first+end pair (`end-frame-method.md`).
- A same-still i2v lock with no motion is the v2 slideshow failure — never the default; allowed only as a
  named deliberate-stillness choice.

QA-tag → 9-field mapping (INVERTED, qa/AGENTS.md): an approval tag flags what is BAD in the reference
= the slot that MUST change — `architecture`→SubjectDescription · `lighting`→Lighting ·
`mood`→Atmosphere · `composition`/`framing`→Camera. Untagged dimensions = what Jono liked, lock from
the reference. No tags = good across the board, vary creatively. His `note` overrides everything.

## 4. Approval gate (SOFT — human)
Surface to Jono: the chosen reel (why it's the clone target + its replicability score 1–5) and the
drafted brief. On his yes → **produce**. On changes → revise the brief and re-surface. Don't produce
before the yes.
