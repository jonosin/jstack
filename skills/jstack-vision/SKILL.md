---
name: jstack-vision
description: >-
  Analyze images, audio, video, or PDFs using Google Gemini via
  Vertex AI (GCP credits). Generic multimodal router. Use when the user
  explicitly says "analyze with gemini", "use gemini vision", "run through
  gemini", "transcribe with gemini", "describe with gemini", or invokes
  /jstack-vision. Works on any media file the caller supplies — photos,
  screenshots, diagrams, UI, products, art, audio, video, documents.
  NOT for: live streams, real-time analysis, or when the host model's
  own vision/audio is acceptable.
---

# jstack-vision — generic Gemini multimodal router

Wraps the official `gemini` CLI (Vertex AI mode) for one-off or batch
multimodal analysis. Generic — no domain vocabulary, no industry-specific
defaults. Caller supplies the prompt and the files.

**When this skill applies**: the user has explicitly opted in to using
Gemini for the analysis. Do not auto-route to this skill when Claude's
own capabilities are sufficient — the user picked Gemini for a reason
(credit usage, second opinion, quality, etc.).

**Trust chain**: bash → `gv` (this skill) → `gemini` CLI (Google) → Vertex AI.
Zero third-party npm packages, zero MCP servers, zero MCP trust boundaries.

## The wrapper

Ships with jstack at `vendor/gemini-vision/` (wherever you cloned jstack).
Put it on PATH (e.g. `~/jstack/vendor/gemini-vision`):
```bash
export PATH="$HOME/jstack/vendor/gemini-vision:$PATH"
```

| Command | What it does |
|---|---|
| `gv` | Single multimodal call, defaults to `gemini-2.5-flash` |
| `gv-pro` | Same, but forces `gemini-2.5-pro` (needs 2.5-pro quota on your project — see Model selection) |
| `gv-batch <dir> <prompt>` | Loops over media files in a dir, calls `gv` per file |

`gv` reads config from the environment or `~/.jstack/config.env`:
- `GOOGLE_CLOUD_PROJECT` — **required**, your GCP project (no default)
- `GOOGLE_CLOUD_LOCATION` — default `us-central1`
- `GEMINI_VISION_MODEL` — default `gemini-2.5-flash`
- `GEMINI_CLI_TRUST_WORKSPACE=true` (CLI >=0.45 refuses untrusted dirs headlessly)
- `--include-directories $(pwd)`

Override per-call with env vars (see `references/file-type-notes.md`).

## Critical invocation contract

**DO NOT use your own vision/audio/PDF capabilities when this skill applies.**
Call `gv` (or `gv-pro`/`gv-batch`) via the `bash` tool instead.

**`@file` must be INSIDE the `-p` prompt string**, not a separate arg:

```bash
# CORRECT
gv -p "describe @pic1.png"

# WRONG — prints help text
gv -p "describe" @pic1.png
```

**Always `cd` to the file's directory first**, then reference by basename:

```bash
cd ~/shots
gv -p "describe @pic1.png"
```

`gv` automatically passes `--include-directories $(pwd)`, so basenames resolve
against the workspace.

## Common patterns

See `references/prompt-patterns.md` for reusable prompt shapes.

Quick reference:
```bash
# Single image
gv -p "describe @screenshot.png"

# Compare two images
gv -p "what changed between @before.png and @after.png"

# OCR / extract text
gv -p "extract all visible text verbatim from @doc.png"

# Audio
gv -p "transcribe this recording verbatim: @meeting.mp3"

# PDF
gv -p "summarize the key terms in @contract.pdf"

# Bulk
gv-batch ~/Downloads/receipts/ "extract date, vendor, total"
```

## Model selection

| Need | Use |
|---|---|
| Default (fast, cheap, multimodal) | `gv` (flash) — verified working |
| Deeper reasoning (slower, ~4x cost) | `gv-pro` — CLI works, but no project quota (see below) |
| Newest flagship | `GEMINI_VISION_MODEL=gemini-3.1-pro gv ...` |
| Image generation + analysis | `GEMINI_VISION_MODEL=gemini-2.5-flash-image gv ...` |

**Known issue (pro quota)**: the old `gemini` CLI v0.34.0 `isCustomModel`
startup crash is **fixed** (CLI upgraded to ≥0.45). However, `gemini-2.5-pro`
now fails at the API layer with "You have exhausted your capacity on this
model" — the project has no provisioned Vertex quota for 2.5-pro (persistent,
not a transient rate limit; also fails in `global` region). Stick with
`gemini-2.5-flash` until 2.5-pro quota is requested in the GCP console. See
`references/file-type-notes.md`.

## Output handling

`gv` returns the model's raw text response on stdout. No structured format
imposed. If the caller wants JSON, ask for it in the prompt:

```bash
gv -p "Describe this image. Return JSON: {description, objects: []}" @pic.png
```

The agent (Claude) parses the response and formats as needed for the user.

## Failure handling

| Error | Action |
|---|---|
| "exhausted your capacity" on `gemini-2.5-pro` | No project quota for 2.5-pro (persistent). Use flash, or request quota in GCP console. |
| Transient 429 on flash | Sleep 5–10s, retry once. `gv-batch` does this. |
| 404 / model not found | Check model name spelling. Some models aren't in all regions. |
| "I cannot locate the file" | Use basename after `cd` to the file's dir. |
| CLI prints help text | `@file` was passed as a separate arg; put it inside the `-p` string. |
| "not running in a trusted directory" | `gv` sets `GEMINI_CLI_TRUST_WORKSPACE=true` already; if calling `gemini` directly, export it or pass `--skip-trust`. |

## What this skill does NOT do

- Generate images (use `gemini-2.5-flash-image` model with a generation prompt if needed — out of scope of typical analysis).
- Stream live audio/video (Vertex AI has streaming endpoints via SDK, but the CLI doesn't expose them in headless mode).
- Replace Claude's own multimodal capabilities for tasks where the user hasn't asked for Gemini.
- Manage GCP billing or credits — that's a console task.

## References

- `references/prompt-patterns.md` — generic prompt shapes per modality
- `references/file-type-notes.md` — size limits, keyframe recipe, model availability
- `vendor/gemini-vision/AGENTS.md` — full operational contract
- `vendor/gemini-vision/README.md` — human-facing docs
