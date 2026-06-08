# AGENTS.md — operational contract for `gv` / `gv-pro` / `gv-batch`

Generic Gemini multimodal wrapper. No domain vocabulary, no industry-specific
defaults. Caller supplies the prompt and the files.

## Auth model

- **Vertex AI** mode (`GOOGLE_GENAI_USE_VERTEXAI=true`)
- Cached OAuth (ADC, `authorized_user`) — no API key, no `gcloud` install
- Billing charged to the project's billing account (consumes GCP credits)

**Critical: forcing Vertex headlessly.** Setting `GOOGLE_GENAI_USE_VERTEXAI=true`
is **not sufficient**. In non-interactive mode the gemini CLI resolves auth as
`effectiveAuthType = settings.security.auth.selectedType || getAuthTypeFromEnv()`.
A global `~/.gemini/settings.json` with `selectedType: "oauth-personal"`
(free **Gemini Code Assist** / "Gemini for Google Cloud API") is truthy, so the
env is ignored and calls route to the **free tier** — not Vertex. The free tier
starves non-flash models ("You have exhausted your capacity… quota will reset
after Xh").

`gv` fixes this **per-process** by exporting
`GEMINI_CLI_SYSTEM_SETTINGS_PATH=<dir>/gemini-vertex-settings.json`, a tiny file
that sets `selectedType: "vertex-ai"` (system settings override user settings in
the merge). This forces Vertex for `gv` only — interactive `gemini` stays on the
free Code Assist tier. Don't delete `gemini-vertex-settings.json`.

## Defaults (env-overridable; config via `~/.jstack/config.env`)

| Var | Default | Purpose |
|---|---|---|
| `GEMINI_VISION_PROJECT` | *(required, no default)* | GCP project billed (credits). Set as `GOOGLE_CLOUD_PROJECT` for the CLI; pinned so the shell's ambient `GOOGLE_CLOUD_PROJECT` can't hijack billing. `GOOGLE_CLOUD_PROJECT` is used if this is unset. |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Vertex AI region |
| `GEMINI_VISION_MODEL` | `gemini-2.5-pro` | Model for `gv` (see Models — flash may not be reachable via the CLI) |
| `GEMINI_CLI_SYSTEM_SETTINGS_PATH` | `<dir>/gemini-vertex-settings.json` | Forces `selectedType=vertex-ai` for this process only (see Auth model) |
| `GEMINI_CLI_TRUST_WORKSPACE` | `true` | Trust cwd non-interactively (required by CLI >=0.45) |
| `GV_BATCH_SLEEP` | `4` | Seconds between `gv-batch` calls |

## Models

| Alias | Model | Notes |
|---|---|---|
| `gv` (default) | `gemini-2.5-pro` | **Confirmed working on Vertex/credits.** Default because flash may be unreachable via the CLI (below). |
| `gv-pro` | `gemini-2.5-pro` | Same as the default now. Kept for explicitness. |
| override | `gemini-2.5-flash` | **May not be reachable via the CLI.** gemini-cli 0.45 hard-remaps any flash request to `gemini-3.x-flash` (`DEFAULT_GEMINI_FLASH_MODEL`); a project without that grant gets `404 ModelNotFound`. Re-enable once a gemini-3.x-flash is granted, or call flash via the google-genai SDK directly. |
| override | `gemini-2.5-flash-image` | "Nano Banana", image gen + analyze (untested) |

Probe which models the project can reach (no `gcloud` required):
```bash
for m in gemini-2.5-pro gemini-2.5-flash; do gv -m "$m" -p "say OK"; done
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
| "exhausted your capacity… quota will reset after Xh" | Calls hit the **free Code Assist tier**, not Vertex — i.e. `GEMINI_CLI_SYSTEM_SETTINGS_PATH` isn't forcing `vertex-ai` (or you ran `gemini` directly). The free tier starves non-flash models. | Use `gv` (it forces Vertex). For a raw `gemini` call, export `GEMINI_CLI_SYSTEM_SETTINGS_PATH=<dir>/gemini-vertex-settings.json` + `GOOGLE_GENAI_USE_VERTEXAI=true` + project/location. |
| `404 ModelNotFound: publishers/google/models/gemini-3-flash` | CLI remapped a flash request to `gemini-3.x-flash`, which the project can't access | Use `gemini-2.5-pro` (the default). Flash may not be reachable via the CLI. |
| 404 / other model not found | Wrong model name or wrong region | Check spelling; some models aren't in all regions. |
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
skills may call it from their own SKILL.md instructions (e.g., an adscan
skill could say "use `gv` for vision analysis"). Keep such couplings opt-in
and minimal.
