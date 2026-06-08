---
name: jstack
description: Owns the packaging convention for the jstack skill family. Use when creating, authoring, scaffolding, or packaging a new jstack skill ("make a jstack skill", "new jstack skill", "add a jstack skill").
---

# Authoring jstack skills

All jstack skills are **canonical in the jstack repo** (`skills/<name>/`, wherever
you cloned jstack) and symlinked into every harness: `~/.agents/skills/` (the hub),
`~/.claude/skills/`, `~/.codex/skills/`, and the `~/.hermes/skills/jstack/` package.
There is no second forked copy — edit the file in the repo and every harness sees it
through the symlink chain. The hermes copies live *inside* the `jstack/` package
directory, never as flat `jstack-*` entries at the hermes skills root.

When asked to create a new jstack skill, do not hand-create directories or symlinks. Run:

```bash
<your-clone>/skills/jstack/scripts/new-jstack-skill.sh <skill-name> --desc "one-line description"
```

It creates the canonical dir + a starter `SKILL.md` in the repo's `skills/`, then
symlinks it into `.agents`, `.claude`, `.codex`, and the hermes `jstack/` package
(skipping any harness not installed). The script resolves the repo from its own
location, so it works wherever you cloned jstack. It is idempotent: re-running it on
an existing skill repairs missing symlinks without touching the canonical `SKILL.md`.
After running it, edit the canonical `SKILL.md` in the repo to fill in the body.

## Before pushing

The repo is shareable. Before any `git push`, run `tools/secrets-gate.sh` from the
repo root — it scans for personal identity, machine paths, GCP project ids, and key
patterns, and exits non-zero on a hit. Keep personal values in `~/.jstack/config.env`
(gitignored), never in a committed skill. Skills read config at runtime via
**env var → `~/.jstack/config.env` → default**.
