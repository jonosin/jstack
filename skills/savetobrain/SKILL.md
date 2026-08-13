---
name: savetobrain
description: >
  Save durable output. Routes: (1) YouTube URL → deterministic transcript capture;
  (2) X/Twitter URL → deterministic source capture; (3) GitHub repository URL or
  owner/repo → deterministic compact repository guide capture; (4) session content
  → location-aware capture. Use when the user says
  /savetobrain, save to brain, save this to the second brain, capture this,
  remember this in the second brain, or provides a YouTube/X/GitHub link to save in
  the brain.
---

# savetobrain — intent router

This file is a thin router. It matches the user's input to one of four public modes,
then hands off to a self-contained reference file. Do not read beyond the matching
branch.

## Intent router — read this first, then follow exactly one branch

Before any other action, check the user's input and working directory:

1. **YouTube URL detected** (`youtube.com/watch`, `youtu.be/`, `youtube.com/shorts`,
   `youtube.com/live`) → load `references/youtube-route.md` and follow it exactly.
   Do not read the rest of this file.

2. **X/Twitter URL detected** (`x.com/<handle>/status/<id>`,
   `twitter.com/<handle>/status/<id>`) → load `references/x-link-route.md` and
   follow it exactly. Do not read the rest of this file.

3. **GitHub repository URL or slug detected** (`github.com/<owner>/<repo>` or
   `<owner>/<repo>`, including private repositories the current `gh` identity can
   read) → load `references/github-route.md` and follow it exactly. Do not read the
   rest of this file.

4. **Conversation content** (decisions, facts, synthesis — no higher-precedence
   URL) → load `references/raw-drops-route.md` and follow it exactly. It resolves
   a registered nested client workspace, then venture workspace, then build
   workspace. A workspace selection loads `references/venture-route.md`; an
   unowned session uses the second-brain raw route.
   Do not read the rest of this file.

## Branch selection order

The branches are checked in order. The first match wins. A workspace session with a
YouTube URL follows the YouTube branch because the URL is the primary intent signal.
