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

### Phase 2 — Sectioning (LLM judgment)

After the script succeeds, read the saved file back into context. Then apply your judgment:

1. Scan the transcript for natural topic shifts — speaker introductions, subject changes, Q&A transitions, sponsor breaks.
2. Insert `##` section headings at those boundaries. Headings should be short and descriptive (e.g. `## BPC-157: History and Discovery`, `## Sponsor: Eight Sleep`, `## Audience Q&A`).
3. Rewrite the file with sections in place. Do not alter the frontmatter or the body text itself — only insert headings.
4. Report to user:
   ```
   Saved: raw/clips/<file>.md — "<title>" (<channel>, <duration>, <N> sections)
   ```

Keep sectioning lean. For a 10-minute video, 2-4 sections is plenty. For a 3-hour podcast, 10-15 sections is appropriate. Don't over-segment — each section should cover a coherent topic block, not every paragraph.

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
