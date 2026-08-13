# gv — Gemini Vision (generic multimodal)

Generic wrapper around Google's official [`gemini` CLI][cli] for calling
Gemini models via Vertex AI. Works on images, audio, video, and PDFs.

[cli]: https://github.com/google-gemini/gemini-cli

## Install

Already installed if you have:
- `gemini` CLI on PATH (`brew install gemini-cli`)
- Cached GCP OAuth credentials (Application Default Credentials)

The scripts in this directory are drop-in. Add this directory to `PATH`
(adjust to wherever you cloned jstack):
```bash
export PATH="$HOME/jstack/vendor/gemini-vision:$PATH"
```

## Quick start

```bash
# Image
gv -p "describe this" @~/pic.jpg

# gv defaults to gemini-2.5-pro on Vertex (billed to GCP credits). gv-pro is the same.
gv-pro -p "deep analysis" @~/screenshot.png

# Audio
gv -p "transcribe verbatim" @~/recording.mp3

# Video (CLI may require keyframe fallback; see AGENTS.md)
gv -p "what happens" @~/clip.mp4

# PDF
gv -p "summarize page 1" @~/doc.pdf

# Bulk
gv-batch ~/Downloads/receipts/ "extract date, vendor, total"
```

## Agent-native flags

`gv` understands a few flags of its own (everything else is forwarded to `gemini`):

```bash
gv --json    -p "describe @pic.png"   # structured envelope: {ok, response, error_class, exit_code, ...}
gv --dry-run -p "describe @pic.png"   # show the resolved call + billing project; no API call, no credits
gv --version                          # gv + gemini versions
gv --help                             # usage

gv-batch --json ~/receipts/ "extract date, vendor, total"  # aggregated {total, ok, failed, results[]}
```

`gv` returns **typed exit codes** (`0` ok · `2` usage · `3` config · `4` auth/billing ·
`5` model unreachable · `6` input · `7` missing `gemini` · `10` unknown), so callers
can branch on failure without grepping stderr. See `AGENTS.md` for the full table.

## Files

| File | Purpose |
|---|---|
| `gv` | Main wrapper. Defaults to `gemini-2.5-pro`, your project, `us-central1`. Forces Vertex auth. |
| `gv-pro` | Same as `gv` (also `gemini-2.5-pro`). |
| `gv-batch` | Loops a directory of media files, calls `gv` per file. |
| `AGENTS.md` | Operational contract: env vars, models, auth, failure modes, limits. |
| `gemini-vertex-settings.json` | Forces `selectedType=vertex-ai` per-process (don't delete). |

## Configuration

`gv` reads config from the environment or `~/.jstack/config.env`:
- Project (billed): `GOOGLE_CLOUD_PROJECT` (or `GEMINI_VISION_PROJECT` to pin) — **required, no default**.
- Location: `GOOGLE_CLOUD_LOCATION` — default `us-central1`.
- Model: `GEMINI_VISION_MODEL` — default `gemini-2.5-pro` (flash may not be reachable via the CLI — see AGENTS.md).

```bash
# ~/.jstack/config.env, or inline:
GEMINI_VISION_PROJECT=your-gcp-project gv -p "..." @file.png
GOOGLE_CLOUD_LOCATION=europe-west4 gv -p "..." @file.png
GEMINI_VISION_MODEL=gemini-2.5-pro gv -p "..." @file.png
```

## Why

- **Official Google CLI**, no third-party npm packages.
- **Vertex AI** mode charges the GCP project's billing account (uses credits).
- **Cached OAuth** — no API key, no `gcloud` install.
- **Generic** — no domain vocabulary; any agent can call it.

## See also

- `vision` skill — the agent skill that documents when to use `gv`.
