---
name: suite
description: Owns the jstack skill family — packaging convention AND suite setup. Use when creating, authoring, scaffolding, or packaging a jstack skill ("make a jstack skill", "new jstack skill", "add a jstack skill"), and when installing or configuring the suite ("set up jstack", "install jstack", "configure jstack", "/jstack-setup", or just cloned the repo and want it wired into Claude Code, Codex, or Hermes).
user_invocable: true
---

# suite — author, package, and set up the skill family

This skill owns three jobs for the jstack suite. Pick the one that matches the request and load only
its reference:

| Job | When | Reference |
|-----|------|-----------|
| **Set up / install** | "set up jstack", "install jstack", "configure jstack", "/jstack-setup", or the repo was just cloned and needs wiring into a harness | `references/setup.md` |
| **Author / package** | "make a jstack skill", "new jstack skill", "scaffold a skill", naming/frontmatter/plugin-convention questions | `references/packaging.md` |
| **Package the plugin** | "package the plugin", "repackage jstack", "Agent Plugins package", "rebuild the .plugin", "package for Cowork", or a skill changed | The repo root (`plugin.json` + `skills/`) is the portable Agent Plugins package. Run `scripts/build-plugin.sh` only to regenerate the Claude/Cowork compatibility bundle. |

Do not load more than one reference at once — route first, then read the one you need.

## Build the `.plugin` (quick start)

Deterministic. One command regenerates the Cowork bundle — it auto-discovers every skill, so new or
updated skills are picked up with no edits to the build:

```bash
bash skills/suite/scripts/build-plugin.sh --bump patch
```

The portable manifest is at `plugin.json`; it discovers every `skills/<name>/` that has a
`SKILL.md` (skipping husk dirs), validates each skill's frontmatter against the Cowork `.plugin` rules
(fails fast on any violation), checks that the Claude companion manifest has the same name and version,
scrubs non-shippable junk (`.git`, `.venv`, `node_modules`,
`__pycache__`, `*.pyc/.orig/.bak/.DS_Store`, dangling symlinks), and zips with stable file ordering to
`dist/<plugin-name>.plugin`. Flags: `--bump patch|minor|major` or `--version X.Y.Z` (bump so Cowork
treats the reinstall as an update), `--out PATH`, `--print-only` (discover + validate, write nothing).
In a Cowork session, pass `--out` pointing at the outputs dir, then present the file.

## Set up / install (quick start)

From the cloned repo:

```bash
bash skills/suite/scripts/setup.sh
```

It copies (or `--link` symlinks) the suite skills into the harness skill dir, writes
`~/.jstack/config.env`, probes optional tooling, and prints next steps. It is idempotent — safe to
re-run. Full flags, config keys, "what it does NOT do", and the Discord symlink pitfall live in
`references/setup.md`. When you (the agent) run it, it goes non-interactive and writes default config;
afterward, offer to fill in the real values.

## Author / package (quick start)

First classify the requested family:

- **Suite-global / venture-agnostic:** use the global scaffolder below. It is canonical in this repo
  and intentionally links the skill into installed harnesses.
- **New venture or project family:** default to **repo-local only**. Read the target repo's `AGENTS.md`,
  then follow the `Repo-local family` procedure in `references/packaging.md`. Do not run the global
  scaffolder, add it to this repo, package it in the jstack `.plugin`, or create links under
  `~/.agents`, `~/.claude`, `~/.codex`, or `~/.hermes` unless the user explicitly asks to promote
  that family globally.

For a suite-global skill only, never hand-create its directories or symlinks. Scaffold with:

```bash
skills/suite/scripts/new-jstack-skill.sh <skill-name> --desc "one-line description"
```

Then fill in the canonical `SKILL.md` body in the repo. The naming convention, the Agent Plugins
package contract, the Cowork `.plugin`
frontmatter rules, the required `## Next skills` table, the pre-push secrets gate, the Discord
`external_dirs` fix, and how to adapt external skills are all in `references/packaging.md`.

## Next skills

| Next | When |
|------|------|
| `skill-creator` | A skill has been scaffolded — use skill-creator to author/restructure its SKILL.md body against the AgentSkills spec. |
| `/vidgen` | The skill being authored has a workflow that reaches "generate a video/clip" — route that step through the video router. |

Otherwise standalone — this is the suite's authoring + setup reference; no required next step.
