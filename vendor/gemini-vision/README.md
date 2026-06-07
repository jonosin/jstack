# gv — Gemini Vision (generic multimodal)

Generic wrapper around Google's official [`gemini` CLI][cli] for calling
Gemini models via Vertex AI. Works on images, audio, video, and PDFs.

[cli]: https://github.com/google-gemini/gemini-cli

## Install

Already installed if you have:
- `gemini` CLI on PATH (`brew install gemini-cli`)
- Cached GCP OAuth credentials

The scripts in this directory are drop-in. Add this directory to `PATH`
(adjust to wherever you cloned jstack):
```bash
export PATH="$HOME/jstack/vendor/gemini-vision:$PATH"
```

## Quick start

```bash
# Image
gv -p "describe this" @~/pic.jpg

# Pro model (needs 2.5-pro Vertex quota on the project — see AGENTS.md)
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

## Files

| File | Purpose |
|---|---|
| `gv` | Main wrapper. Defaults to `gemini-2.5-flash`, your `GOOGLE_CLOUD_PROJECT`, `us-central1`. |
| `gv-pro` | Same but `gemini-2.5-pro`. |
| `gv-batch` | Loops a directory of media files, calls `gv` per file. |
| `AGENTS.md` | Operational contract: env vars, models, failure modes, limits. |

## Configuration

`gv` reads config from the environment or `~/.jstack/config.env`:
- Project: `GOOGLE_CLOUD_PROJECT` — **required**, set to your own GCP project.
- Location: `GOOGLE_CLOUD_LOCATION` — default `us-central1`.
- Model: `GEMINI_VISION_MODEL` — default `gemini-2.5-flash`.

```bash
# ~/.jstack/config.env, or inline:
GOOGLE_CLOUD_PROJECT=your-gcp-project gv -p "..." @file.png
GOOGLE_CLOUD_LOCATION=europe-west4 gv -p "..." @file.png
GEMINI_VISION_MODEL=gemini-3.1-pro gv -p "..." @file.png
```

## Why

- **Official Google CLI**, no third-party npm packages.
- **Vertex AI** mode charges the GCP project's billing account (uses credits).
- **Cached OAuth** — no API key, no `gcloud` install.
- **Generic** — no domain vocabulary; any agent can call it.

## See also

- `jstack-vision` skill — the agent skill that documents when to use `gv`.
