# X link route — deterministic raw clip capture

Use this when the user explicitly asks to save an X/Twitter link to the second brain.

## Goal

Preserve the external source as flat raw v2 in `raw/` with minimal editorial judgment. Do not write wiki pages. Brainwork compiles later.

## Deterministic workflow

1. Load the second-brain contract before writing:

```bash
Read ~/second-brain/AGENTS.md
Read ~/second-brain/SKILL.md
```

2. Extract the tweet/status ID and handle from the URL.

Example URL:

```text
https://x.com/monokern/status/2071246711222055363?s=...
```

Extract:

```text
handle=monokern
status_id=2071246711222055363
```

3. Check for an existing raw clip before fetching.

Search both the status ID and handle under `raw/`:

```text
search_files(pattern="2071246711222055363|monokern", path="~/second-brain/raw", target="content")
```

If a raw file already contains the status ID, do not create a duplicate. Report the existing path and run `python3 tools/sb.py pending` for the final backlog count.

4. Fetch the post content with X Search first.

Use `x_search` with image/video understanding on:

```text
query="url:<status_id> OR <status_id>"
enable_image_understanding=true
enable_video_understanding=true
```

If that returns a usable post/thread body, keep it as provenance, but still try the browser extraction below when possible because the browser can expose the actual rendered text.

5. Open the canonical URL in the browser.

```text
browser_navigate("https://x.com/<handle>/status/<status_id>")
```

Then extract rendered article text with page JS:

```javascript
Array.from(document.querySelectorAll('article')).map(a=>a.innerText).join('\n---ARTICLE---\n')
```

Use `browser_console(expression=...)` for this. This was the working method for the monokern save: X rendered the article in the logged-in browser, and `article.innerText` returned the full post body plus metrics.

6. Choose the source text deterministically.

Prefer sources in this order:

1. Browser `article.innerText` from the canonical status page, if it contains the original author, handle, title/body, timestamp or metrics.
2. X Search result for the exact status ID, if browser rendering is blocked or incomplete.
3. Browser snapshot text, only if both above fail and it contains enough of the post to preserve the source.

Never invent missing sections. If the thread is truncated, say it is truncated in the raw clip. If the post is an X Article and only the article preview/body is visible, preserve exactly what was visible.

7. Write a raw clip, not a drop.

Prepare the capture and use its exact raw v2 metadata before the atomic write:

```bash
python3 tools/sb.py capture prepare --route x --source "https://x.com/<handle>/status/<status_id>" --target "raw/YYYY-MM-DD-<handle>-<short-topic-slug>.md" --json
```

Path format:

```text
~/second-brain/raw/YYYY-MM-DD-<handle>-<short-topic-slug>.md
```

Use the exact raw-v2 frontmatter returned by prepare. Do not add tags, author,
platform, or route-local source fields. Do not invent an ID.

8. Body format.

Preserve the external content as closely as possible. Light Markdown cleanup is allowed only to make the captured source readable:

- Keep author/handle.
- Keep the post title or first line.
- Preserve section headings and code blocks.
- Preserve quoted prompts as blockquotes or fenced code.
- Preserve visible metrics/timestamp if present.
- Do not add agent analysis, takeaways, or recommendations.

9. Finalize once, then verify.

Run from the brain root:

```bash
python3 tools/sb.py capture finalize --route x --artifact "raw/<file>.md" --json
python3 tools/sb.py compile status --json
```

Finalization registers compile state. It does not perform semantic extraction.

## Final response

Use the normal `savetobrain` two-line report:

```text
Saved raw source: raw/<file>.md — <one-line description>. Brainwork deferred.
Pending ingest backlog: <N> source(s). Run /brainwork to process.
```

If the clip already existed:

```text
Already saved: raw/<file>.md. Brainwork still deferred.
Pending ingest backlog: <N> source(s). Run /brainwork to process.
```
