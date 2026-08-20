---
name: chatgpt-brain
description: "Operate a second brain remotely from ChatGPT. Use when ChatGPT needs to search a GitHub-backed second brain, save conversations as raw evidence, compile raw material into canonical wiki knowledge, or maintain generated brain views."
---

# chatgpt-brain

Use this skill as the remote adapter between ChatGPT and a second-brain vault.

## Model

Treat these as separate layers:

- raw/: immutable evidence
- wiki/: canonical knowledge
- generated views: navigation data

## Search

1. Read the generated index when available.
2. Use it to find relevant canonical pages.
3. Open wiki pages before making knowledge claims.
4. Open raw sources when evidence or detail is required.

## Save

1. Create a raw markdown artifact.
2. Preserve source context and provenance.
3. Commit the file to GitHub.
4. Leave canonical pages unchanged until compilation.

## Compile

1. Read pending raw material.
2. Extract facts, concepts, and relationships.
3. Decide canonical updates.
4. Update wiki markdown.
5. Refresh generated views and verify integrity.

## Remote execution

Use GitHub file operations for reading and writing. Use GitHub Actions when shell commands such as sb.py are required.
