# File type notes

Operational details for each modality `gv` supports.

## Image

**Extensions**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`

**Token cost**: depends on resolution.
- Small (~512×512): ~258 tokens
- Medium (~1024×1024): ~1,000 tokens
- Large (~4K): ~2,000+ tokens

The wrapper auto-resizes/handles large images via the File API if they exceed
inline limits (~20MB).

**Pattern**:
```bash
cd ~/shots
gv -p "describe @photo.jpg"
```

## Audio

**Extensions**: `.mp3`, `.wav`, `.ogg`, `.flac`, `.aac`, `.opus`, `.m4a`

**Token cost**: ~32 tokens per second of audio for the standard rate.
- 1 minute ≈ 2,000 tokens
- 1 hour ≈ 120,000 tokens

**Inline limit**: ~9.5 hours of audio / ~20MB. File API handles larger.

**Pattern**:
```bash
cd ~/recordings
gv -p "transcribe verbatim @meeting.mp3"
```

**Quirks**:
- Some formats (`.m4a` from iOS Voice Memos) may need conversion to `.wav` or `.mp3` for reliable handling.
- For multi-speaker audio, prompt explicitly: "label speakers as Speaker 1, Speaker 2, ...".

## Video

**Extensions**: `.mp4`, `.mov`, `.mkv`, `.webm`, `.avi`, `.flv`

**Critical quirk**: the `gemini` CLI's `read_file` officially supports
"text, images, audio, and PDF" — **video is not listed**. Two paths:

### Path 1: Pass video directly (preferred for short clips)
```bash
cd ~/clips
gv -p "what happens in @clip.mp4"
```
Works in many cases but not guaranteed. If it fails (CLI errors or returns
"I cannot analyze video"), fall back to Path 2.

### Path 2: Keyframe extraction (always works)
```bash
ffmpeg -i clip.mp4 -vf "fps=1" /tmp/frames_%04d.jpg
cd /tmp && gv -p "Describe what is happening in each frame: @frames_0001.jpg, @frames_0002.jpg, @frames_0003.jpg"
```

**Trade-off**: loses temporal information (motion, transitions) but always
reliable. Use 1 fps for most cases; 0.5 fps for longer videos to stay under
token limits.

**Token cost**: 1 fps × 60 sec = 60 frames × ~258 tokens/frame = ~15,000
tokens/minute. For a 5-minute video at 1 fps, expect ~75,000 tokens of input.

**Inline limit**: ~1 minute. File API: ~1 hour.

## PDF

**Extensions**: `.pdf`

**Capabilities**: native OCR + image extraction. Multi-page text content is
preserved with page boundaries.

**Token cost**: roughly 1 page ≈ 1,500–3,000 tokens depending on density.
- 10-page report ≈ 15,000–30,000 tokens
- 100-page report ≈ 150,000–300,000 tokens

**Inline limit**: ~1,000 pages / 20MB. File API: up to 2GB.

**Pattern**:
```bash
cd ~/documents
gv -p "summarize @report.pdf"
```

**Multi-doc pattern**:
```bash
cd ~/legal
gv -p "Compare @contract-v1.pdf and @contract-v2.pdf. What changed in the indemnification clause?"
```

## Flash vs Pro

`gv` defaults to **`gemini-2.5-pro`** because flash may not be reachable via
the CLI (see below). Pro handles all modalities well. If your project/CLI can
reach a flash model, override per-call with `GEMINI_VISION_MODEL`.

## Model availability (Vertex)

Probe via the wrapper (no `gcloud` required):
```bash
for m in gemini-2.5-pro gemini-2.5-flash; do gv -m "$m" -p "say OK"; done
```

**Observed** (CLI 0.45.2, Vertex auth forced):
- `gemini-2.5-pro` ✓ works end-to-end on Vertex, billed to GCP credits
- `gemini-2.5-flash` ✗ — `404 ModelNotFound`. The CLI hard-remaps flash to
  `gemini-3.x-flash` (`DEFAULT_GEMINI_FLASH_MODEL`), which a project without
  that grant can't access; fails in us-central1, global, and us-east5.

## How vision bills GCP credits (the auth fix)

`GOOGLE_GENAI_USE_VERTEXAI=true` alone is ignored: headless auth is
`selectedType || getAuthTypeFromEnv()`, and the global `~/.gemini/settings.json`
has `selectedType: oauth-personal` (free **Code Assist** / "Gemini for Google
Cloud API"). That truthy value wins, so calls hit the free tier — which returns
"exhausted your capacity" for non-flash models. `gv` forces Vertex per-process
via `GEMINI_CLI_SYSTEM_SETTINGS_PATH=<dir>/gemini-vertex-settings.json`
(`selectedType: vertex-ai`), leaving interactive `gemini` on the free tier.
Confirmed: traffic then lands on the **Agent Platform API** (= Vertex AI) in the
GCP console, not "Gemini for Google Cloud API".

The v0.34.0 `isCustomModel` startup crash is also fixed (upgrade to ≥0.45,
upstream #23934), and CLI >=0.45's "trusted directory" gate is handled via
`GEMINI_CLI_TRUST_WORKSPACE=true`.

## Cheap flash via the SDK (optional, if you need flash)

Pro is the working default. If flash cost matters, bypass the CLI's remap with
the google-genai SDK (same Vertex auth as `gv`):
   ```python
   from google import genai
   client = genai.Client(vertexai=True, project="...", location="us-central1")
   response = client.models.generate_content(
       model="gemini-2.5-flash",   # SDK sends it literally — no CLI remap
       contents=[prompt, image],
   )
   ```
