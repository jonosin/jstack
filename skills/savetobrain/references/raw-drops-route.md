# Session route — save conversation output to its owner

Reached when the user invokes `/savetobrain` and no venture or build
workspace owner is selected. Resolve the owner before writing.

## What you are writing into

The second brain (`${SECOND_BRAIN_PATH}` from `~/.jstack/config.env`, default
`~/second-brain`) is an **agent-only system of record**. No human reads it. It has
two layers:

- `raw/` — the ground-truth layer. Immutable, append-only. Only things that
  actually happened: what the user said, what a session actually concluded, what an
  external source actually contains.
- `wiki/` — compiled knowledge. A *different* agent (`/brainwork`) builds it
  later by reading `raw/`. Every future agent that plugs into this brain answers
  from the wiki and escalates to raw for work-grade tasks.

**You are the only agent that will ever see this full session.** When it ends,
everything not written down is gone. Everything you do write becomes permanent
context that every future agent inherits. You are the curator standing between this
conversation and every agent that comes after — under-save and future agents lose
the session's output forever; over-save noise and you bloat the ground-truth layer
every future agent pays tokens to read.

## Curation — read editorial rules first

Load `references/editorial-rules.md`. Apply the mandate and universal hard rules
#1-4. The route-specific rules below override or extend them where noted.

## Route-specific hard rules

5. **Resolve the owner.** Check, in order: registered nested client workspace,
   venture workspace, build workspace, then the unowned second brain. A matching
   workspace must not fall through to a second-brain capture.
6. **Workspace owner.** Load `references/venture-route.md`. Write one workspace
   artifact, regenerate the deterministic index, then validate or repair the
   registered brain link. Do not call a capture finalizer and do not create
   second-brain retrieval state.
7. **Unowned second brain.** Use one flat `raw/YYYY-MM-DD-<slug>.md` target.
   First run `python3 tools/sb.py capture prepare --route session --source
   "conversation:<stable-session-identity>" --target "raw/<file>.md" --json`.
   Use its exact raw-v2 frontmatter, atomically publish the immutable file without
   replacing an existing file, then run `python3 tools/sb.py capture finalize
   --route session --artifact "raw/<file>.md" --json` exactly once. Do not compile.
8. **Useful no-write.** If there is no durable decision, fact, synthesis, or
   source evidence, report the reason and write nothing. If the same immutable
   artifact already exists, report that path and do not make another capture.

## Frontmatter contract

Use only the exact raw-v2 frontmatter from `capture prepare`. Do not add route-local
metadata fields.

Supersession: if the user says this replaces earlier knowledge, identify the verified
raw ID in the exact raw-v2 `supersedes` list. If no exact ID is verified, preserve
the user's replacement statement in the body; do not invent an identifier.

## Downstream contract — who reads your file

- `/brainwork` (fresh agent, no session memory) compiles wiki pages from it.
  Make its job mechanical: decisions findable, current-vs-killed unmistakable,
  reasoning attributed to the session date.
- Future working agents may read the raw directly for drafting/deciding/building.
  Save enough that they don't need the transcript.
- You may annotate: mark a block `<!-- background only — do not compile -->` or flag
  low-confidence items. Brainwork honors annotations.

## Final report

Run `python3 tools/sb.py pending` (read-only), then report:

```
Saved raw source: raw/<file>.md — <one-line description>. Brainwork deferred.
Pending ingest backlog: <N> source(s). Run /brainwork to process.
```

If you saved nothing: `Nothing worth saving from this session: <reason>. No file written.`
