# YouTube Route — jstack-savetobrain

Deterministic YouTube transcript capture. When the user provides a YouTube URL to savetobrain, run `scripts/youtube-capture.py` — one shot, no decisions.

## Trigger

User input contains a YouTube URL (`youtube.com/watch`, `youtu.be/`, `youtube.com/shorts`, `youtube.com/live`) and the intent is to save it to the second brain.

## Workflow

### Phase 1 — Deterministic capture (script)

Run the script. Single invocation, zero flags:

```
python3 ~/jstack/skills/jstack-savetobrain/scripts/youtube-capture.py "<youtube_url>"
```

The script handles everything that doesn't require judgment:
- Extracts video ID from any YouTube URL format
- Fetches full transcript via `youtube-transcript-api`
- Gets metadata (title, channel, date, duration) via `yt-dlp`
- Cleans artifacts: removes `[music]`, `[snorts]`, `[laughter]`, `>>` separators, filler words
- Fixes common ASR name/product misspellings (see `NAME_FIXES` dict in script)
- Saves as `raw/clips/YYYY-MM-DD-<slug>-readable-transcript.md` with full frontmatter
- Prints the absolute path to stdout

If the script fails:
- Transcript unavailable / captions disabled → report: "No transcript available for this video."
- Network error → retry once, then report failure.
- Do not fabricate, do not summarize from title/description, do not use ASR fallback.

### Phase 2 — Sectioning (LLM judgment over a compact scaffold)

**Do NOT read the full transcript back into context** — a 3-hour podcast is ~50K tokens and you only need to place ~12 headings. Instead work over a compact offset scaffold so cost is flat regardless of length:

1. Get the scaffold (a few KB even for a 197KB clip):
   ```
   python3 ~/.claude/skills/jstack-savetobrain/scripts/youtube-capture.py scaffold "<clip_path>"
   ```
   It prints JSON: `{body_chars, n_segments, segments:[{i, offset, preview, cue?}]}` — one short preview per candidate boundary. Some segments carry a `cue` flag (`"sponsor"` or `"qa"`): the script scanned the full window and found a sponsor read or Q&A transition the 12-word preview might not show. A cue tells you *where* a sponsor/Q&A block sits so you can name it correctly — it does **not** add to your section budget. Fold each cue into the count band below: when you place a section near a cue, name it for the cue (e.g. `Sponsor: AG1`), and a cue boundary *replaces* a nearby topical boundary rather than adding one. The length band is a hard ceiling — never exceed it just because there are several cues.
2. Read ONLY the scaffold. From the previews (and any `cue` flags), pick the segment indices where a new topic clearly begins — speaker intros, subject changes, Q&A transitions, sponsor breaks. Write a short descriptive heading for each (e.g. `BPC-157: History and Discovery`, `Sponsor: Eight Sleep`, `Audience Q&A`).
3. Write the picks to a temp JSON file as `[{"i": <segment index>, "heading": "<text>"}]`, then insert deterministically (headings inserted at byte offsets — body is never rewritten, so integrity is guaranteed):
   ```
   python3 ~/.claude/skills/jstack-savetobrain/scripts/youtube-capture.py insert "<clip_path>" "<picks_json_path>"
   ```
4. Report to user:
   ```
   Saved: raw/clips/<file>.md — "<title>" (<channel>, <duration>, <N> sections)
   ```

Pick count, by length: 10-min clip → 2-4; 30-min → 4-8; 3-hour podcast → 10-15. **Don't over-segment** — each section is a coherent topic block, not every paragraph. A flat single-topic monologue may warrant 1-2 sections only; never invent a boundary the previews don't support. If the scaffold has fewer real topic shifts than the length band suggests, prefer fewer sections.

## Output format

```markdown
---
title: "Video Title"
source: "https://youtu.be/<id>"
channel: "Channel Name"
video_id: "<id>"
duration: "H:MM:SS"
published: YYYY-MM-DD
collected: YYYY-MM-DD
tags: [youtube, transcript, readable]
---

# Video Title

Source: https://youtu.be/<id>
Channel: Channel Name
Video ID: <id>
Duration: H:MM:SS
Collected: YYYY-MM-DD

Cleaned transcript text...
```

No timestamps. Sections are added by the agent in Phase 2, not by the script.

## Extending name fixes

The `NAME_FIXES` dict in `scripts/youtube-capture.py` maps ASR misspellings → corrections. When you encounter new patterns (wrong names, products, technical terms), add them to the dict. Keep it lean — only add fixes you've actually seen in transcripts, not speculative ones.

## Determinism contract

- Same URL → same output every time (metadata may drift if video title/channel changes)
- No LLM calls, no network calls beyond transcript API + yt-dlp metadata
- No interactive prompts, no branching logic
- Script exit code 0 = success; non-zero = failure with stderr message
