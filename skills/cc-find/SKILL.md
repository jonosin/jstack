---
name: cc-find
description: Find a Claude Code session by natural-language description and return the claude --resume command. Use when the user says /cc-find, find a Claude session about X, where is the Claude session where I discussed Y, search my past Claude sessions, locate an old Claude conversation, or wants to resume a Claude session they can't find by id.
user_invocable: true
---

# cc-find

Search Claude Code sessions with a natural-language query and return the matching `claude --resume` command. Lean and deterministic — local BM25 over the session JSONLs, no API key, no LLM call.

## Invoke

```bash
# adjust the path to wherever jstack is installed (e.g. ~/.claude/skills)
python3 ~/.claude/skills/cc-find/scripts/find_claude_session.py "<query>"
```

The script auto-detects the Claude project from CWD. Pass `--claude-dir <path>` to point at a specific Claude project directory, or `--project <slug>` if you've added friendly aliases to the script. Pass `--top N` to control the number of results (default 5). Pass `--json` for machine-readable output.

## What it does

1. Resolves the Claude project directory (`~/.claude/projects/<slug>/`).
2. Parses every `*.jsonl` using the jstack transcript extractor (the `jstack` skill ships it — same noise filter, same text extraction, no duplicated logic).
3. Tokenizes the corpus, scores each session with BM25 (k1=1.5, b=0.75), and applies a 3× boost when query terms appear in the first user turn.
4. Prints the top N sessions with date, turn count, first user turn, score, and the resume command.

## Output shape

```
Query: "product hunt UGC LinkedIn leads"
Project: -home-user-second-brain   Sessions: 17

1. 7089a240-600e-430e-82e7-2af674bf250f
   Date: 2026-06-02   Turns: 38   Score: 9.92
   First turn: Please read ~/.jstack/handoffs/...

   claude --resume 7089a240-600e-430e-82e7-2af674bf250f --dangerously-skip-permissions

2. ...
```

The user copies the `claude --resume` line for whichever match looks right.

## After finding the session

If the user wants to capture the session as a second-brain raw drop, hand off to `/savetobrain-from-cc <session-id>` (or, for staged review, the same skill with `--staging`).

## What this skill does NOT do

- Does not run `claude --resume` itself — just prints the command.
- Does not edit `wiki/`, `wiki/index.md`, `wiki/log.md`, or `wiki/hot.md`.
- Does not call any external API. Pure local search.
- Does not maintain a search index. Re-parses JSONLs on every query. Fine for ~50–200 sessions; slow for thousands.

## Next skills

| Next | When |
|------|------|
| `/savetobrain-from-cc` | You found the session and want it captured as a second-brain raw drop (pass the session ID; `--staging` for review first). |
| `/handoff-from-cc` | You found the session and want a handoff artifact built from its transcript instead. |
