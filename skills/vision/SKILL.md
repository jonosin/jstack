---
name: vision
description: >-
  Analyze images, audio, video, or PDFs using Google Gemini via
  Vertex AI (GCP credits). Generic multimodal router. Use when the user
  explicitly says "analyze with gemini", "use gemini vision", "run through
  gemini", "transcribe with gemini", "describe with gemini", or invokes
  /vision. Works on any media file the caller supplies — photos,
  screenshots, diagrams, UI, products, art, audio, video, documents.
  NOT for: live streams, real-time analysis, or when the host model's
  own vision/audio is acceptable.
---

# vision — generic Gemini multimodal router

Wraps the official `gemini` CLI (Vertex AI mode) for one-off or batch
multimodal analysis of **images, audio, VIDEO, and PDFs** — all four media
types are fully supported today, not a roadmap item. Generic — no domain
vocabulary, no industry-specific defaults. Caller supplies the prompt and
the files.

## What it handles

| Media type | Supported | Notes |
|---|---|---|
| Images | Yes | Photos, screenshots, diagrams, UI, product/art shots. OCR via prompt. |
| Audio | Yes | Verbatim transcription, summarization. See `references/file-type-notes.md` for size limits. |
| Video | Yes | Frame-by-frame or full-clip analysis and description; see `references/file-type-notes.md` for the keyframe recipe on longer clips. |
| PDFs | Yes | Summarize, extract terms, structured extraction. |
| Live streams / real-time | No | Vertex AI has streaming endpoints via SDK, but the `gemini` CLI doesn't expose them headlessly. |
| Image generation | No | Analysis only — see "What this skill does NOT do". |

**When this skill applies**: the user has explicitly opted in to using
Gemini for the analysis. Do not auto-route to this skill when Claude's
own capabilities are sufficient — the user picked Gemini for a reason
(credit usage, second opinion, quality, etc.).

**Trust chain**: bash → `gv` (this skill) → `gemini` CLI (Google) → Vertex AI.
Zero third-party npm packages, zero MCP servers, zero MCP trust boundaries.

## The wrapper

Ships with jstack at `vendor/gemini-vision/` (wherever you cloned jstack).
Put it on PATH:
```bash
export PATH="$HOME/jstack/vendor/gemini-vision:$PATH"
```

| Command | What it does |
|---|---|
| `gv` | Single multimodal call, defaults to `gemini-2.5-pro` (Vertex/credits) |
| `gv-pro` | Same as `gv` now (also `gemini-2.5-pro`) |
| `gv-batch [--json] <dir> <prompt>` | Loops over media files in a dir, calls `gv` per file |

## Agent-native flags

`gv` parses these itself (they are not forwarded to `gemini`):

| Flag | Effect |
|---|---|
| `--json` | Emit a structured envelope instead of raw text: `{ok, model, project, location, prompt, files, response, error, error_class, exit_code}`. Parse `.response` for the answer; check `.ok` / `.exit_code` to branch on failure. |
| `--dry-run` | Print the resolved `gemini` invocation (and the billing project) without calling the API. Combine with `--json` for a machine-readable preview. No credits spent. |
| `-h`, `--help` | Print `gv` usage and exit. |
| `--version` | Print `gv` + `gemini` versions and exit. |

`gv-batch --json` aggregates per-file envelopes into one object:
`{dir, prompt, total, ok, failed, results: [envelope...]}` (each result also carries its `file`).

## Exit codes

`gv` returns typed exit codes so a caller can branch without grepping stderr:

| Code | Meaning |
|---|---|
| `0` | Success |
| `2` | Usage error (missing `-p`, bad flag) |
| `3` | Config error (no GCP project set) |
| `4` | Auth / billing (Vertex not forced, free-tier "exhausted your capacity", expired OAuth) |
| `5` | Model unreachable (`404 ModelNotFound`, flash remap) |
| `6` | Input / file error (defensive — gemini usually reports a missing file as a 0-exit text answer, so this rarely fires) |
| `7` | Dependency missing (`gemini` not on PATH) |
| `10` | Unknown upstream failure |

In `--json` mode the same value is also in `.exit_code`, with a human-readable class in `.error_class`.

`gv` reads config from the environment or `~/.jstack/config.env`, and sets
(all overridable):
- `GOOGLE_CLOUD_PROJECT` ← `GEMINI_VISION_PROJECT` or `GOOGLE_CLOUD_PROJECT` (**required, no default**); pinned so the shell's ambient `GOOGLE_CLOUD_PROJECT` can't bill the wrong project
- `GOOGLE_CLOUD_LOCATION=us-central1`
- `GEMINI_VISION_MODEL=gemini-2.5-pro` (flash may not be reachable via the CLI — see Model selection)
- `GOOGLE_GENAI_USE_VERTEXAI=true` **+** `GEMINI_CLI_SYSTEM_SETTINGS_PATH=<dir>/gemini-vertex-settings.json` → forces Vertex auth so calls bill GCP credits, not the free Code Assist tier (the env flag alone is ignored when the global CLI has `selectedType: oauth-personal`)
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
| Default multimodal (image/pdf/audio/video) | `gv` (gemini-2.5-pro on Vertex) — verified working, billed to GCP credits |
| Image generation + analysis | `GEMINI_VISION_MODEL=gemini-2.5-flash-image gv ...` (untested) |

**Why pro, not flash**: on Vertex, `gemini-2.5-pro` works and bills GCP credits.
`gemini-2.5-flash` may be **not reachable via the CLI** — gemini-cli 0.45
hard-remaps any flash request to `gemini-3.x-flash`
(`DEFAULT_GEMINI_FLASH_MODEL`), which a project without that grant can't reach
→ `404 ModelNotFound`. So `gv` defaults to pro. To use cheap flash you'd call
the google-genai SDK directly (Vertex), bypassing the CLI's remap.

**Background**: the v0.34.0 `isCustomModel` startup crash is fixed by upgrading
to ≥0.45, and the "exhausted your capacity" error is usually the **free Code
Assist tier**, not Vertex — `gv` forces Vertex auth to avoid it. See
`references/file-type-notes.md`.

## Output handling

By default `gv` returns the model's raw text response on stdout — no structured
format imposed. Two ways to get structure:

1. **Envelope (recommended for agents):** add `--json`. You get
   `{ok, model, project, location, prompt, files, response, error, error_class, exit_code}`
   regardless of the prompt, so you can branch on `.ok` and read `.response`
   without parsing free text.
   ```bash
   gv --json -p "describe @pic.png" | jq -r '.response'
   ```
2. **Model-shaped JSON:** ask for it in the prompt when you want the *answer*
   itself structured (the envelope's `.response` then holds JSON text).
   ```bash
   gv -p "Describe @pic.png. Return JSON: {description, objects: []}"
   ```

Combine them: `gv --json -p "... Return JSON: {...}"` gives an envelope whose
`.response` is the model's JSON string.

## Recipes

```bash
# Preview the exact call + billing project before spending credits
gv --dry-run -p "transcribe @meeting.mp3"

# Agent-native: get the answer, fail loudly on auth/model errors
out=$(gv --json -p "what color is @logo.png?") || echo "gv failed: $(jq -r .error_class <<<"$out")"
jq -r '.response' <<<"$out"

# Batch a folder into one JSON object you can iterate
gv-batch --json ~/receipts/ "extract date, vendor, total as JSON" \
  | jq '.results[] | {file, response}'
```

## Failure handling

| Error | Exit | Action |
|---|---|---|
| "exhausted your capacity… quota will reset after Xh" | `4` | Calls hit the free Code Assist tier, not Vertex. Use `gv` (forces Vertex). Don't call `gemini` directly without `GEMINI_CLI_SYSTEM_SETTINGS_PATH`. |
| `404 ModelNotFound … gemini-3-flash` | `5` | CLI remapped flash → gemini-3.x-flash (no access). Use `gemini-2.5-pro` (default). |
| Transient 429 | `10` | Sleep 5–10s, retry once. `gv-batch` paces calls with `GV_BATCH_SLEEP`. |
| "I cannot locate the file" | `0`* | Use basename after `cd` to the file's dir. *gemini usually answers this as a 0-exit text response, so check `.response`, not just the exit code. |
| CLI prints help text | — | `@file` was passed as a separate arg; put it inside the `-p` string. |
| "not running in a trusted directory" | `4` | `gv` sets `GEMINI_CLI_TRUST_WORKSPACE=true` already; if calling `gemini` directly, export it or pass `--skip-trust`. |
| no GCP project set | `3` | Export `GEMINI_VISION_PROJECT` / `GOOGLE_CLOUD_PROJECT`, or set it in `~/.jstack/config.env`. |
| `gemini` not on PATH | `7` | `brew install gemini-cli`. |

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

## Next skills

| Next | When |
|------|------|
| Calling skill (e.g. `/jstack-sf-new`) | vision is usually invoked BY another skill for catalog/creative analysis — return its result to that caller. |
| Otherwise | Standalone — a one-off Gemini multimodal analysis with no required next step. |
