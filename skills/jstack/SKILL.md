---
name: jstack
description: Owns the packaging convention for the jstack skill family. Use when creating, authoring, scaffolding, or packaging a new jstack skill ("make a jstack skill", "new jstack skill", "add a jstack skill").
---

# Authoring jstack skills

## Naming convention (decided 2026-06-12)

- `jstack-<skill>` — daily productivity, venture-agnostic (`jstack-savetobrain`,
  `jstack-vision`, `jstack-handoff`).
- `jstack-<venture-code>-<skill>` — venture-specific (`jstack-sf-new`; `sf` =
  StayFrame). Venture skills sort together in every picker and stay under the jstack
  umbrella. NEVER use a colon in a skill directory name — `name:thing` is the harness's
  plugin namespace (`superpowers:brainstorming`) and a colon in a plain skill name breaks
  resolution and Discord's `/skill` picker.

All jstack skills are **canonical in the jstack repo** (`skills/<name>/`, wherever
you cloned jstack) and symlinked into every harness. **Every link points directly
at the repo dir — no transitive hop through `.agents`:** `~/.agents/skills/<name>`
(the discovery hub), `~/.claude/skills/<name>`, and `~/.codex/skills/<name>` each
resolve straight to `<clone>/skills/<name>`. Hermes entries live inside the package
dir `~/.hermes/skills/jstack/<name>`, also pointing straight at the repo. There is
no second forked copy — edit the file in the repo and every harness sees it through
its own direct symlink.

Discord `/skill` discovery does not depend on this layout: it is handled by adding
`~/jstack/skills` to Hermes `external_dirs` (see the Discord section below), which
scans the canonical repo directly.

When asked to create a new jstack skill, do not hand-create directories or symlinks. Run:

```bash
<your-clone>/skills/jstack/scripts/new-jstack-skill.sh <skill-name> --desc "one-line description"
```

It creates the canonical dir + a starter `SKILL.md` in the repo's `skills/`, then
symlinks it (direct to the repo) into `.agents`, `.claude`, `.codex`, and the
`.hermes/skills/jstack/` package — skipping any harness not installed. The script
resolves the repo from its own location, so it works wherever you cloned jstack. It
is idempotent: re-running it on an existing skill repairs or retargets symlinks
without touching the canonical `SKILL.md`.
After running it, edit the canonical `SKILL.md` in the repo to fill in the body.

## Next skills table (required on every skill)

Every jstack skill ENDS with a `## Next skills` table — the recommended skill(s) to invoke
after this one, so an agent (or Jono) always knows the next hop in a workflow. Two columns:
the skill (an invocable `/jstack-…` or, for craft, `video-prod-skills:…`) and **when** to go
there. List only real next hops, not a catalog. A standalone skill with no natural successor
still includes the table — name companion/related skills or state "standalone — no required
next step." The scaffolder seeds an empty version; fill it when you write the body.

> **Video generation is always routed through `/jstack-vidgen`** — any skill whose workflow
> reaches "generate a video / clip" points its Next-skills row at `/jstack-vidgen` (the
> universal router that enforces ask-duration+resolution, show-the-exact-prompt-and-craft-skill,
> and no dup-frame), never directly at a backend.

## Before pushing

The repo is shareable. Before any `git push`, run `tools/secrets-gate.sh` from the
repo root — it scans for personal identity, machine paths, GCP project ids, and key
patterns, and exits non-zero on a hit. Keep personal values in `~/.jstack/config.env`
(gitignored), never in a committed skill. Skills read config at runtime via
**env var → `~/.jstack/config.env` → default**.

## Discord `/skill` autocomplete and symlinks

Hermes' Discord gateway resolves skill symlinks to their real paths with
`Path.resolve()` and drops any skill whose resolved path falls outside a configured
scan root. Since jstack skills are canonical in `~/jstack/skills/` and only symlinked
into harness directories, the resolved path lands outside both `~/.hermes/skills/` and
`~/.agents/skills/`, causing the skill to be silently absent from Discord's `/skill`
picker.

The fix is to add `~/jstack/skills` as an external skills directory in Hermes config:

```yaml
skills:
  external_dirs:
    - ~/.agents/skills
    - ~/jstack/skills
```

After updating config, restart the gateway or run `/restart` on Discord. Without this,
`hermes skills list` and `skill_view` will see the skills but `/skill` on Discord won't.

## Adapting external skills

When adapting a skill from an external source (gstack, skills.sh, another agent's repo), do not copy it verbatim. External skills are often deeply coupled to their host infrastructure. The gstack `skillify` skill, for example, is 1,200 lines where 60% is gstack-specific preamble, onboarding state machines, telemetry, the `$B` browser harness, `browse-client.ts` SDK, and atomic write helpers. None of that ports.

The right approach: read the full source, extract the core workflow (steps that describe the actual transformation, not the host plumbing), map every host-specific tool reference to its Hermes equivalent, and drop anything that assumes a different agent runtime. Scaffold with `new-jstack-skill.sh` and write the SKILL.md body from the extracted workflow, not from the source file.

## Next skills

| Next | When |
|------|------|
| `skill-creator` | A skill has been scaffolded — use skill-creator to author/restructure its SKILL.md body against the AgentSkills spec. |
| `/jstack-vidgen` | The skill being authored has a workflow that reaches "generate a video/clip" — route that step through the video router. |

Otherwise standalone — this is the authoring convention reference; no required next step.
