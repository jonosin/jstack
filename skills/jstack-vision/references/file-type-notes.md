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

## Video & audio: when to use Flash vs Pro

`gemini-2.5-flash` handles all modalities competently. Use Pro only when:
- Long video (>30 min) where Flash's context summarization loses detail
- Dense technical audio (e.g., legal deposition) where exact wording matters
- PDF with complex tables/charts where Flash misreads

## Model availability for the project

```bash
gcloud ai models list --region="$GOOGLE_CLOUD_LOCATION" --project="$GOOGLE_CLOUD_PROJECT"
```

Or via the Vertex AI console: GCP tab → Vertex AI → Model Garden.

**Notes:**
- `gemini-2.5-flash` is the verified default — works end-to-end.
- `gemini-2.5-pro` may return "exhausted your capacity" if your project has no
  provisioned quota; request it in the GCP console.
- Newer flagships (`gemini-3.1-pro`) depend on your project's model access.

## CLI startup bug (FIXED)

The `gemini` CLI v0.34.0 crashed at startup on non-flash models with
`TypeError: resolved.startsWith is not a function` (`isCustomModel` loading
built-in agents). This is **fixed** — the CLI was upgraded to 0.45.2 via
`brew upgrade gemini-cli` (upstream issue google-gemini/gemini-cli#23934,
confirmed resolved). Non-flash models now start cleanly.

Note CLI >=0.45 added a "trusted directory" gate; `gv` sets
`GEMINI_CLI_TRUST_WORKSPACE=true` so headless calls work.

## If 2.5-pro is critical (no quota workaround)

The remaining blocker is Vertex quota, not the CLI. Either:

1. Request `gemini-2.5-pro` quota for the project in the GCP console
   (Vertex AI → Quotas), then `gv-pro` works as-is.
2. Or call the Python SDK directly (Vertex AI + cached OAuth) once quota exists:
   ```python
   from google import genai
   client = genai.Client(vertexai=True, project="...", location="us-central1")
   response = client.models.generate_content(
       model="gemini-2.5-pro",
       contents=[prompt, image],
   )
   ```
