# AGENTS.md — operational contract for `gi` / `gi-pro` / `gi-batch`

Generic Gemini image-generation wrapper via the google-genai SDK (Vertex AI).
No domain vocabulary — caller supplies the prompt and reference files.

## Flags (parsed by `gi`, not forwarded)

| Flag | Effect |
|---|---|
| `-p`, `--prompt TEXT` | Generation prompt (required) |
| `-o`, `--out PATH` | Output PNG file path (required) |
| `-m`, `--model` | Model alias (`flash`, `pro`, `budget`) or full gemini-... ID. Default: `gemini-3.1-flash-image` |
| `--ref PATH` | Reference image(s) passed before the prompt. Repeatable. Small refs (<200px) are auto-upscaled 8× nearest-neighbour. |
| `--project ID` | GCP project (overrides config) |
| `--location REGION` | Vertex AI location (default: global) |
| `--chroma-remove HEX` | Post-process: flood-fill background from corners → alpha. e.g. `#00FF00` |
| `--chroma-tol N` | Chroma tolerance (default: 60) |
| `--json` | Emit structured JSON envelope |
| `--dry-run` | Print resolved config; do not call (no billing) |
| `-h`, `--help` | Print usage and exit |
| `--version` | Print `gi` + google-genai versions and exit |

`gi-batch [--json] [-n N] -o DIR <prompts-file-or-prompt>`
- File mode: one prompt per line, blank/# lines skipped.
- Variant mode (`-n N`): generate N variants of a single prompt.
- `--json` emits `{total, ok, failed, results: [envelope...]}`; each result carries `prompt`, `index`.

## Exit codes

| Code | Class | Trigger |
|---|---|---|
| `0` | — | success |
| `2` | usage | missing `-p`/`-o`, bad flag, unknown model alias |
| `3` | config | no GCP project set |
| `4` | auth | UNAUTHENTICATED, PERMISSION_DENIED, 403 |
| `5` | model | 404 ModelNotFound, INVALID_ARGUMENT (model rejecting) |
| `6` | input | no image in response, bad request |
| `7` | dep | google-genai or Pillow not installed |
| `10` | unknown | any other failure, including 429 RESOURCE_EXHAUSTED |

`gi-batch`: `0` all ok, `2` usage, `3` file not found, `1` ≥1 failure (human mode).
`--json` mode always exits `0` and reports failures via `failed` count.

## Auth model

- **google-genai SDK** with `vertexai=True`
- Application Default Credentials at `~/.config/gcloud/application_default_credentials.json`
  (type `authorized_user`; no `gcloud` binary needed)
- Billing charged to the GCP project's billing account (consumes GCP credits)

**Why not the `gemini` CLI.** The CLI always attaches function-calling tools; image models
reject those with `400: model does not support function calling`. This wrapper uses the SDK
directly.

## Defaults (env-overridable; config via `~/.jstack/config.env`)

| Var | Default | Purpose |
|---|---|---|
| `GEMINI_IMGEN_PROJECT` | *(from `GOOGLE_CLOUD_PROJECT`)* | GCP project billed (credits). Pinned so the shell's ambient `GOOGLE_CLOUD_PROJECT` can't hijack billing. |
| `GEMINI_IMGEN_LOCATION` | `global` | Vertex AI region (image models: global or us-central1) |
| `GEMINI_IMGEN_MODEL` | `gemini-3.1-flash-image` | Default generation model |
| `GI_BATCH_SLEEP` | `4` | Seconds between `gi-batch` calls |

## Models

| Alias | Model ID | Price/img (1K) | Location | Notes |
|---|---|---|---|---|
| `pro` | `gemini-3-pro-image` | $0.134 | **global only** | Best fidelity; identity/outfit fidelity with refs |
| `flash` (default) | `gemini-3.1-flash-image` | $0.067 | **global only** | ~95% as good as pro at half price |
| `budget` | `gemini-2.5-flash-image` | $0.039 | us-central1 & global | Drifts identity; adds unwanted details |

Probe which models the project can reach:
```bash
for alias in flash pro budget; do
  gi --dry-run -m "$alias" -p "test" -o /dev/null 2>&1 | grep model:
done
```

## Model behavior gotchas

- `response_modalities=["TEXT","IMAGE"]` is required.
- Image models (pro, flash) emit **interleaved thinking text and sometimes interim images**;
  the final inline-data part is the real output — `gi` takes the last, not the first.
- Gemini image models **cannot emit alpha/transparency**. For sprites: request a flat
  chroma-key background and use `--chroma-remove` to flood-fill it out (tolerance ~60).
- Parallel calls rate-limit fast: 3 concurrent → one 429s. Use `gi-batch` with sleep,
  or serialize.
- Reference images: for small/pixel sources, `gi` auto-upscales 8× nearest-neighbour
  and flattens onto white.

## Reference image handling

Reference images are passed **before** the prompt in `contents[]`, which gives the model
style/identity context. The pipeline:
1. Load ref as RGBA
2. If width < 200px: upscale 8× nearest-neighbour (models lock onto palette/proportions
   much better at higher resolution)
3. Flatten onto opaque white (transparency confuses the model)
4. Append the prompt text as the final content part

## Chroma-key post-processing (`--chroma-remove`)

Since image models cannot emit alpha, the workaround is:
1. Prompt the model to draw on a flat chroma-key background (e.g. "EXACT hex #00FF00")
2. `--chroma-remove "#00FF00"` flood-fills from all four corners with tolerance ~60,
   replacing matched pixels with transparency

The output file gets `-alpha.png` suffix (e.g. `sprite.png` → `sprite-alpha.png`).

## Dependencies

- **google-genai** SDK: `pip install google-genai`
- **Pillow**: `pip install Pillow`

The ADC file at `~/.config/gcloud/application_default_credentials.json` must exist
(type `authorized_user`). The `gcloud` binary is NOT required.

## Setup

```bash
# Add to PATH
export PATH="$HOME/jstack/vendor/gemini-image:$PATH"

# One-time install
pip install google-genai Pillow

# Verify
gi --version
gi --dry-run -p "test" -o /dev/null
```

## Envelope (--json)

```json
{
  "ok": true,
  "model": "gemini-3.1-flash-image",
  "project": "your-gcp-project-id",
  "location": "global",
  "prompt": "a pixel art cat",
  "files_in": ["ref.png"],
  "files_out": ["out.png"],
  "cost_estimate": 0.067,
  "error": null,
  "error_class": null,
  "exit_code": 0
}
```

## Failure modes

| Error | Cause | Fix |
|---|---|---|
| `404 ModelNotFound` | Model not in this region | Try `--location global` or `us-central1` |
| `400 INVALID_ARGUMENT` on model reachable | Wrong `response_modalities` or model rejecting prompt | Check model supports IMAGE output |
| `429 RESOURCE_EXHAUSTED` | Too many concurrent calls | Sleep 5–10s, retry; use `gi-batch` with `GI_BATCH_SLEEP` |
| `UNAUTHENTICATED` / `PERMISSION_DENIED` | ADC expired or wrong project | Check `~/.config/gcloud/application_default_credentials.json` exists; verify project has billing |
| `no image in response` | Prompt didn't produce an image | Check prompt; try more explicit instructions |
| `ModuleNotFoundError: google` | SDK not installed | `pip install google-genai` |
| `ModuleNotFoundError: PIL` | Pillow not installed | `pip install Pillow` |

## Batch API (TODO — not implemented)

Research confirmed (2026-06-12): Vertex AI Batch Prediction is accessible via
`client.batches.create()` in the google-genai SDK, with either BigQuery (`bq://`)
or GCS (`gs://`) as input source. This is the path that works with ADC/Vertex auth.
Image output is limited to 1K resolution in batch mode. Pricing is 50% off real-time.

The Gemini Developer API batch path (JSONL upload) requires an API key and is NOT
compatible with our ADC/Vertex setup.

Implementation needs:
- GCS bucket setup (or BigQuery dataset) for input/output
- JSONL input format mapping for image generation requests
- `gi-batch-api` command to submit and poll batch jobs

When implemented, add `gi-batch-api` as a separate command.

## Layering with other skills

`gi` is intentionally generic. Other skills/scripts may call it for image
generation. Keep couplings opt-in and minimal.
