# Backend: Veo 3.1 on Vertex AI

> **RUN-FIRST. The script works — do NOT read it before running.** `scripts/veo_gen.py`'s
> live i2v/t2v submit path is implemented and tested. To generate a clip, copy the recipe
> below and run it. Do **not** read the Python, re-derive the SDK call, or grep for
> conventions first — everything you need is in this top section. Drop to "Debug — read only
> if a run fails" (bottom) ONLY after a real failure, then fix the root cause and update this
> doc + the script so the next agent doesn't hit it.

## ▶ Generate a Veo clip (copy-paste, no script-reading needed)

```bash
# i2v from a local still — DEFAULT iterate tier (Veo 3.1 Fast). Validate first, then submit.
PY=~/.jstack/imgen-venv/bin/python
SCRIPT=~/.claude/skills/jstack-vidgen/scripts/veo_gen.py

# 1. DRY-RUN first — validates config + billing project + cost, spends NOTHING:
GEMINI_VIDGEN_MODEL=veo-3.1-fast-generate-001 "$PY" "$SCRIPT" --dry-run --json \
  --prompt "<single-start motion block — see video-prod-skills:cinematic-motion-language>" \
  --first-frame still.png \
  --duration 4 --resolution 1080p --aspect-ratio 9:16 -o out.mp4

# 2. Real submit (drop --dry-run). Spends GCP credits. Confirm cost with the human first:
GEMINI_VIDGEN_MODEL=veo-3.1-fast-generate-001 "$PY" "$SCRIPT" --json \
  --prompt "<...>" --first-frame still.png \
  --duration 4 --resolution 1080p --aspect-ratio 9:16 -o out.mp4
```

- **t2v** (no still): omit `--first-frame`.
- **first-and-last-frame** (interpolate a hard transition, e.g. day→night): add `--last-frame end.png`
  alongside `--first-frame start.png`. Veo generates the transition between the two frames. Both
  frames should share aspect ratio/composition. See `prompt-guides/veo-3.1-prompt-guide.md`.
- `--json` emits a `{ok, model, project, cost_estimate, files_out, exit_code, ...}` envelope.
- **Standard quality** (final/hero clip): drop the `GEMINI_VIDGEN_MODEL` override (default is
  `veo-3.1-generate-001`) or set it to that id explicitly.

### Conventions baked in (so nobody greps for these again)

| Convention | Value |
|---|---|
| **Default iterate tier** | **Veo 3.1 Fast** (`veo-3.1-fast-generate-001`, ~$0.15/output-sec). Use it for all iteration. |
| Standard tier | `veo-3.1-generate-001`, ~$0.40/output-sec — reserve for the final/hero clip. |
| **Fast min duration** | **~4s** — 3s is rejected (`INVALID_ARGUMENT`). |
| Cost @ Fast | 4s ≈ **$0.60**, 8s ≈ **$1.20** |
| Cost @ Standard | 4s ≈ **$1.60**, 8s ≈ **$3.20** |
| Billing project | resolves `GEMINI_VIDGEN_PROJECT` → `GOOGLE_CLOUD_PROJECT` (already set in `~/.jstack/config.env`) — usually nothing to pass. |
| ADC | `~/.config/gcloud/application_default_credentials.json` (type `authorized_user`; no `gcloud` binary needed at call time). |
| Region | **`us-central1`** — Veo is regional, NOT `global` (don't copy imgen's `global` default). |
| Venv | `~/.jstack/imgen-venv/bin/python` (homebrew python3 is broken on this machine). |

**Pipeline note:** in the StayFrame reel pipeline the agent renders the clip with this script,
then the **human drag-drops the mp4 onto the beat at GATE B** in the dashboard — the dashboard
does not call Veo itself.

---

## Debug — read only if a run fails / you're debugging

Everything below is theory + raw SDK. You do **not** need it to generate a clip; it's here so
that when a run genuinely fails you can diagnose, fix the root cause, and update this doc.

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

## Raw SDK shape (internals — `veo_gen.py` already does this for you)

The `scripts/veo_gen.py` `generate()` body implements exactly this. You do NOT need to call the
SDK directly — run the CLI recipe at the top. This snippet is here for debugging the script.

```python
# equivalent of what veo_gen.py generate() does
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

The CLI at `scripts/veo_gen.py` (mirrors imgen's `gi` shape) wraps all of the above — its live
submit path is implemented and tested. `--dry-run` validates config + cost without spending. See
its `--help`. Use the top-of-file recipe to run it; you should not need to read its source.

## Failure handling (expected classes, mirrors imgen)

| Error | Likely cause | Action |
|---|---|---|
| `404 ModelNotFound` | stale/region-wrong model id | verify id in Model Garden; confirm `location=us-central1` |
| `UNAUTHENTICATED` / `PERMISSION_DENIED` | ADC expired / wrong project | check `~/.config/gcloud/application_default_credentials.json`; confirm `GEMINI_VIDGEN_PROJECT` |
| `INVALID_ARGUMENT` | bad duration/resolution/aspect for this model | check allowed set in Model Garden |
| `429 RESOURCE_EXHAUSTED` | quota | wait, retry; request quota in console |
