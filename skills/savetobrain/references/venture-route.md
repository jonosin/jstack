# Workspace route — save session output into workspace docs/

Reached when `/savetobrain` is invoked inside a venture or build repo with
a `docs/` folder and `docs_index.py` available. The workspace owns the artifact;
the brain sees it through the registered `docs/index.md` symlink. Write no raw
drop.

## Detection — confirm this is the right route

Before proceeding, verify all three conditions:

1. The current working directory contains a `docs/` folder.
2. `docs_index.py` is reachable at
   `~/jstack/skills/init/scripts/docs_index.py`.
3. The `docs/` folder has an existing `index.md` (generated or hand-maintained).

If a selected workspace fails these checks, stop with a workspace-local actionable
failure. Do not fall through to second-brain raw capture.

If conditions hold, determine the workspace kind:

- `--venture <slug>` — for repos under `~/ventures/`
- `--repo <path> --satellite-kind build` — for repos under `~/builds/`

Use `--venture <slug>` when the cwd is inside `~/ventures/<slug>/` or any
subdirectory of it. The slug is the venture directory name.

## Curation — read editorial rules first

Load `references/editorial-rules.md`. Apply the mandate and universal hard rules
#1-4. The route-specific rules below extend them.

## What to save

Knowledge worth saving: strategic decisions, durable facts, conclusions, plans,
relationships, preferences, research findings, evidence from the session. Not worth
saving: code written, bugs fixed, refactors, builds run — the repo and git history
are the record for those.

When the session produced both strategic and execution output, save only the
strategic portion. "Nothing strategic here — the implementation lives in the repo"
is a correct outcome.

## Where to save

Write to `docs/strategy/YYYY-MM-DD-kebab-topic.md`. This is the canonical durable
zone. The filename must match the `YYYY-MM-DD-kebab-topic.md` pattern so
`docs_index.py` indexes it.

## Frontmatter contract

Required keys (matching `docs_index.py` expectations):

```yaml
---
title: "Human title — what this document decides or captures"
summary: "One line — what the doc is about and its verdict or state."
status: proposed
---
```

`status` must be one of: `active`, `accepted`, `proposed`, `draft`,
`superseded`, `deprecated`, `archived`. Use `proposed` for new strategy docs
awaiting review, `active` for in-force decisions.

Optional but useful: `created: YYYY-MM-DD`. If omitted, `docs_index.py` derives it
from the filename date.

Provenance: if the file contains agent-authored synthesis, add
`synthesis_by: "<model/harness>"` as an additional frontmatter key. Quote
load-bearing user statements exactly in the body.

## After writing

1. Regenerate the index:
   ```
   python3 ~/jstack/skills/init/scripts/docs_index.py index --write --venture <slug>
   ```
   (Use `--repo <path> --satellite-kind build --slug <slug>` for build repos.)

2. Verify the registered brain link:
   ```
   python3 ~/jstack/skills/init/scripts/docs_index.py brain-link-lint --venture <slug>
   ```

3. If the link is missing or broken, repair it:
   ```
   python3 ~/jstack/skills/init/scripts/docs_index.py brain-link --write --venture <slug>
   ```

## Final report

Report in this exact format:

```
Saved: docs/strategy/<file>.md — <one-line description>
Index regenerated. Brain link: <GREEN or fixed>.
```

If you saved nothing: `Nothing worth saving from this session: <reason>. No file written.`

## Client folder variant

When the working directory is a registered nested client workspace with its own
`docs/` folder and `index.md`:

- Save directly to `docs/YYYY-MM-DD-kebab-topic.md` (client folders use a flat
  `docs/`, not `docs/strategy/`).
- Regenerate its deterministic `docs/index.md`, then validate and repair its
  registered brain link with the helper for that workspace.

This route ends after the artifact, index, and link are ready. It has no
second-brain registration step and creates no second-brain retrieval state.
