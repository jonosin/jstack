# Prompt patterns

Generic, modality-agnostic prompt shapes for `gv`. Pick the one that fits
the caller's question; rewrite it for the specific case. Do not pre-fill
with domain vocabulary (ad creative, medical, legal, etc.) — let the
caller add the domain framing.

## Image

**Describe**
```
Describe @<file> in detail. Include visible objects, text, layout, colors, and any apparent context.
```

**OCR / extract text**
```
Extract all visible text from @<file>. Return verbatim, preserving order and line breaks.
```

**Count**
```
Count the number of <thing> in @<file>. Reply with just the integer.
```

**Identify**
```
What is <object> in @<file>? Reply with the name and a one-sentence explanation.
```

**Classify**
```
Classify @<file> into one of: <A>, <B>, <C>. Reply with just the letter.
```

**Compare two images**
```
Compare @<a.png> and @<b.png>. What is different? List each change.
```

**Visual Q&A**
```
@<file>
Question: <the question>
Answer in <N> sentences.
```

## Audio

**Transcribe**
```
Transcribe @<audio.mp3> verbatim. Include speaker labels if you can detect multiple speakers.
```

**Summarize**
```
Listen to @<audio.mp3> and summarize the key points in <N> bullets.
```

**Extract entities**
```
From @<audio.mp3>, extract: names, dates, numbers, locations. Return as a list.
```

**Translate**
```
Transcribe @<audio.mp3> in its original language, then translate to <target language>.
```

## Video

**Describe**
```
Describe what happens in @<video.mp4>. Include setting, subjects, actions, and any text on screen.
```

**Identify scene changes**
```
Watch @<video.mp4> and list each scene change with a timestamp (HH:MM:SS) and a one-line description of the new scene.
```

**Extract on-screen text**
```
Extract all visible text from @<video.mp4>, in order of appearance, with approximate timestamps.
```

**Action timeline**
```
From @<video.mp4>, list every distinct action in chronological order with timestamps.
```

**Keyframe fallback** (when the CLI rejects video):
```bash
ffmpeg -i clip.mp4 -vf "fps=1" /tmp/frames_%04d.jpg
cd /tmp && gv -p "Describe what is happening in each frame: @frames_0001.jpg, @frames_0002.jpg, ..."
```

## PDF

**Summarize**
```
Summarize @<doc.pdf> in <N> sentences.
```

**Extract specific section**
```
From @<doc.pdf>, extract the section titled "<title>". Return verbatim.
```

**Key terms**
```
List the key terms defined in @<doc.pdf> with one-line definitions.
```

**Q&A over content**
```
@<doc.pdf>
Question: <the question>
Answer with a citation (page number or section heading).
```

**Compare versions**
```
Compare @<v1.pdf> and @<v2.pdf>. What changed?
```

## Multi-file

**Bulk process** — use `gv-batch`:
```bash
gv-batch <dir> "<prompt that references @BASENAME or @<filename>>"
gv-batch ~/screenshots/ "describe @BASENAME in one sentence"
```

**Compare across many**
```bash
cd ~/product-shots
gv -p "Group these images by visual similarity. @shot1.jpg, @shot2.jpg, @shot3.jpg, ..."
```

## Structured output

Two layers — don't confuse them:

- **Envelope** (`gv --json`): wraps *any* call in `{ok, response, error_class, exit_code, ...}`. Use it to branch on success/failure programmatically. `.response` is the model's text.
- **Model-shaped JSON** (prompt asks for JSON): structures the *answer* itself. With `--json` too, that JSON lands inside `.response` as a string.

**JSON shape** (caller's choice — no domain vocab):
```bash
gv -p "Describe @<file>. Return JSON: {description: string, objects: string[], colors: string[]}"

# Envelope + model JSON, then pull the answer out:
gv --json -p "Describe @<file>. Return JSON: {description, objects: []}" | jq -r '.response'
```

**Grading scale** (caller defines what the scale means):
```bash
gv -p "Rate @<file> on a 1-10 scale for <criterion>. Reply with just the number."
```

**Step-by-step reasoning**:
```bash
gv -p "Analyze @<file> step by step. Show your reasoning, then give a final answer."
```

## Rules of thumb

- **Be specific about what to return**: "Reply with just the number" is clearer than "tell me the count".
- **Reference files inline** with `@<filename>`, not as separate args.
- **One task per call** for complex analysis; multi-task prompts dilute focus.
- **Specify format last** ("Return JSON: {...}", "Reply in <N> bullets") — model tends to honor format constraints.
- **Don't pre-fill domain context** — let the caller (user) frame the analysis. Generic "describe" beats domain-specific "tear down this Meta ad" when the skill is generic.
