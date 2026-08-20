# jstack

A personal agent-workflow skill suite. jstack is a set of composable agent skills for Claude Code, Codex, Hermes, and remote ChatGPT workflows.

## Quick start

Install skills using the existing suite setup flow.

## Skill catalog

| Skill | What it does | Extra setup |
|-------|--------------|-------------|
| `brainwork` | Processes, ingests, and validates a second-brain vault. | second-brain vault |
| `savetobrain` | Captures sources as raw vault material. | second-brain vault |
| `chatgpt-brain` | Operates a GitHub-backed second brain remotely from ChatGPT. It provides search, save, compile, and maintenance workflows. | GitHub access to the vault |

## Brain workflows

Brain skills use a second-brain vault containing markdown knowledge pages and tools such as `sb.py`.

`chatgpt-brain` is the remote adapter. ChatGPT can read and write vault files through GitHub. Operations requiring shell execution can use GitHub Actions.
