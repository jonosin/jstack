---
name: jstack-savetobrain-from-claude
description: Extract a Claude Code session transcript from the second-brain Claude project as a raw drop, ready for /jstack-brainwork to ingest. Reuses the jstack transcript extractor but writes to raw/personal/drops/ (or raw/personal/scratch/ with --staging). Use when the user says /jstack-savetobrain-from-claude, save this Claude session to the brain, capture the current Claude session, or wants a Claude Code transcript preserved as second-brain raw material.
user_invocable: true
---

# jstack-savetobrain-from-claude

Extract a Claude Code session as a raw drop. Lean wrapper over the jstack transcript extractor: same JSONL parser, same noise filter, same markdown renderer — different project mapping and different output convention.

## Required input

Require an explicit Claude Code session ID. If the user did not provide one, stop and ask:

> Please run `/status` in Claude Code and send me the session ID to save.

Do not guess. Do not pick the latest session by default.

## Extraction

The script auto-detects incremental vs full via a per-session `.state.json` in the staging dir.

```bash
# adjust the path to wherever jstack is installed (e.g. ~/.claude/skills)
python3 ~/.claude/skills/jstack-savetobrain-from-claude/scripts/extract_jstack_transcript.py <session-id>
```

- **First run (no state)**: full extraction.
- **Re-run**: incremental — only new JSONL lines since last run.

Re-extraction is idempotent: running again on a session that has not grown prints `No new entries found. Session unchanged.` and exits 0.

## Output

Default: the rendered transcript is written as a raw drop under

```
raw/personal/drops/YYYY-MM-DD-claude-session-<short-id>-<session-date>.md
```

The file is frontmattered per `skills/llm-wiki/references/raw-template.md` with `source: claude-code://session/<id>`, so `/jstack-brainwork` can ingest it as a Standard (or Personal) source.

Use `--staging` to write under `raw/personal/scratch/claude-transcripts/` instead — for when the user wants to inspect the transcript before promoting it to a drop.

Use `--full` to force a complete re-extraction (overwrites state).
Use `--since <iso>` to extract only entries after a timestamp.
Use `--out <path>` to override the output path entirely.

## Report

Keep it one line. The script already prints included/skipped counts; just say where it landed and what to do next:

```
Saved raw source: raw/personal/drops/2026-06-04-claude-session-0abed117.md. Brainwork deferred; run /jstack-brainwork when you want it processed.
```

If the user passed `--staging`, say the transcript is staged and ask whether to promote it to a drop.

## Handoff

Do not invoke `/jstack-brainwork` automatically. The growth-loop convention is to defer ingest. The user runs `/jstack-brainwork` when they want the drop processed.

## What this skill does NOT do

- Does not edit `wiki/`, `wiki/index.md`, `wiki/log.md`, or `wiki/hot.md`.
- Does not run `tools/sb.py` (index, log, check, graph, or lint).
- Does not generate wiki prose, summaries, or strategic analysis.
- Does not auto-ingest the drop. Capture and brainwork stay decoupled.

## Next skills

| Next | When |
|------|------|
| `/jstack-brainwork` | After extracting the Claude session as a drop — process/ingest it (deferred by design; run when you want it compiled). |
| `/jstack-claude-find` | If you still need to locate the session ID to extract. |
