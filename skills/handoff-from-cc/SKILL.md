---
name: handoff-from-cc
description: Use ONLY when the user explicitly provides a Claude Code session ID for a DIFFERENT/PAST session to extract its transcript and turn it into a jstack handoff artifact. Intended to be run from a NON-Claude harness (OpenCode, Codex, Hermes) that needs to pull a Claude session out. Boundary vs /handoff: ending or handing off the CURRENT conversation — even from inside Claude Code, even if a session ID is known — is always /handoff, never this skill. Do NOT invoke this for reading, opening, or continuing an existing handoff file (e.g. "read this handoff and continue" is a normal file read, not this skill). Requires an explicit past-session ID; without one, this skill does not apply — route to /handoff instead.
---

Require an explicit Claude Code session ID. If the user didn't provide one, stop and ask:

> Please run `/status` in Claude Code and send me the session ID.

## Extract

Run:

```bash
# adjust the path to wherever jstack is installed (e.g. ~/.claude/skills)
python3 ~/.claude/skills/suite/scripts/extract_claude_session.py <session-id>
```

The script auto-discovers the session JSONL via three strategies (in order):
1. Explicit `--claude-projects-dir` (direct or subdirectory search)
2. CWD or `--project-dir` hash match
3. Global scan of all `~/.claude/projects/*` directories

In most cases no extra flags are needed. If the session can't be found, pass `--project-dir <path>` (the repo path Claude Code ran in) or `--claude-projects-dir <full-path>` (the root `~/.claude/projects/` or a specific project directory).

After extraction, report the transcript path and turn counts.

## Create Handoff

Now invoke `/handoff` and tell it:

> Read `~/.jstack/transcripts/<session-id>.clean.md` and create a handoff from it.

## Next skills

| Next | When |
|------|------|
| `/handoff` | Immediately after extraction — point it at the cleaned transcript to produce the actual handoff artifact (the required next hop; this skill only extracts). |
| `/cc-find` | You don't have the session ID yet and need to locate it first. |
