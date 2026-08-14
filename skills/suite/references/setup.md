# Setting up jstack — install and configure

One-shot installer. Copies the suite skills into the user's harness skill directory,
writes `~/.jstack/config.env`, probes optional tooling (codex, gemini, ffmpeg), and prints
next steps. Safe to re-run.

## Run it

From the cloned repo, run the bundled script:

```bash
bash skills/suite/scripts/setup.sh
```

Useful flags:
- `--skills-dir DIR` — install target (default: auto-detect `~/.codex/skills`, `~/.claude/skills`, `~/.agents/skills`, or `~/.hermes/skills`).
- `--link` — symlink skills instead of copying (so edits track the repo).
- `--non-interactive` — never prompt; write config from defaults (this is automatic when run by an agent, since there's no TTY).
- `--print-only` — report what it would do, change nothing.

When you (the agent) run this, it runs non-interactively and writes a **default** config. After it
finishes, offer to fill in the real values: ask the user for their persona name, second-brain vault
path, and GCP project (only if they want `vision`), then write them into `~/.jstack/config.env`.

## What it configures

`~/.jstack/config.env` is the single source of config. Scripts and skills resolve values as
**env var → `~/.jstack/config.env` → safe default**. Keys:

| Key | Used by | Default |
|-----|---------|---------|
| `JSTACK_PERSONA_NAME` | jstack-msgdraft, voice | `the user` |
| `SECOND_BRAIN_PATH` | brainwork, savetobrain* | `~/second-brain` |
| `GOOGLE_CLOUD_PROJECT` | vision | *(required for vision)* |
| `GOOGLE_CLOUD_LOCATION` | vision | `us-central1` |
| `GEMINI_VISION_MODEL` | vision | `gemini-2.5-flash` |
| `CLAUDE_PROJECTS_DIR` | cc-find, *-from-claude | `~/.claude/projects` |
| `JSTACK_HANDOFF_DIR` | handoff | `~/.jstack/handoffs` |
| `ADSCAN_DIR` | adscan | `~/builds/adscan` |

## After running

Report to the user: where skills were installed, the config path, the probe results, and the
remaining manual steps the script printed (reload skills, set `GOOGLE_CLOUD_PROJECT`, add the
`vendor/gemini-vision` dir to PATH for vision, second-brain/adscan are separate prerequisites).

## What setup does NOT do

- Does not install the second-brain (llm-wiki) vault or the adscan repo — those are separate.
- Does not log into codex or GCP — it only checks and reports auth status.
- Does not modify the user's shell profile; it prints the PATH line for them to add.

## Pitfalls

### Discord `/skill` autocomplete silently drops symlinked jstack skills

When skills are installed with `--link`, the SKILL.md files are symlinks pointing to
`~/jstack/skills/`. Hermes' Discord gateway resolves symlinks to their real paths and
drops any skill whose resolved path falls outside a configured scan root. After
running `setup.sh --link` into `~/.hermes/skills/`, verify that `~/jstack/skills` is
in `skills.external_dirs` in `~/.hermes/config.yaml`:

```yaml
skills:
  external_dirs:
    - ~/.agents/skills
    - ~/jstack/skills
```

Without this, `hermes skills list` sees the skills but `/skill` on Discord won't.
Restart the gateway (`/restart` on Discord) after adding the config.
