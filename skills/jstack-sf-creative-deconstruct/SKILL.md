---
name: jstack-sf-creative-deconstruct
description: "Deconstruct a reel or TikTok slideshow link into a StayFrame learnings-catalog card. Use when Jono pastes a TikTok / Instagram / YouTube link (a winning reel or photo/slideshow post) to add to the catalog, says /jstack-sf-creative-deconstruct, 'deconstruct this reel', 'break down this video', 'add this to the learnings catalog', or 'turn this link into a card'. One link in -> one deconstruction card + rebuilt index out. Acquire is link-type aware (video vs slideshow); analysis runs the canon 11-section schema."
---

# jstack-sf-creative-deconstruct

One reel/slideshow link → one StayFrame **learnings-catalog card**, index rebuilt, lint clean.
This skill is a **runnable wrapper** over the existing canon — it dispatches and glues, it does **not**
re-define the schema. Source of truth stays:

- **Schema + analyze tooling:** `~/ventures/stayframe/playbook/method/reel-deconstruction.md` (§3 = the 11-section deconstruction schema, §1 = acquire lanes).
- **Taxonomy + card frontmatter + controlled vocab:** `playbook/method/ig-pattern-mining.md §3` and the spec `docs/superpowers/specs/2026-06-15-learnings-catalog-design.md`.
- **Driver:** `tools/learnings.py` (`build` compiles the derived index, `query` ranks for the creative phase).

All paths under `~/ventures/stayframe/` (abbrev `SF`). **Brain ⊥ satellite:** this is StayFrame craft —
it never gets copied to `~/second-brain`. Offer `/jstack-savetobrain` only if a *strategy* decision surfaces.

## When to use
Jono pastes one or more links to *winning* posts he picked (discovery is OFF by default — he supplies the
links; auto-sourcing via Apify is `research-router` territory and only on his explicit ask). Each link →
one card. Batch by processing each link through the full loop.

## Loop (per link)

### 0. Classify the link
- TikTok `…/video/<id>`, Instagram reel, YouTube → **video path**.
- TikTok `…/photo/<id>` (a photo/slideshow post) → **slideshow path**.
- Unsure? `/photo/` in the URL ⇒ slideshow. Don't rewrite `/photo/`→`/video/` — TikTok 404s the rewrite.

### 1. Acquire (link-type aware — verified end-to-end 2026-06-15)
Brew `yt-dlp` is broken (`No module named expat`) — **always `uvx`**. Work in a temp dir, then move the
raw media into `SF/playbook/learnings/reels/`.

| Link type | Tool | Output |
|---|---|---|
| **TikTok — video AND slideshow** | `uvx gallery-dl -q -D <dir> <url>` | video → `.mp4`; slideshow (`/photo/`) → N `.jpg` + the post's `.mp3` |
| Instagram reel, YouTube | `uvx yt-dlp -f "mp4/best" -o "<slug>.%(ext)s" <url>` | merged `mp4` + audio |

**TikTok: prefer `gallery-dl` for both video and slideshow** — it reliably handled both in testing.
`yt-dlp`'s TikTok extractor is flaky behind TikTok's JS challenge (intermittent *"Unable to extract
universal data for rehydration"*) and routes `/photo/` URLs to its generic extractor → *"Unsupported
URL"*. Don't rewrite `/photo/`→`/video/` (TikTok 404s it).

**Metrics gotcha:** `yt-dlp --print …` implies `--simulate` — it prints metadata but **downloads
nothing**. To grab the multiple without downloading, run a metadata-only pass
(`uvx yt-dlp --skip-download --print "plays=%(view_count)s likes=%(like_count)s dur=%(duration)s" <url>`)
and download separately with `gallery-dl`. `gallery-dl` does **not** return play counts — for the outlier
multiple on a TikTok slideshow use the Apify `clockworks~tiktok-scraper` recipe (`reel-deconstruction.md §1`),
or record `metrics: {}` when Jono only wants the structure (he picked the winner).

Fallbacks (in order): curl the Apify `videoUrl` · brave-cdp logged-in session · Jono screen-records.

### 2. Deconstruct — `gv` (Gemini via Vertex/credits)

```bash
export PATH="$HOME/jstack/vendor/gemini-vision:$PATH"
```

**Video path** — `gv` reads the whole mp4 + audio in one call (direct path; keeps motion, transitions,
beat-sync). If `gv` rejects the file or returns a refusal, fall back to keyframe extraction
(`jstack-vision references/file-type-notes.md` Path 2) **plus** a separate audio transcription, because
keyframes drop motion *and* audio. When exact cut times matter, cross-check with ffmpeg scene-detect:
```bash
ffmpeg -i <slug>.mp4 -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1 | grep -o 'pts_time:[0-9.]*'
```

**Slideshow path** — first normalize the `gallery-dl` filenames (they carry spaces + hashtags that break
ffmpeg globs): rename the stills to `img_01.jpg…` and the audio to `audio.mp3`. Then assemble stills +
audio into one mp4 so it's (a) `gv`-analyzable in a single call with audio and (b) playable in the
dashboard's video-only `reel` endpoint. Use a **fixed ~3s/slide dwell** (TikTok's mp3 is the full ~60s
track, not the post's display time — even-dwell-over-audio makes a needlessly long, token-heavy clip):
```bash
ffmpeg -y -framerate 1/3 -i '<dir>/img_%02d.jpg' -i '<dir>/audio.mp3' \
  -c:v libx264 -pix_fmt yuv420p -vf "scale=720:-2,format=yuv420p" -c:a aac -shortest <slug>.mp4
```
Keep the raw images + mp3 under `learnings/reels/<slug>/` for provenance; set `reel:` to the assembled
`<slug>.mp4`. Then `gv` the assembled mp4 (tell it the dwell is synthetic — focus on slide order/content). Run the **same 11-section schema** with these adaptations
(note them in the card body):
- Section 1 **slide table** replaces the shot table: `slide # | subject | composition | overlay text`.
- Camera-motion / beat-sync fields are **N/A** (a slideshow has none); `motion:` frontmatter = `static`
  (or `transition` if the post adds crossfades). Pacing = slide count + dwell (mark dwell synthetic).
- Everything else (hook, register, overlay, audio, structure template, people dependency, replicability,
  why-it-performed, clone-and-improve) applies unchanged.

### 3. Write the card — `learnings/deconstructions/<date>-<slug>.md`
Copy a seed card's frontmatter as the template
(`learnings/deconstructions/2026-06-11-turtlefiji-still-serenity.md`). Frontmatter (controlled vocab —
`property_type / beats / motion` from the spec; the build prints a soft warning for off-vocab tags):
```yaml
type: deconstruction
slug: <account>-<candidate-pattern>
title: "<@account short label> (<multiple>x)"
source_url: <url>
source_platform: tiktok|instagram|youtube
metrics: {plays: N, median: N, multiple: N}   # {} if unknown
tag: property-led|person-led                   # person-led ⇒ record an evidence-of-people conversion plan
replicability: 1-5                             # can stills+i2v fill every beat under augment-not-fabricate? ≤2 ⇒ reject
property_type: [...]
beats: [...]
motion: [...]                                  # slideshow ⇒ [static]
register: polished-guest-eye|...
candidate_pattern: <slug>                       # the pattern this is evidence for (may not exist yet)
reel: ../reels/<slug>.mp4
created: <date>
```
Body = the 11-section schema (`reel-deconstruction.md §3`), with the slideshow adaptations above when
relevant. **Red line carries through:** any clone-and-improve plan augments the property's REAL photos
only — no invented guests/amenities/structures. Store pattern intent **engine-agnostic** (prompt rules,
not Veo/Kling format) — format is applied later at the Render Gate.

### 4. Rebuild + verify
```bash
cd ~/ventures/stayframe
python3 tools/learnings.py build      # fix any error it prints (e.g. unresolved examples slug)
python3 tools/learnings.py query      # confirm the new card appears
```

### 5. Promote when a 2nd reel rhymes
When a new deconstruction matches an existing `candidate_pattern`, extend the pattern card
(`learnings/patterns/<slug>.md`): add the new slug to `examples: [...]` and flip `status`
`untested → replicated` (→ `validated` once it performs for *us*). Patterns are the payoff —
`creative.md §1` queries them for the next client. A new pattern method that becomes real canon →
capture via `/jstack-sf-learn` (writes the playbook + `DECISIONS.md`).

### 6. Lint gate
```bash
python3 tools/sf_lint.py     # must stay 0
```
**Do not commit** unless Jono says so — he reviews.

## Definition of done (per batch)
Each link → one deconstruction card with valid frontmatter, raw media in `learnings/reels/`,
`index.json` rebuilt clean, `sf_lint` 0. Any pattern reaching ≥2 examples promoted out of `untested`.
Report: cards added, patterns promoted, off-vocab tags introduced (if any), slideshow adaptations used,
Gemini spend.

## Out of scope
Apify auto-discovery (Jono supplies links) · dashboard write-back curation · brain copies of craft.

## Next skills

| Next | When |
|---|---|
| `/jstack-sf-new <resort>` | Apply the learned pattern when building a resort reel — `creative.md §1` queries the catalog for the next client. |
| `/jstack-sf-learn` | A new pattern method became real canon and should be written into the playbook + `DECISIONS.md`. |
| `/jstack-sf` | Unsure of next step — route by intent / read-only StayFrame status. |
