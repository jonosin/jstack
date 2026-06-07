---
name: jstack-handoff-from-claude
description: Extract a clean transcript from a Claude Code session by session ID, then create a jstack handoff artifact from it. Use when the user provides a Claude session ID and wants a handoff generated from that session.
---

Require an explicit Claude Code session ID. If the user didn't provide one, stop and ask:

> Please run `/status` in Claude Code and send me the session ID.

## Extract

Run:

```bash
# adjust the path to wherever jstack is installed (e.g. ~/.claude/skills)
python3 ~/.claude/skills/jstack/scripts/extract_claude_session.py <session-id>
```

If the current directory isn't the one Claude Code ran in, pass `--project-dir <path>` or `--claude-projects-dir <full-path>`.

After extraction, report the transcript path and turn counts.

## Create Handoff

Now invoke `/jstack-handoff` and tell it:

> Read `~/.jstack/transcripts/<session-id>.clean.md` and create a handoff from it.
