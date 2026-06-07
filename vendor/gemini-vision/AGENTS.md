# AGENTS.md — operational contract for `gv` / `gv-pro` / `gv-batch`

Generic Gemini multimodal wrapper. No domain vocabulary, no industry-specific
defaults. Caller supplies the prompt and the files.

## Auth model

- **Vertex AI** mode (`GOOGLE_GENAI_USE_VERTEXAI=true`)
- Cached OAuth credentials (no API key, no `gcloud` install)
- Billing charged to the project's billing account (consumes GCP credits)

## Defaults (env-overridable; config via `~/.jstack/config.env`)

| Var | Default | Purpose |
|---|---|---|
| `GOOGLE_CLOUD_PROJECT` | *(required)* | Your GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Vertex AI region |
| `GEMINI_VISION_MODEL` | `gemini-2.5-flash` | Model for `gv` |
| `GEMINI_CLI_TRUST_WORKSPACE` | `true` | Trust cwd non-interactively (required by CLI >=0.45) |
| `GV_BATCH_SLEEP` | `4` | Seconds between `gv-batch` calls |

## Models

Any model accepted by the `gemini` CLI's `-m` flag. Canonical:

| Alias | Model | Notes |
|---|---|---|
| `gv` (default) | `gemini-2.5-flash` | Fast, multimodal, default choice. Verified working. |
| `gv-pro` | `gemini-2.5-pro` | Deeper reasoning. If your project has **no Vertex capacity/quota** for 2.5-pro it returns "exhausted your capacity" — request quota in the GCP console before relying on it. |
| override | `gemini-3.1-pro` | Newest flagship, strongest reasoning |
| override | `gemini-2.5-flash-image` | "Nano Banana", image gen + analyze |

List available models for the project:
```bash
gcloud ai models list --region="$GOOGLE_CLOUD_LOCATION" --project="$GOOGLE_CLOUD_PROJECT"
```

## File types supported

| Type | Extensions |
|---|---|
| Image | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` |
| Audio | `.mp3`, `.wav`, `.ogg`, `.flac`, `.aac`, `.opus`, `.m4a` |
| Video | `.mp4`, `.mov`, `.mkv`, `.webm`, `.avi`, `.flv` |
| Document | `.pdf` |

`gv-batch` globs all of the above. Other extensions: pass the file path
explicitly to `gv`.

## Reference syntax in prompts

**`@` must be inside the `-p` prompt string**, not a separate arg. The gemini
CLI parses `@file` as a file reference inside the prompt body.

```bash
# CORRECT — @file is inside the -p string
gv -p "describe @pic1.png and @pic2.png"

# WRONG — @file as a separate arg dumps the help text
gv -p "describe" @pic1.png
```

**Always `cd` to the file's directory first**, then reference files by
basename. `gv` automatically passes `--include-directories $(pwd)`, so the
model can resolve basenames against the workspace.

```bash
cd ~/shots
gv -p "describe @pic1.png"
```

**Avoid `@/absolute/path/to/file.png`** — the CLI may report "I cannot locate
the file" because absolute paths are resolved relative to the included
directories, not the filesystem root.

## Video: keyframe fallback

`gemini` CLI's `read_file` officially supports "text, images, audio, and
PDF" — video is not listed. Two paths:

1. **Pass video directly** (preferred for short clips):
   ```bash
   gv -p "describe what happens" @clip.mp4
   ```
   Works for many cases but not guaranteed.

2. **Extract keyframes first** (always works):
   ```bash
   ffmpeg -i clip.mp4 -vf "fps=1" /tmp/frames_%04d.jpg
   cd /tmp && gv -p "describe the sequence across @frames_0001.jpg, @frames_0002.jpg, etc."
   ```
   Loses temporal information but reliable.

## Failure modes

| Error | Cause | Fix |
|---|---|---|
| "exhausted your capacity" (retries then fails) | Vertex AI quota: `gemini-2.5-pro` may have **no provisioned capacity** for your project (persistent, not a rate limit) | Use `gemini-2.5-flash`, or request 2.5-pro quota in the GCP console. Transient 429 rate limits on flash do resolve with `gv-batch`'s built-in sleep. |
| 404 / model not found | Wrong model name or wrong region | Check spelling. Some models aren't in all regions. |
| "I cannot locate the file" | `@/abs/path` in headless mode | `cd` to dir, use basename, or use `--include-directories` |
| CLI prints help text | `@file` passed as a separate arg, not inside `-p` prompt | Put `@file` inside the quoted prompt string |
| "not running in a trusted directory" | CLI >=0.45 trust gate, headless | `gv` sets `GEMINI_CLI_TRUST_WORKSPACE=true` automatically; if calling `gemini` directly, export it or pass `--skip-trust` |
| `TypeError: resolved.startsWith is not a function` on startup | `gemini` v0.34.0 bug (fixed upstream) | Upgrade: `brew upgrade gemini-cli` (need ≥0.45). |
| "gemini: command not found" | CLI not on PATH | `brew install gemini-cli` |
| "Loaded cached credentials" then auth error | OAuth token expired | Re-auth: delete `~/.config/gcloud/application_default_credentials.json` and run any `gemini` command to trigger a new OAuth flow |

## Limits (Vertex AI)

| Modality | Inline | File API |
|---|---|---|
| Image | up to ~20MB | up to 2GB |
| Audio | up to ~9.5h | up to 2GB |
| Video | up to ~1 min | up to ~1h |
| PDF | up to ~1000 pages / 20MB | up to 2GB |

For files above the inline limit, the `gemini` CLI handles the File API
upload automatically.

## Layering with other skills

`gv` is intentionally generic and not coupled to any other skill. Other
skills may call it from their own SKILL.md instructions (e.g., a future
adscan skill could say "use `gv` for vision analysis"). Keep such
couplings opt-in and minimal.
