# Backend: Veo 3.1 on Vertex AI

The Google Veo backend. Billed to the user's **GCP credits via ADC** (not Topview credits).
Mirrors the auth/project/region conventions of `jstack-imgen` (`gi`) and `jstack-vision` (`gv`):
`google-genai` SDK in Vertex mode, ADC auth, billing project pinned via a dedicated env var,
regional location. Use this backend when the engine is **Veo 3.1** OR the user wants to spend
GCP credits instead of Topview credits.

## Model IDs

| Alias | Model ID | Notes |
|---|---|---|
| standard | `veo-3.1-generate-001` | full quality, native audio |
| fast | `veo-3.1-fast-generate-001` | cheaper/faster |
| (legacy) | `veo-3.1-generate-preview` | earlier preview id; may still resolve |

> **Verify the live model id in Model Garden before the first run.** Veo ids rotate
> (`-preview` → `-001`); a stale id 404s. Confirm in the Vertex AI Model Garden / `gcloud ai
> models` for the billing project, then pin via `GEMINI_VIDGEN_MODEL`.

## Capabilities

- **text-to-video** (t2v)
- **image-to-video** — single first frame (i2v)
- **reference images** (preview)
- **first + last frame** (distinct frames — interpolates between them)
- **video extend** (continue an existing clip)
- **prompt rewriting** (model rewrites/expands the prompt; can be disabled)

## API surface

Vertex AI via the `google-genai` SDK in **Vertex mode**:

```python
from google import genai
client = genai.Client(vertexai=True, project=PROJECT, location="us-central1")
op = client.models.generate_videos(model=MODEL, prompt=PROMPT, image=IMAGE)  # long-running op
# poll until done:
while not op.done:
    time.sleep(10)
    op = client.operations.get(op)
videos = op.response.generated_videos  # GCS URIs or inline bytes per config
```

`generate_videos(...)` returns a **long-running operation** you poll to completion (videos take
minutes). Output goes to **GCS** (set an output URI) or returns **inline bytes**, depending on
the `config`.

**REST equivalent**: `POST .../models/<model>:predictLongRunning` then poll
`.../operations/<op>:fetchPredictOperation`.

## Auth / project / region

- **ADC** at `~/.config/gcloud/application_default_credentials.json` (type `authorized_user` —
  the same credential `gi`/`gv` use; `gcloud` binary NOT required at call time).
- **Billing project pinned via env** so the ambient shell `GOOGLE_CLOUD_PROJECT` can't hijack
  billing (matches imgen's pinning):
  - `GEMINI_VIDGEN_PROJECT` — the GCP project to bill. **Defaults to `GOOGLE_CLOUD_PROJECT`.**
- **Location `us-central1`** — Veo is **regional, NOT `global`**. (imgen image models use
  `global`; Veo does not — do not copy imgen's location default.)
  - `GEMINI_VIDGEN_LOCATION` — defaults to `us-central1`.
- `GEMINI_VIDGEN_MODEL` — default model id (propose `veo-3.1-generate-001`).

Read config the jstack way: **env var → `~/.jstack/config.env` → default**.

## Pricing (verified 2026-06)

Per **output-second**, with audio:

| Tier | $/output-second | 8s clip | 3s clip |
|---|---|---|---|
| standard (`veo-3.1-generate-001`) | **$0.40** | ~$3.20 | ~$1.20 |
| fast (`veo-3.1-fast-generate-001`) | **$0.15** | ~$1.20 | ~$0.45 |

Sources: MindStudio pricing page + r/Bard corroboration (verified 2026-06). Per-second billing
makes duration the dominant cost lever — confirm `duration` before every submit (Universal Rule 1).

## Constraints

- **Aspect ratio**: 9:16 / 16:9.
- **Resolution**: 720p & 1080p.
- **Duration**: typically ~4–8s. **Verify the exact allowed set in Model Garden before the first
  run** — Veo's accepted durations are model-version specific.
- **Native audio** supported (drives the standard tier price; can be toggled).

## Ready-to-run recipe (UNTESTED — no credits spent during authoring)

Minimal `google-genai` SDK snippet, Vertex mode, **i2v from a local still**. This was NOT executed
during authoring — no GCP credits were spent. Treat it as a starting point; verify model id +
allowed durations first.

```bash
# Env it needs (set in shell or ~/.jstack/config.env):
export GEMINI_VIDGEN_PROJECT="<your-gcp-project>"   # falls back to GOOGLE_CLOUD_PROJECT
export GEMINI_VIDGEN_LOCATION="us-central1"          # Veo is regional, NOT global
# ADC must exist: ~/.config/gcloud/application_default_credentials.json (type authorized_user)
pip install google-genai        # zero third-party deps beyond Google's SDK
```

```python
# veo_i2v.py — UNTESTED reference (no credits spent during authoring)
import os, time
from google import genai
from google.genai import types

PROJECT  = os.environ.get("GEMINI_VIDGEN_PROJECT") or os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ.get("GEMINI_VIDGEN_LOCATION", "us-central1")
MODEL    = os.environ.get("GEMINI_VIDGEN_MODEL", "veo-3.1-generate-001")

client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)

# Load the local first frame. (Veo also accepts a GCS URI via Image(gcs_uri=...).)
image = types.Image.from_file(location="still.png")          # first frame for i2v

op = client.models.generate_videos(
    model=MODEL,
    prompt="<single-start motion block — see video-prod-skills:cinematic-motion-language>",
    image=image,
    config=types.GenerateVideosConfig(
        aspect_ratio="9:16",        # 9:16 | 16:9
        resolution="1080p",         # 720p | 1080p
        duration_seconds=8,         # verify allowed set first (~4–8s)
        number_of_videos=1,
        generate_audio=True,        # native audio (standard tier)
        # output_gcs_uri="gs://<bucket>/veo/",  # optional: write to GCS instead of inline bytes
    ),
)

# Long-running op — poll to completion (minutes).
while not op.done:
    time.sleep(10)
    op = client.operations.get(op)

for i, gv in enumerate(op.response.generated_videos):
    gv.video.save(f"out_{i}.mp4")   # inline bytes; if output_gcs_uri set, read the URI instead
    print("wrote", f"out_{i}.mp4")
```

A CLI scaffold mirroring imgen's `gi` shape ships at `scripts/veo_gen.py` (dry-run works without
spending credits; the live submit path is a clearly-marked TODO). See its `--help` / `--dry-run`.

## Failure handling (expected classes, mirrors imgen)

| Error | Likely cause | Action |
|---|---|---|
| `404 ModelNotFound` | stale/region-wrong model id | verify id in Model Garden; confirm `location=us-central1` |
| `UNAUTHENTICATED` / `PERMISSION_DENIED` | ADC expired / wrong project | check `~/.config/gcloud/application_default_credentials.json`; confirm `GEMINI_VIDGEN_PROJECT` |
| `INVALID_ARGUMENT` | bad duration/resolution/aspect for this model | check allowed set in Model Garden |
| `429 RESOURCE_EXHAUSTED` | quota | wait, retry; request quota in console |
