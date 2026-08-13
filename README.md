# jstack

A personal agent-workflow skill suite. jstack is a set of composable [agent skills][skills]
for Claude Code, Codex, and Hermes that shape how an agent talks, hands off sessions, captures
knowledge, drafts messages, and analyzes media. It started as one person's setup; this repo is
the genericized, shareable version.

[skills]: https://docs.claude.com/en/docs/claude-code/skills

> **Heads up:** this is an opinionated personal stack, not a polished product. Some skills work
> out of the box; others (`brainwork`, `savetobrain*`, `vision`,
> `adscan`) need extra setup or a separate repo. Configure to taste.

## Quick start

```bash
git clone <your-fork-url> ~/jstack
cd ~/jstack
bash skills/suite/scripts/setup.sh
```

The `jstack` skill's setup routine copies the skills into your harness skill dir (auto-detects
`~/.claude/skills`, `~/.agents/skills`, or `~/.hermes/skills`), writes `~/.jstack/config.env`, and
probes optional tooling. Then reload your agent so it sees the suite skills.

Prefer symlinks (so edits track the repo)? `bash skills/suite/scripts/setup.sh --link`.

Manual install: copy each `skills/<name>/` directory into your harness skill directory yourself,
then `cp .env.example ~/.jstack/config.env` and edit it.

## Skill catalog

| Skill | What it does | Extra setup |
|-------|--------------|-------------|
| `jstack` | Suite front door: packaging convention + scaffolder (`/jstack`), and setup/install that writes config (`skills/suite/scripts/setup.sh`). | — |
| `premortem` | Assumes a plan already failed and works backward to expose failure modes. | — |
| `jstack-voice` | Warm, direct, concise communication voice. Toggle on/off. | — |
| `focus` | Compresses the previous response (~40%). | — |
| `handoff` | Compacts a session into a handoff doc for a fresh agent. | — |
| `handoff-from-cc` | Builds a handoff from a Claude Code session by ID. | Claude Code |
| `to-spec` | Creates an outcome-led execution spec from settled context. | — |
| `jstack-challenge` | Spawns a cold-briefed advisor subagent to pressure-test your position. | — |
| `cc-find` | Natural-language BM25 search over past Claude Code sessions. | Claude Code, Python 3 |
| `myvoice` | Drafts outbound in your voice (mode × channel) and keeps the voice canon current. | set `JSTACK_PERSONA_NAME` |
| `git-guardrails` | Installs a PreToolUse hook that mechanically blocks destructive git commands (force push, reset --hard, clean -f, branch -D, checkout .) before they execute. | one-time setup |
| `vision` | Multimodal analysis (image/audio/video/PDF) via Gemini on Vertex AI. | GCP project + `gemini` CLI |
| `brainwork` | Processes/ingests/lints a second-brain (llm-wiki) vault. | a second-brain vault |
| `savetobrain` | Captures conversation, YouTube, X/Twitter, or GitHub repository sources as raw vault material. | a second-brain vault; `gh auth login` for GitHub repositories |
| `savetobrain-from-cc` | Saves a Claude session transcript into the vault. | a second-brain vault |
| `adscan` | Pulls Meta Ad Library creative for advertisers. | separate `adscan` repo, `ffmpeg` |
| `show-me` | Explains the current topic with the smallest useful visual. | — |
| `asciiexplain` | Explains a topic with a terminal-safe ASCII diagram. | — |

## Configuration

All config lives in `~/.jstack/config.env`. Every value resolves as
**environment variable → `~/.jstack/config.env` → built-in default**, so you can override any key
per-call with an env var. See [`.env.example`](.env.example) for the full list. Key ones:

| Key | Used by | Default |
|-----|---------|---------|
| `JSTACK_PERSONA_NAME` | myvoice, voice | `the user` |
| `SECOND_BRAIN_PATH` | brainwork, savetobrain* | `~/second-brain` |
| `GOOGLE_CLOUD_PROJECT` | vision | *(required for vision)* |
| `CLAUDE_PROJECTS_DIR` | claude-find, *-from-claude | `~/.claude/projects` |
| `ADSCAN_DIR` | adscan | `~/builds/adscan` |

## Prerequisites by skill

- **vision** — a Google Cloud project with Vertex AI enabled, the `gemini` CLI
  (`brew install gemini-cli`), and cached OAuth. Set `GOOGLE_CLOUD_PROJECT`, then add the bundled
  wrapper to PATH: `export PATH="$HOME/jstack/vendor/gemini-vision:$PATH"`. See
  [`vendor/gemini-vision/README.md`](vendor/gemini-vision/README.md).
- **brainwork / savetobrain*** — a second-brain vault built on the `llm-wiki` skill
  (an Obsidian-style markdown wiki with `tools/sb.py`). Point `SECOND_BRAIN_PATH` at it. Without a
  vault these skills have nothing to operate on.
- **adscan** — a separate `adscan` CLI repo (built on `meta-ads-collector`). Install it and
  set `ADSCAN_DIR`. Needs `ffmpeg` for video poster frames.
- **Codex advisor (jstack-challenge)** — optional. Install `@openai/codex` and `codex login` to let
  the advisor run as a background Codex agent; otherwise it uses a Claude subagent.

## Layout

```
jstack/
  README.md
  .env.example          # all config keys
  skills/               # the suite skills (copy/symlink into your harness)
  vendor/gemini-vision/ # the `gv` Gemini wrapper used by vision
  tools/secrets-gate.sh # pre-push scan for identity/keys (run before every push)
```

## Authoring & contributing

- Scaffold a new skill with `skills/suite/scripts/new-jstack-skill.sh <skill-name>`. It creates the
  canonical dir under `skills/` and symlinks it into every harness installed on your machine.
- **Before every `git push`, run `bash tools/secrets-gate.sh`.** It scans tracked and new files for
  personal identity, machine paths, GCP project ids, and credential patterns, and fails on a hit.
  Keep personal values in `~/.jstack/config.env` (gitignored), never in a committed skill.

## Notes

- No API keys are committed. `vision` reads `GOOGLE_CLOUD_PROJECT` from your config; nothing
  else needs a key. Keep `~/.jstack/config.env` out of version control (it's gitignored here).
- Skills follow the [agent skills][skills] format (a `SKILL.md` with YAML frontmatter), so they work
  in any harness that loads skills.
