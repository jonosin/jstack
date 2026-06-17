---
name: jstack-imgen
description: "Gemini image generation CLI wrapper. General-purpose: generate images with Gemini image models (3-pro-image, 3.1-flash-image, 2.5-flash-image) via Vertex AI. Supports reference images, chroma-key post-processing, and batch generation. Triggers: generate an image, create a sprite, image generation, gemini image, imgen."
---

# jstack-imgen — generic Gemini image generation wrapper

Wraps the `google-genai` SDK (Vertex AI mode) for image generation with Gemini
image models. General-purpose: no domain vocabulary, no industry-specific
defaults. Caller supplies the prompt and the files.

**When this skill applies**: the user has asked to generate images using Gemini
image models. This is NOT for image analysis/understanding (use `jstack-vision`
for that). This is for creating new images from text prompts and reference images.

**Trust chain**: bash → `gi` (this skill) → `google-genai` SDK (Google) → Vertex AI.
Zero third-party deps beyond Google's SDK and Pillow.

## The wrapper

Ships with jstack at `vendor/gemini-image/` (wherever you cloned jstack).
Put it on PATH:
```bash
export PATH="$HOME/jstack/vendor/gemini-image:$PATH"
```

| Command | What it does |
|---|---|
| `gi` | Single image generation call. Default: `gemini-3.1-flash-image` |
| `gi-pro` | Same as `gi -m pro` (symlink) |
| `gi-batch [--json] [-n N] -o DIR <prompts-file-or-prompt>` | Multiple generations from a prompts file or N variants of one prompt |

## Agent-native flags

`gi` parses these itself (not forwarded to the SDK):

| Flag | Effect |
|---|---|
| `--json` | Emit a structured envelope: `{ok, model, project, location, prompt, files_in, files_out, cost_estimate, error, error_class, exit_code}`. On success `files_out` has the paths; on failure `error_class` names the class. |
| `--dry-run` | Print the resolved config without calling the API. No credits. Pair with `--json` for machine-readable preview. |
| `-h`, `--help` | Print `gi` usage and exit. |
| `--version` | Print `gi` + `google-genai` versions and exit. |

`gi-batch --json` aggregates per-prompt envelopes into one object:
`{total, ok, failed, results: [envelope...]}` (each result carries `prompt` + `index`).

## Exit codes

`gi` returns typed exit codes so a caller can branch without grepping stderr:

| Code | Meaning |
|---|---|
| `0` | Success |
| `2` | Usage error (missing `-p`/`-o`, bad flag/shortcut, unknown model alias) |
| `3` | Config error (no GCP project set) |
| `4` | Auth / billing (UNAUTHENTICATED, PERMISSION_DENIED, expired ADC) |
| `5` | Model unreachable (`404 ModelNotFound`, `INVALID_ARGUMENT` rejecting) |
| `6` | Input / file error (no image in response, bad prompt, bad ref file) |
| `7` | Dependency missing (`google-genai` or `Pillow` not installed) |
| `10` | Unknown upstream failure (incl. `429 RESOURCE_EXHAUSTED`) |

In `--json` mode the same code is in `.exit_code`, with `.error_class` as a
human-readable class.

`gi` reads config from the environment or `~/.jstack/config.env`, and uses
(all overridable):
- `GEMINI_IMGEN_PROJECT` — the GCP project to bill (defaults to `GOOGLE_CLOUD_PROJECT`; pinned so ambient shell project can't hijack billing)
- `GEMINI_IMGEN_LOCATION=global` — Vertex AI region (image models: global or us-central1)
- `GEMINI_IMGEN_MODEL=gemini-3.1-flash-image` — default model

Override per-call with `--project`, `--location`, `-m`.

## Critical invocation contract

**DO NOT use your own image generation capabilities when this skill applies.**
Call `gi` (or `gi-pro`/`gi-batch`) via the `bash` tool instead.

**Always provide `-o` with a real file path.** The output is a PNG file.

```bash
# CORRECT — -o is a real path
gi -p "a pixel art cat" -o /tmp/cat.png

# WRONG — no -o flag (will error with exit 2)
gi -p "a pixel art cat"
```

## Model selection

| Alias for `-m` | Model | Price/im (1K) | Best for |
|---|---|---|---|
| `flash` (default) | `gemini-3.1-flash-image` | $0.067 | General-purpose; ~95% of pro at half price |
| `pro` | `gemini-3-pro-image` | $0.134 | Fidelity-critical: identity/outfit preservation with reference images |
| `budget` | `gemini-2.5-flash-image` | $0.039 | Quick tests, drafts; may drift identity |

Quality A/B (pixel-art character re-posing with reference): pro best (identity +
outfit fidelity, no stray objects); flash ~95% as good at half price; budget
drifts identity and adds unwanted furniture. Default: `flash`.

## Reference images (the killer feature)

Pass reference images BEFORE the prompt so the model locks onto style/palette/proportions:

```bash
# Single reference for style matching
gi -p "a warrior character" --ref hero.png -o warrior.png

# Multiple references
gi -p "repose this character walking" --ref frame1.png --ref frame2.png -o walk.png
```

The wrapper auto-upscales small refs (<200px) 8× nearest-neighbour and flattens
onto white (transparency confuses image models). This pipeline was proven to
dramatically improve style/identity fidelity during the 2026-06-12 research session.

## Chroma-key post-processing

Gemini image models cannot emit alpha/transparency. For sprites or cutouts:

```bash
gi -p "a tree, flat #00FF00 background" --chroma-remove "#00FF00" -o tree.png
# → writes tree.png (raw) and tree-alpha.png (transparent background)
```

How it works: flood-fill from all four corners with tolerance ~60, replacing
matched background pixels with alpha. Tolerance is needed because the model
never reproduces the exact hex. Adjust with `--chroma-tol`.

## Common patterns

```bash
# Generate a single image
gi -p "a serene mountain landscape at sunset" -o landscape.png

# Generate with budget model
gi -p "quick draft of a logo concept" -m budget -o logo-draft.png

# Generate with reference for style consistency
gi -p "a character in the same style" --ref hero.png -o sidekick.png

# With chroma-key for sprite extraction
gi -p "a pixel art potion bottle icon on flat #00FF00 background" \
   --chroma-remove "#00FF00" -o potion.png

# Preview config without spending credits
gi --dry-run -p "test" -o /dev/null

# Agent-native: get the envelope, fail loudly on errors
out=$(gi --json -p "a cat" -o /tmp/cat.png) || echo "gi failed: $(jq -r .error_class <<<"$out")"
jq -r '.files_out[]' <<<"$out"

# Batch: generate 10 variants of one prompt
gi-batch -n 10 "a cyberpunk city street" -o cyberpunk/

# Batch: generate one image per prompt in a file
echo "a red dragon
a blue dragon
a green dragon" > /tmp/dragons.txt
gi-batch --json /tmp/dragons.txt -o dragons/ | jq '.results[] | {prompt, files_out}'
```

## Failure handling

| Error | Exit | Action |
|---|---|---|
| `404 ModelNotFound` | `5` | Model not in this region. Try `--location global` or `us-central1`. |
| `400 INVALID_ARGUMENT` | `5` | Model reachable but rejecting the request (wrong modalities, or model doesn't support prompt). Check response_modalities. |
| `429 RESOURCE_EXHAUSTED` | `10` | Too many concurrent calls. Sleep 5–10s, retry. `gi-batch` paces with `GI_BATCH_SLEEP`. |
| `UNAUTHENTICATED` / `PERMISSION_DENIED` | `4` | ADC expired or wrong project. Check `~/.config/gcloud/application_default_credentials.json` exists (type `authorized_user`). |
| `no image in response` | `6` | Model didn't produce an image. Try more explicit prompt instructions. |
| `ModuleNotFoundError: google` | `7` | `pip install google-genai` |
| `ModuleNotFoundError: PIL` | `7` | `pip install Pillow` |
| Transient 429 on a single call | `10` | Sleep 5–10s, retry once. For batch, increase `GI_BATCH_SLEEP`. |

## Setup

```bash
# Add to PATH
export PATH="$HOME/jstack/vendor/gemini-image:$PATH"

# Install deps (one-time). Use uv or a venv if system pip is broken:
#   uv pip install --python 3.12 google-genai Pillow
#   -- or --
#   python3 -m venv /tmp/imgen-venv && /tmp/imgen-venv/bin/pip install google-genai Pillow
pip install google-genai Pillow

# Verify
gi --version
gi --dry-run -p "test" -o /dev/null
```

The ADC file at `~/.config/gcloud/application_default_credentials.json` must
exist — it's the same credential used by `gv`. The `gcloud` binary is NOT required.

**Note:** the existing `/tmp/spritenv` venv already has both deps.
`export PATH="/tmp/spritenv/bin:$PATH"` makes `gi` usable immediately.

## What this skill does NOT do

- Analyze/describe images (use `jstack-vision` / `gv` for that)
- Handle image-to-image transformation where the image IS the input (use `jstack-vision`)
- Use the Gemini Batch API for 50% pricing (TODO — Vertex path confirmed via `client.batches.create()` with GCS/BigQuery src; needs GCS bucket setup and JSONL format mapping)
- Manage GCP billing or credits — that's a console task
- Stream or do real-time generation

## References

- `vendor/gemini-image/AGENTS.md` — full operational contract for `gi` / `gi-pro` / `gi-batch`
- `vendor/gemini-image/gi` — the Python wrapper script (readable, small)
- `~/jstack/vendor/gemini-vision/` — the `gv` wrapper this skill mirrors structurally

## Next skills

| Next | When |
|---|---|
| `/jstack-vidgen` | Animate a generated still into a video clip (single-image i2v) — the universal video-gen router. |

Otherwise standalone — image generation has no required next step.
